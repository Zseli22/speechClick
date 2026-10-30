# speechClick

speechClick is a small NVDA add-on that keeps fast scrolling from turning speech into noise.

When NVDA is asked to speak a string that is very similar to the one it spoke a moment ago, speechClick plays a short click instead of the speech. Text that differs meaningfully is always spoken in full, however quickly it follows. A list or a paragraph flying past ends up sounding like a steady click rather than a wall of half-finished words.

## Requirements

* NVDA 2023.1 or later. Tested with NVDA 2023.3 and 2026.3.

## Installation

1. Download `speechClick-1.0.0.nvda-addon` from the [latest release](https://github.com/Zseli22/speechClick/releases/latest).
2. Press Enter on the downloaded file and confirm the installation.
3. NVDA restarts and the add-on is active.

speechClick is not in the NVDA Add-on Store yet, so the release file is the only way to install it at the moment.

## Usage

The add-on needs no configuration to be useful; it starts working as soon as it is installed.

| Command | Description |
| --- | --- |
| `NVDA+control+shift+s` | Toggles speechClick on and off |

The command is listed in NVDA's Input Gestures dialog under the "Speech Click" category, where it can be reassigned.

## Settings

Open NVDA menu → Preferences → Settings → Speech Click.

| Setting | Default | Range |
| --- | --- | --- |
| Enable speech click filter | on | on / off |
| Minimum time between repeated speech (ms) | 50 | 1–5000 |
| Speech resume delay after scrolling stops (ms) | 1000 | 0–30000 |

A click replaces speech only when three things are true: the new utterance is at least 85% similar to the previous one, it arrives sooner than the minimum time, and it arrives sooner than the resume delay. In practice the smaller of those two values is the limit, so raising one of them alone has no effect once the other is lower.

* **Minimum time between repeated speech** — how close together two similar utterances must be before the second one becomes a click. Raise it to click more often, lower it to hear more of what is scrolling past.
* **Speech resume delay** — an upper bound on how long after the previous utterance a click may still be used. It is meant to stop the click from lingering after you have stopped scrolling: once the gap grows past this value, normal speech returns.

The similarity threshold is fixed at 85% and is not exposed in the settings.

## How it works

The add-on is a global plugin. On load it wraps `speech.speech.speak`; for each utterance it joins the text items, compares them with the previous utterance using `difflib.SequenceMatcher`, and checks the elapsed time. If the conditions above hold, it plays `click.wav` through `nvwave` and returns without speaking. Otherwise it calls the original method untouched. The original method is restored when the add-on is disabled or removed.

## Building from source

```powershell
git clone https://github.com/Zseli22/speechClick.git
cd speechClick
.\build.ps1
```

The script reads the version from `manifest.ini` and writes `dist\speechClick-<version>.nvda-addon`, which is the file to attach to a release. It packages only `manifest.ini`, `doc` and `globalPlugins`, and skips bytecode caches.

To try a change without building, copy `globalPlugins\speechClick` into `%APPDATA%\nvda\addons\speechClick\globalPlugins\` and restart NVDA.

## License

speechClick is released under the GNU General Public License version 2. See [LICENSE](LICENSE).

## Author

Evangelosz Nagy — [vangi.nagy@gmail.com](mailto:vangi.nagy@gmail.com)
