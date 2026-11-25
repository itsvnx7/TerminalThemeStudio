# Terminal Theme Studio 2.0 — Glass & Segments

A local Python tool for permanent Windows Terminal styling, including the tab row and PowerShell/CMD prompt. Features a configurable glass appearance, Powerline-style prompts, and a local startup system-information panel. This is a standalone Windows Terminal styling tool, not an EUF Terminal distribution. Does not replace EUF or install third-party software. Python 3.9+ and a recent Windows Terminal on Windows 11 recommended.

## Install / upgrade

1. Extract all files into one folder. Keep `theme.py`, `style.py`, `panel.py`, and `config.json` together.
2. Open that folder in Explorer, type `cmd` in its address bar, press Enter.
3. Run `python theme.py` (or `py theme.py`). No administrator permissions or pip installs required.
4. Close **all** Windows Terminal windows and reopen CMD or PowerShell. If the CMD prompt is unchanged, sign out and sign back in so the updated per-user PROMPT environment variable is inherited. If the old console host opens, choose Windows Terminal in Settings > Startup > Default terminal application.

If you used version 1, version 2 reuses its existing original-settings backup. Use the version 2 script for future changes and restoration.

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
- `acrylic`: false for clear see-through content like the reference; true for blurred content. Windows controls actual compositing.
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

## Scope & recovery

The tool changes per-user Windows Terminal settings (all existing profiles), the per-user `PROMPT` environment variable, and adds a clearly marked block to detected console PowerShell profiles. It writes helpers and original backups to `%LOCALAPPDATA%\TerminalThemeStudio`. No startup tasks, global CMD AutoRun, downloads, network calls, or policy changes. Python must remain installed for the info panel. Existing shell sessions need reopening. Windows PowerShell execution policy, signed profiles (left unchanged), custom shell launch commands, external prompt tools and managed-device policies can prevent or override the appearance. Direct CMD shells outside Windows Terminal may inherit the prompt but not the theme; EUF and other applications may draw their own prompts/colors.

`python theme.py --restore` removes the managed theme and prompt, restores original appearance and terminal preference, removes the marked PowerShell profile block, and preserves other profile text. It leaves backup/helper files on disk. If the script reports an error, rerun or restore; backups are saved before changes. JSONC comments and formatting are removed when rewriting Terminal settings; exact original snapshots are in the backup directory. Restore is field-based for managed appearance fields (including font, padding, scrollbar, title bar and cursor), so later manual changes to those fields may be reverted. Do not run v1 after installing v2. 

Run the included offline unit tests with `python -m unittest discover -s tests -v`. These exercise sample settings and generated prompt/profile text without touching the registry or real shell profiles. Actual Windows appearance, PowerShell runtime, and registry behavior have not been tested here. Reference: https://learn.microsoft.com/windows/terminal/customize-settings/appearance and https://learn.microsoft.com/windows/terminal/customize-settings/themes

## Publishing and development

The project has no third-party Python dependencies. Keep the Python files and configuration together. The `.gitignore` excludes interpreter caches, virtual environments and local backup files. Do not upload your actual Windows Terminal settings, registry backups, or generated shell profiles.

To publish, create an empty repository on GitHub, then run these commands from the extracted folder (replace `YOUR-USERNAME` with your GitHub username):

```sh
git init
git add .
git commit -m "Initial release: Terminal Theme Studio 2.0"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/TerminalThemeStudio.git
git push -u origin main
```

Alternatively, use GitHub's Add file > Upload files and upload the extracted files, not the ZIP.

No license has been selected. Before distributing the project as open source, choose a license that reflects how you want others to use it.
