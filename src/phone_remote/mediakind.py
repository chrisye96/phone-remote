"""Works out what kind of thing is playing, and a readable name for the app playing it.

The system's "now playing" report says which app it came from, plus title, artist and album,
but nothing reliable about whether it is music or video (browsers call everything music).
So the kind is guessed: known apps first, then what the metadata looks like.
"""

# Lowercase pieces of an app id -> (kind, display name). The first match wins.
KNOWN_APPS = [
    ("spotify", "music", "Spotify"),
    ("zunemusic", "music", "Media Player"),
    ("applemusic", "music", "Apple Music"),
    ("itunes", "music", "iTunes"),
    ("foobar2000", "music", "foobar2000"),
    ("cloudmusic", "music", "NetEase Music"),
    ("qqmusic", "music", "QQ Music"),
    ("kugou", "music", "Kugou"),
    ("kuwo", "music", "Kuwo"),
    ("musicbee", "music", "MusicBee"),
    ("aimp", "music", "AIMP"),
    ("tidal", "music", "TIDAL"),
    ("vlc", "video", "VLC"),
    ("potplayer", "video", "PotPlayer"),
    ("mpc-hc", "video", "MPC-HC"),
    ("mpc-be", "video", "MPC-BE"),
    ("mpv", "video", "mpv"),
    ("zunevideo", "video", "Movies & TV"),
    ("netflix", "video", "Netflix"),
    ("disney", "video", "Disney+"),
    ("bilibili", "video", "Bilibili"),
    ("iqiyi", "video", "iQIYI"),
    ("qqlive", "video", "Tencent Video"),
]
BROWSERS = [("msedge", "Edge"), ("chrome", "Chrome"), ("firefox", "Firefox"), ("opera", "Opera"),
            ("brave", "Brave"), ("vivaldi", "Vivaldi"), ("thebrowsercompany", "Arc")]  # not "arc": too many names contain it


def _readable(app_id):
    # "SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify" -> "Spotify", "C:\\x\\foo.exe" -> "foo"
    name = app_id.rsplit("!", 1)[-1].replace("/", "\\").rsplit("\\", 1)[-1]
    return name[:-4] if name.lower().endswith(".exe") else name


def classify(app_id, artist="", album=""):
    """Returns (kind, app name); kind is "music", "video" or "" when there is no good guess."""
    lowered = (app_id or "").lower()
    for piece, kind, name in KNOWN_APPS:
        if piece in lowered:
            return kind, name
    for piece, name in BROWSERS:
        if piece in lowered:
            # ponytail: in a browser an album only comes with music sites (Spotify, YouTube Music);
            # anything else there is mostly video. Podcasts land on the wrong side.
            return ("music" if album else "video"), name
    return ("music" if artist or album else ""), _readable(app_id or "")
