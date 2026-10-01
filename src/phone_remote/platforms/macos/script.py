"""macOS：运行 AppleScript 的小工具。"""
import subprocess


def osascript(*lines, args=()):
    cmd = ["osascript"]
    for line in lines:
        cmd += ["-e", line]
    result = subprocess.run(cmd + list(args), capture_output=True, text=True, timeout=5)
    return result.stdout.strip()


def osascript_async(line):
    subprocess.Popen(["osascript", "-e", line])
