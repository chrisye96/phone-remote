<img src="docs/logo.svg" width="96" alt="Phone Remote logo">

# Phone Remote

**English** | [中文](README.zh-CN.md)

Run a small program on your computer, open a web page on your phone, and control what is playing on the computer: volume, play and pause, seeking, a touchpad, scrolling, text input, and the usual shortcuts for Bilibili, YouTube, browsers and AI chat apps.

Works on Windows and macOS, written in Python. The phone and the computer need to be on the same Wi-Fi. Nothing is installed on the phone: an iPhone, an iPad, or an Android phone or tablet all work, in the browser they already have.

## Running it

The easy way is the packaged program on the [releases page](https://github.com/chrisye96/phone-remote/releases/latest), which needs no Python: `PhoneRemote.exe` for Windows, `PhoneRemote-macOS-AppleSilicon.zip` for a Mac with an Apple chip (M1 or later), `PhoneRemote-macOS-Intel.zip` for a Mac with an Intel processor. The release page lists the steps for the first start on a Mac. To run from source instead:

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

The first time on a Mac, allow "Terminal" under System Settings > Privacy & Security > Accessibility (with the packaged app, allow "PhoneRemote" instead). While that is missing, the QR page shows the steps at the top.

There is no window. The program runs in the system tray at the bottom right of the taskbar (the menu bar on a Mac) and opens a page with a QR code. Scan it with your phone's camera. To open the remote like an app next time, add the page to your home screen: Share > Add to Home Screen in Safari, or the menu > Add to Home screen in Chrome on Android.

Right-click the tray icon to show the QR code again, turn starting at login on or off (off by default), re-pair, change the language, or quit. The About item shows the version you are running and opens this project's page; the version is also at the bottom of the QR page, and on the phone in Settings (the gear in the top right corner). If something goes wrong, look at the log in `%APPDATA%\PhoneRemote\phone-remote.log`.

To run it in a terminal window instead, which makes its output visible: `.venv\Scripts\python -m phone_remote --console`.

### Language

The interface comes in English and Chinese. The first time, each side starts in the language of the device it runs on (Chinese where the system is set to Chinese, English everywhere else); after that it keeps what you choose. There are two separate settings:

- **The remote on the phone**: tap the gear in the top right corner and choose under Language. Each phone remembers its own choice.
- **The tray menu and QR page on the computer**: Language in the tray menu. In terminal mode, set `language` to `zh` in the configuration file.

### Updates

Once a day the program asks GitHub for the version number of the latest release. When there is a newer one, the tray menu gains an "Update available" item that opens the [releases page](https://github.com/chrisye96/phone-remote/releases/latest); download the new file there (`PhoneRemote.exe`, or the zip for your Mac) and replace the old one. Nothing is downloaded or installed automatically. If you run from source, `git pull` instead.

That one request is the only time the program contacts the internet on its own. To turn it off, set `check_updates` to `false` in the configuration file.

The remote page on the phone needs no updating: the computer serves it, so it is always the computer's version.

## Building a standalone program

Windows: double-click `scripts\build-windows.bat`. It produces `PhoneRemote.exe` (about 20 MB) in `dist\`. Copy it to another Windows computer and double-click it; Python is not needed there.

macOS: run `sh scripts/build-macos.sh`. It produces `PhoneRemote.app` and a zip of it in `dist/`. The app only runs on the kind of Mac that built it (Apple chip or Intel), and it is not signed with an Apple developer account, so another Mac asks for confirmation the first time it is opened.

Releases are built the same way by GitHub Actions: pushing a tag such as `v0.5.0` runs the tests, builds the exe and both Mac apps, and publishes them on the releases page (`.github/workflows/release.yml`). Pull requests get the tests and a trial build.

## The four screens

![The four screens](docs/screens.png)

(The screenshot shows an older version with Chinese labels.)

- **Play**: what is playing (an icon for music or video, the title and artist, and the app playing it), a draggable progress bar, touchpad, Fullscreen / Exit / OK, and four sets of keys for general use, Bilibili, YouTube and music.
- **Browse**: touchpad, browser back and forward, reload, zoom, tab switching, and shortcuts to your usual sites.
- **Type**: type or dictate on the phone and send the text to whatever input has focus on the computer. Tapping the text box makes it fill the screen, so long text is easy to write; line breaks are kept (they are typed as Shift+Enter, because plain Enter would send a half-written message in most chat boxes), up to 10,000 characters. Below it are editing keys (Enter, New line, Backspace, Select all, Undo, Tab, Address bar) and control keys named after what they are, since each means something different from one program to the next: Up, Down, Shift+Tab, Esc, Ctrl+C. "New AI chat" sends Ctrl/Cmd+Shift+O, which starts a new conversation in ChatGPT.
- **Windows**: lists the windows open on the computer; tap one to bring it to the front. Maximize and minimize are here too. "To other screen" (Windows only) moves the current window to the next monitor, for example sending a video to a TV that is plugged in as a second screen. On a Mac the list shows apps.

The touchpad works like a laptop's: slide to move the pointer, tap to click, tap with two fingers to right-click, slide with two fingers to scroll (a quick flick keeps scrolling and slows to a stop). To drag, rest a finger on it until the border turns solid, then slide; lifting the finger lets go.

A playback bar stays at the bottom of every screen: volume down and up, rewind, play or pause, fast forward, mute.

Key colours show what a key does: blue for playback and the main action, cyan for volume, green for confirming, yellow for navigation, red for exit, close and delete. The play / pause key is the cyan of the logo, since it is the key you press most.

### Site shortcuts

The Sites row on the Browse screen holds up to 4 shortcuts; tapping one opens the site in the computer's browser. Tap "+ Add" and enter an address (`bilibili.com` is enough). Leave the name empty to use the page's own title; the dot takes its colour from the site's theme colour or icon. Hold a shortcut to edit or delete it (from a keyboard, the menu key or Shift+F10 does the same). They are stored under `shortcuts` in the configuration file.

### Tablets, and holding the phone sideways

The page rearranges itself to use the screen it is on:

- **Phone held sideways**: navigation down the left edge, keys in the middle, the touchpad on the right over the full height.
- **Tablet held sideways**: the same three columns with larger keys. There is room to show the general keys and one site's keys together, and the site shortcuts on the Play screen.
- **Upright tablet**: the touchpad across the top and the keys in two columns under it.

If you would rather steer the pointer with your left thumb, open Settings (the gear) and move the touchpad to the left; it applies whenever the screen is wide.

### Keyboards and screen readers

Every key, the navigation and the settings also work from a keyboard, a switch, or a screen reader such as TalkBack or VoiceOver: each has a spoken name, and the chosen screen and tab are announced. The touchpad and dragging the progress bar still need a finger; the scroll keys and the Back and Fwd keys do the same jobs.

### Controlling more than one computer

Run the program on each computer. Scan one computer's QR code to open the remote, then tap the computer's name at the top:

- **Add computer…**: paste the address from the other computer's QR page (scan its QR code with the camera and copy the link it finds; hold the link if there is no Copy button). You can give it a name at the same time.
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
  update.py        asks GitHub whether a newer release exists
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

## Support

Phone Remote is free. If it is useful to you, you can buy me a coffee:

<a href="https://buymeacoffee.com/chrisye"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" height="40"></a>

## Icons

Icons come from [Tabler Icons](https://tabler.io/icons) (MIT License). Only the few dozen in use are bundled into `src/phone_remote/web/icons.svg`, so nothing is fetched from the internet at run time. To add or remove icons, see `scripts/build-icons.py`.

The logo is drawn in `src/phone_remote/logo.py`: a larger version for 48 px and up, and a simpler one with a single signal arc for 16 and 32 px. `scripts/build-logo.py` writes every file from it: the favicons and home screen icons in `web/` (one for iOS, and for Android the four listed in `web/manifest.webmanifest`, two of them filled to the corners so the launcher can cut them to its own shape), `docs/logo.svg`, and the Windows icon `scripts/phone-remote.ico`. The tray icon is drawn from the same module when the program starts.
