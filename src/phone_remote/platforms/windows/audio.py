"""Windows：读系统音量。直接调用系统音频接口（Core Audio），不依赖第三方库。"""
import ctypes
from ctypes import POINTER, byref, c_float, c_int, c_long, c_ulong, c_void_p

ole32 = ctypes.windll.ole32
CLSCTX_ALL = 23


class GUID(ctypes.Structure):
    _fields_ = [("d1", c_ulong), ("d2", ctypes.c_ushort), ("d3", ctypes.c_ushort),
                ("d4", ctypes.c_ubyte * 8)]


def _guid(text):
    value = GUID()
    ole32.CLSIDFromString(ctypes.c_wchar_p(text), byref(value))
    return value


CLSID_DEVICE_ENUMERATOR = _guid("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
IID_DEVICE_ENUMERATOR = _guid("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
IID_ENDPOINT_VOLUME = _guid("{5CDF2C82-841E-4546-9722-0CF74078229A}")
ole32.CoCreateInstance.argtypes = [POINTER(GUID), c_void_p, c_ulong, POINTER(GUID), POINTER(c_void_p)]

# 各接口里用到的方法在虚函数表中的位置
RELEASE = 2
GET_DEFAULT_ENDPOINT = 4   # IMMDeviceEnumerator
ACTIVATE = 3               # IMMDevice
GET_VOLUME_SCALAR = 9      # IAudioEndpointVolume
GET_MUTE = 15


def _method(obj, index, *argtypes):
    vtable = ctypes.cast(obj, POINTER(POINTER(c_void_p)))[0]
    return ctypes.WINFUNCTYPE(c_long, c_void_p, *argtypes)(vtable[index])


def _release(obj):
    if obj:
        _method(obj, RELEASE)(obj)


def init_thread():
    """每个要读音量的线程先调一次。"""
    ole32.CoInitializeEx(None, 0)


def read_volume():
    """返回 (音量 0-100, 是否静音)；读不到（比如没有输出设备）时返回 None。"""
    enumerator, device, volume = c_void_p(), c_void_p(), c_void_p()
    try:
        if ole32.CoCreateInstance(byref(CLSID_DEVICE_ENUMERATOR), None, CLSCTX_ALL,
                                  byref(IID_DEVICE_ENUMERATOR), byref(enumerator)) < 0:
            return None
        # 每次都重新取默认设备，这样切换耳机和扬声器后读到的是新设备
        if _method(enumerator, GET_DEFAULT_ENDPOINT, c_int, c_int, POINTER(c_void_p))(
                enumerator, 0, 1, byref(device)) < 0:
            return None
        if _method(device, ACTIVATE, POINTER(GUID), c_ulong, c_void_p, POINTER(c_void_p))(
                device, byref(IID_ENDPOINT_VOLUME), CLSCTX_ALL, None, byref(volume)) < 0:
            return None
        level, muted = c_float(), c_int()
        if _method(volume, GET_VOLUME_SCALAR, POINTER(c_float))(volume, byref(level)) < 0:
            return None
        if _method(volume, GET_MUTE, POINTER(c_int))(volume, byref(muted)) < 0:
            return None
        return round(level.value * 100), bool(muted.value)
    finally:
        for obj in (volume, device, enumerator):
            _release(obj)
