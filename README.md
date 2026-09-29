# Water Panda for Windows

Water Panda is a local Windows desktop companion with water tracking, movement reminders, personal reminders and animated panda activities.

## Install

Download `Water_Panda_Setup.exe` from the latest GitHub Actions artifact or tagged release, open it and select **Start Water Panda** when installation finishes. The installer uses a panda-face icon and does not require a separate Python installation.

## Controls

Double-click the panda to open Panda Home. The minimal panda and tray right-click menus contain:

- Open Panda Home
- Enable or disable roaming
- Ask for water now
- Pause water reminders for one hour
- Resume water reminders
- Add personal reminder
- Exit Water Panda

Panda Home contains water history, reminders, settings and the complete **Panda activities** page. Activities include walking, fetch, bored-on-log, kung-fu, sleep, meditation, bamboo eating, bamboo hanging, staff practice and reminder previews.

## Privacy and updates

Water history, personal reminders and preferences remain local in `%LOCALAPPDATA%\WaterPuppy`. Installer upgrades replace application files without deleting `water_history.db` or `settings.json`.

## Build the installer

The GitHub workflow builds on a genuine Windows runner:

1. PyInstaller creates the windowed `WaterPanda.exe` application directory.
2. Automated tests verify source, assets, icon and menu structure.
3. Inno Setup packages `Water_Panda_Setup.exe`.
4. Every push to `main` stores a downloadable workflow artifact.
5. Tags such as `v14.0.0` also publish the installer as a GitHub Release.

To build manually on Windows:

```powershell
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
pyinstaller --noconfirm --clean WaterPanda.spec
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer\WaterPanda.iss"
```

The completed installer is written to `installer\output\Water_Panda_Setup.exe`.
