[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $type) { $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result }
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
  int f(); int g(); int h(); int i();
  int SetMasterVolumeLevelScalar(float level, Guid context);
  int j();
  int GetMasterVolumeLevelScalar(out float level);
  int k(); int l(); int m(); int n();
  int SetMute([MarshalAs(UnmanagedType.Bool)] bool mute, Guid context);
  int GetMute(out bool mute);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate(ref Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume volume); }
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int f(); int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint); }
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorComObject { }
public class Audio {
  static IAudioEndpointVolume Endpoint() {
    var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
    IMMDevice device; Marshal.ThrowExceptionForHR(enumerator.GetDefaultAudioEndpoint(0, 1, out device));
    IAudioEndpointVolume volume; var id = typeof(IAudioEndpointVolume).GUID;
    Marshal.ThrowExceptionForHR(device.Activate(ref id, 23, 0, out volume));
    return volume;
  }
  public static float Volume { get { float v; Marshal.ThrowExceptionForHR(Endpoint().GetMasterVolumeLevelScalar(out v)); return v; } }
  public static bool Muted { get { bool m; Marshal.ThrowExceptionForHR(Endpoint().GetMute(out m)); return m; } }
}
'@
$mgrType = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime]
$propsType = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties, Windows.Media.Control, ContentType=WindowsRuntime]
$mgr = Await ($mgrType::RequestAsync()) $mgrType
# [Console]::In 的异步读其实是同步的，会卡住循环，所以自己包一层
$reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput())
$pending = $reader.ReadLineAsync()
$pick = $null; $last = ''; $tick = 0; $pos = 0; $dur = 0
while ($true) {
  if ($pending.IsCompleted) {
    $cmd = $pending.Result
    if ($null -eq $cmd) { break }
    $pending = $reader.ReadLineAsync()
    try {
      $parts = $cmd -split ' '
      if ($pick -and $dur -gt 0 -and $parts[0] -eq 'seek') {
        $target = [math]::Max(0, [math]::Min($dur - 1, [double]$parts[1]))
        Await ($pick.TryChangePlaybackPositionAsync([long]($target * 10000000))) ([bool]) | Out-Null
      }
    } catch {}
    Start-Sleep -Milliseconds 150
    $tick = 0
  }
  if ($tick % 5 -eq 0) {
    $state = @{ s = 'None'; t = ''; p = 0; d = 0; v = -1; m = $false }
    try { $state.v = [int][math]::Round([Audio]::Volume * 100); $state.m = [Audio]::Muted } catch {}
    try {
      $pick = $mgr.GetCurrentSession()
      foreach ($s in $mgr.GetSessions()) { if ("$($s.GetPlaybackInfo().PlaybackStatus)" -eq 'Playing') { $pick = $s; break } }
      if ($pick) {
        $info = $pick.GetPlaybackInfo()
        $state.s = "$($info.PlaybackStatus)"
        try { $state.t = (Await ($pick.TryGetMediaPropertiesAsync()) $propsType).Title } catch {}
        $line = $pick.GetTimelineProperties()
        $dur = $line.EndTime.TotalSeconds
        $pos = $line.Position.TotalSeconds
        if ($dur -gt 0 -and $state.s -eq 'Playing') {
          $rate = $info.PlaybackRate; if (-not $rate) { $rate = 1 }
          $pos += ([DateTimeOffset]::Now - $line.LastUpdatedTime).TotalSeconds * $rate
        }
        $pos = [math]::Max(0, [math]::Min($dur, $pos))
        $state.p = [math]::Round($pos, 1); $state.d = [math]::Round($dur, 1)
      } else { $dur = 0 }
    } catch {}
    $json = $state | ConvertTo-Json -Compress
    if ($json -ne $last) { [Console]::Out.WriteLine($json); $last = $json }
  }
  $tick++
  Start-Sleep -Milliseconds 100
}
