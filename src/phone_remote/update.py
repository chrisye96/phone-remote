"""Tells the user when a newer release exists. It only reads a version number from GitHub;
nothing is downloaded or run. The user gets the new version from the releases page themselves.
"""
import json
import re
import urllib.request

from . import __version__

LATEST_API = "https://api.github.com/repos/chrisye96/phone-remote/releases/latest"
# Fixed here, not taken from the response, so the network can never decide which page gets opened
RELEASES_PAGE = "https://github.com/chrisye96/phone-remote/releases/latest"
CHECK_EVERY = 24 * 3600


def _fetch():
    request = urllib.request.Request(LATEST_API, headers={"User-Agent": "phone-remote/" + __version__,
                                                          "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def _numbers(version):
    """ "v0.4.1" -> (0, 4, 1); None when it is not plain dotted numbers."""
    match = re.fullmatch(r"v?(\d+(?:\.\d+){0,3})", str(version).strip())
    return tuple(int(part) for part in match.group(1).split(".")) if match else None


def newer_version(current=__version__, fetch=_fetch):
    """The latest release's version, like "0.5.0", when it is newer than the running one; otherwise None.

    Never raises: no network, a rate limit or an unexpected answer all just mean "nothing to report".
    """
    try:
        latest = _numbers(fetch()["tag_name"])
    except Exception:  # anything at all going wrong here must not disturb the program
        return None
    running = _numbers(current)
    if latest and running and latest > running:
        return ".".join(str(n) for n in latest)
    return None
