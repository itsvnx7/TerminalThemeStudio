# Terminal Theme Studio 2.0 — Glass & Segments

**Your terminal. Your style. Your rules.**

![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Windows Terminal](https://img.shields.io/badge/Windows-Terminal-0078D4)
![Version 2.0](https://img.shields.io/badge/Version-2.0-8B5CF6)
![Dependencies](https://img.shields.io/badge/Dependencies-None-2EA44F)

Customize Windows Terminal with persistent themes, acrylic blur, adjustable transparency and segmented prompts for CMD and PowerShell.

## Features

| Feature | Description |
| --- | --- |
| Color themes | Purple, blue, white and black |
| Glass effect | Adjustable opacity and optional acrylic blur |
| Title bar | Matching tab colors and optional acrylic tab row |
| Segmented prompt | Username, current directory, shell and clock |
| System panel | Local hardware and operating system information at startup |
| Persistence | Saved appearance across sessions |
| Recovery | Restore original managed settings and prompts |
| Lightweight | No third-party Python dependencies or administrator privileges required |

## Requirements

- Python 3.9 or newer
- Windows 11 and a recent version of Windows Terminal recommended
- Cascadia Code PL or a compatible Powerline font for arrow glyphs

This is a standalone Windows Terminal styling tool, not an EUF Terminal distribution. It does not replace EUF or install third-party software.

## Quick start

```cmd
git clone https://github.com/itsvnx7/TerminalThemeStudio.git
cd TerminalThemeStudio
python theme.py
```

Alternatively, select **Code → Download ZIP** on GitHub, extract the archive and run `python theme.py` in the extracted folder. Keep `theme.py`, `style.py`, `panel.py` and `config.json` together.

Close all Windows Terminal windows and reopen CMD or PowerShell. If the CMD prompt has not changed, sign out and back in. If the legacy console opens, select Windows Terminal under **Settings → Startup → Default terminal application**.

Version 1 users: version 2 reuses the existing original-settings backup. Use version 2 for future changes and restoration.

## Configuration

```json
{
    "theme": "purple",
    "opacity": 50,
    "acrylic": true,
    "glass_titlebar": true,
    "custom_prompt": true,
    "startup_panel": true,
    "powerline": true,
    "font_face": "Cascadia Code PL",
    "set_default_terminal": true,
    "custom_colors": {}
}
```

- `theme`: `purple`, `blue`, `white`, `black`, `off`. Off restores the saved appearance and shell changes.
- `opacity`: 0–100 percent opaque; 30 = very transparent, 50 = medium, 70 = less transparent. 100 = solid.
- `acrylic`: false for clear see-through content; true for blurred content. Windows controls actual compositing.
- `glass_titlebar`: true enables the Windows Terminal acrylic tab row (native fixed 50% acrylic), removes the solid gray tab-row color and keeps the active tab matched to the theme. The selected tab itself may remain solid; Windows Terminal controls this. If false, use a solid matching title bar.
- `custom_prompt`: segmented username, live working directory, shell and clock. PowerShell also shows last-command duration and error indicator. CMD time includes hundredths of a second and does not support command duration with its native prompt.
- `startup_panel`: local boxed system info (CPU, GPU when detectable, logical threads, RAM, disk, OS, user, uptime). PowerShell shows it in interactive Windows Terminal sessions. CMD shows it when opened via the standard Windows Terminal CMD profile; direct CMD launches from Win+R or another program may show only the prompt. Existing custom CMD launch commands are preserved. No global CMD AutoRun hook is installed.
- `powerline`: false uses plain separators if the arrow glyphs appear as boxes. `font_face`: defaults to Cascadia Code PL; if missing, select a locally installed Powerline/Nerd Font or use `Cascadia Code` with `powerline: false`.
- `set_default_terminal`: true sets the per-user Windows Terminal preference. False restores the prior preference if managed by the tool.
- `custom_colors`: optional overrides for background, foreground, cursorColor, selectionBackground using #RRGGBB. Prompt segment palettes follow the named theme.

Acrylic blur is enabled by default. To see the blur, enable Windows Settings > Personalization > Colors > Transparency effects.

Edit config.json and rerun `python theme.py` to apply. Command line theme/opacity changes save to config.json:

```cmd
python theme.py --theme blue --opacity 35
python theme.py --theme purple --opacity 50
python theme.py --theme white --opacity 85
python theme.py --theme black --opacity 70
python theme.py --dry-run
python theme.py --restore
```

## Safety, compatibility & recovery

The tool changes per-user Windows Terminal settings (all existing profiles), the per-user `PROMPT` environment variable, and adds a clearly marked block to detected console PowerShell profiles. It writes helpers and original backups to `%LOCALAPPDATA%\TerminalThemeStudio`. No startup tasks, global CMD AutoRun, downloads, network calls, or policy changes. Python must remain installed for the info panel. Existing shell sessions need reopening. Windows PowerShell execution policy, signed profiles (left unchanged), custom shell launch commands, external prompt tools and managed-device policies can prevent or override the appearance. Direct CMD shells outside Windows Terminal may inherit the prompt but not the theme; EUF and other applications may draw their own prompts/colors.

`python theme.py --restore` removes the managed theme and prompt, restores original appearance and terminal preference, removes the marked PowerShell profile block, and preserves other profile text. It leaves backup/helper files on disk. If the script reports an error, rerun or restore; backups are saved before changes. JSONC comments and formatting are removed when rewriting Terminal settings; exact original snapshots are in the backup directory. Restore is field-based for managed appearance fields (including font, padding, scrollbar, title bar and cursor), so later manual changes to those fields may be reverted. Do not run v1 after installing v2. 

Run the included offline unit tests with `python -m unittest discover -s tests -v`. These exercise sample settings and generated prompt/profile text without touching the registry or real shell profiles. Actual Windows appearance, PowerShell runtime, and registry behavior have not been tested here. Reference: https://learn.microsoft.com/windows/terminal/customize-settings/appearance and https://learn.microsoft.com/windows/terminal/customize-settings/themes

## Troubleshooting

| Problem | Solution |
| --- | --- |
| Blur is missing | Enable Windows transparency effects, set `acrylic` to `true` and lower opacity. |
| Arrow symbols appear as boxes | Use Cascadia Code PL or set `powerline` to `false`. |
| CMD prompt did not change | Close all terminal windows; sign out and back in if needed. |
| PowerShell prompt did not change | Check profile restrictions or other prompt tools. |
| Want to undo changes | Run `python theme.py --restore`. |

## Feedback

Found a bug or have a feature request? [Open an issue](https://github.com/itsvnx7/TerminalThemeStudio/issues).

Project maintained by [itsvnx7](https://github.com/itsvnx7).

## License

MIT License

Copyright (c) 2026 itsvnx7

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
