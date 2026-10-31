"""macOS：运行 AppleScript 的小工具。"""
import subprocess


def _command(lines, args):
    cmd = ["osascript"]
    for line in lines:
        cmd += ["-e", line]
    return cmd + list(args)


def osascript(*lines, args=()):
    result = subprocess.run(_command(lines, args), capture_output=True, text=True, timeout=5)
    return result.stdout.strip()


def osascript_async(*lines, args=()):
    subprocess.Popen(_command(lines, args))


def show_error(title, text):
    # Not osascript(): its timeout would take the alert away after 5 seconds
    osascript_async("on run argv",
                    "display alert (item 1 of argv) message (item 2 of argv) as critical",
                    "end run", args=[title, text])
