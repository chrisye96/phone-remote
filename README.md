<img src="docs/logo.svg" width="96" alt="Phone Remote logo">

# Phone Remote

**English** | [中文](README.zh-CN.md)

Run a small program on your computer, open a web page on your phone, and control what is playing on the computer: volume, play and pause, seeking, a touchpad, scrolling, text input, and the usual shortcuts for Bilibili, YouTube, browsers and AI chat apps.

Works on Windows and macOS, written in Python. The phone and the computer need to be on the same Wi-Fi. Nothing is installed on the phone.

## Running it

Windows: double-click `start-windows.bat`. The first run creates a `.venv` virtual environment in the repository and installs the dependencies, which needs an internet connection and takes about a minute.

macOS (install once, after that only the last line is needed):

```bash
python3 -m venv .venv
```

```bash
.venv/bin/python -m pip install -e .
```

```bash
.venv/bin/python -m phone_remote
```

The first time on a Mac, allow "Terminal" under System Settings > Privacy & Security > Accessibility.

There is no window. The program runs in the system tray at the bottom right of the taskbar (the menu bar on a Mac) and opens a page with a QR code. Scan it with your phone's camera.

Right-click the tray icon to show the QR code again, turn starting at login on or off (off by default), re-pair, change the language, or quit. If something goes wrong, look at the log in `%APPDATA%\PhoneRemote\phone-remote.log`.

To run it in a terminal window instead, which makes its output visible: `.venv\Scripts\python -m phone_remote --console`.

### Language

The interface is English by default and can be switched to Chinese. There are two separate settings:

- **The remote on the phone**: tap `EN | 中` in the top right corner. Each phone remembers its own choice.
- **The tray menu and QR page on the computer**: Language in the tray menu. In terminal mode, set `language` to `zh` in the configuration file.

## Building a standalone program

Double-click `scripts\build-windows.bat`. It produces `PhoneRemote.exe` (about 20 MB) in `dist\`. Copy it to another Windows computer and double-click it; Python is not needed there.

## The four screens

![The four screens](docs/screens.png)

(The screenshot shows an older version with Chinese labels.)

- **Play**: what is playing (an icon for music or video, the title and artist, and the app playing it), a draggable progress bar, touchpad, Fullscreen / Exit / OK, and four sets of keys for general use, Bilibili, YouTube and music.
- **Browse**: touchpad, browser back and forward, reload, zoom, tab switching, and shortcuts to your usual sites.
- **Type**: type or dictate on the phone and send the text to whatever input has focus on the computer, plus Enter, Backspace, Select all, Undo, dictation on the computer and so on. "New AI chat" sends Ctrl/Cmd+Shift+O, which starts a new conversation in the ChatGPT and Claude apps and sites.
- **Windows**: lists the windows open on the computer; tap one to bring it to the front. Maximize and minimize are here too. "To other screen" (Windows only) moves the current window to the next monitor, for example sending a video to a TV that is plugged in as a second screen. On a Mac the list shows apps.

A playback bar stays at the bottom of every screen: volume down and up, rewind, play or pause, fast forward, mute.

Key colours show what a key does: blue for playback and the main action, cyan for volume, green for confirming, yellow for navigation, red for exit, close and delete. The play / pause key is the cyan of the logo, since it is the key you press most.

### Site shortcuts

The Sites row on the Browse screen holds up to 4 shortcuts; tapping one opens the site in the computer's browser. Tap "+ Add" and enter an address (`bilibili.com` is enough). Leave the name empty to use the page's own title; the dot takes its colour from the site's theme colour or icon. Hold a shortcut to edit or delete it. They are stored under `shortcuts` in the configuration file.

### Tablets

On a wide screen such as an iPad, the touchpad takes the whole left side and the keys sit in a column on the right, in both orientations. Phones keep the single-column layout.

### Controlling more than one computer

Run the program on each computer. Scan one computer's QR code to open the remote, then tap the computer's name at the top:

- **Add computer…**: paste the address from the other computer's QR page (scan its QR code with the camera, hold the link it finds and choose Copy Link). You can give it a name at the same time.
- Tap a name to switch to that computer.
- **Rename…** and **Remove** apply to the current one.

The name defaults to the computer's own host name. The list is kept in the phone's browser, so another phone has to add the computers again. Every computer needs a version of the program that has this feature.

## Security

- **The pairing code never crosses the network.** It exists only in the QR code and on the phone. Each command carries a signature computed from the code, plus the time. Someone capturing traffic cannot learn the code, and replaying a captured command does nothing.
- **Wrong guesses get locked out.** After 10 bad signatures from one address, that address is ignored for 5 minutes.
- **Re-pair.** Choose Re-pair in the tray menu (`--reset-pairing` in terminal mode) to switch to a new pairing code at once. Every phone paired before stops working and has to scan again. Do this if you lose a phone or someone else has seen the QR code.
- **Commands are not encrypted.** Someone capturing traffic on the same network can see which keys you press and what you type. That is fine at home or on your own phone hotspot. On office, dorm or cafe Wi-Fi, do not type passwords on the Type screen.

When the computer moves to another network, such as a phone hotspot, its address changes. Right-click the tray icon, choose Show QR code and scan again. If Windows treats the network as "Public", the firewall may block the phone; allow the program when prompted, or set the network to "Private".

## Feature switches

Every feature can be turned off on its own. The first run creates a configuration file (its location is printed on start; on Windows it is `%APPDATA%\PhoneRemote\config.json`). Set the entry under `features` to `false` and restart. The computer then refuses the matching commands and the phone no longer shows that part.

| Switch | Feature |
|---|---|
| `touchpad` | Touchpad: move the pointer, click, scroll |
| `text_input` | Text input |
| `windows` | Window list and switching |
| `play_state` | Shows whether something is playing or paused, and its title |
| `progress` | Progress bar, dragging to seek, ±30 seconds |
| `volume_display` | Shows the volume level |
| `sleep_timer` | Sleep timer |
| `open_sites` | Site shortcuts |
| `site_keys` | Keys specific to Bilibili and YouTube |
| `browser_keys` | Browser keys |

Volume, play and pause, seeking and the basic keys are the core and cannot be turned off.

## Code layout

```
src/phone_remote/
  __main__.py      entry point
  config.py        port, pairing code, feature switches
  server.py        HTTP server: page files, checking signatures
  actions.py       validating and dispatching commands
  keys.py          key names, parsing key combinations
  timer.py         sleep timer
  pairing.py       QR page
  siteinfo.py      reads a site's name and colour (used when adding a shortcut)
  tray.py          tray icon and menu
  autostart.py     starting at login
  i18n.py          interface language on the computer (the phone page's is web/js/i18n.js)
  platforms/       one implementation per system; other code only uses the interface in base.py
    base.py
    windows/       input.py  windows.py  media.py  audio.py
    macos/         input.py  windows.py  media.py
  web/             the phone page: index.html, css/, js/ (one module per feature), icons.svg
tests/             automated tests; they never touch the real keyboard or mouse
scripts/           build script, icon sprite and logo scripts
docs/              refactoring plan
```

Run the tests by double-clicking `run-tests.bat`.

## Branches

- `main`: the stable version, ready to use.
- `dev`: day-to-day development. New work branches off `dev` as `feature/*`, merges back into `dev`, and reaches `main` once verified.

## Icons

Icons come from [Tabler Icons](https://tabler.io/icons) (MIT License). Only the few dozen in use are bundled into `src/phone_remote/web/icons.svg`, so nothing is fetched from the internet at run time. To add or remove icons, see `scripts/build-icons.py`.

The logo is drawn in `src/phone_remote/logo.py`: a larger version for 48 px and up, and a simpler one with a single signal arc for 16 and 32 px. `scripts/build-logo.py` writes every file from it: the favicons and home screen icons in `web/`, `docs/logo.svg`, and the Windows icon `scripts/phone-remote.ico`. The tray icon is drawn from the same module when the program starts.
