# Water Panda v25 for Windows

A local desktop panda with water tracking, hula-hoop movement breaks, wristwatch personal reminders, bamboo feeding and configurable automatic activities.

Download Water_Panda_Setup.exe from the latest tagged GitHub release, close the old copy and install. The installer has a panda-face icon and needs no Python or administrator rights. Your local history and settings are preserved.

Double-click opens Panda Home. Right-click contains Home, roaming, Water now, water Pause/Resume, Add reminder and Exit. Reminder dialogue is an in-canvas cloud above the panda's right side. Home supplies all 27 activity controls, a 19-item selectable routine pool, scrollable behaviour settings, history, CSV export and inline Undo confirmation.

**Not yet now recovers after eight seconds without requiring Pause.** It logs nothing and keeps the next water reminder 30 minutes away. Snooze is ten minutes. Water accepted at 100/200/300 ml triggers a thank-you bow.

v25 replaces rig walking with six coherent side-profile phases, combines duplicate grooming/rest/log controls, improves compact clouds and jump clearance, fixes tray registration and local database connection handling, and prevents Panda Home being covered by the ordinary pet.

See [the complete replication prompt](Water_Panda_Replication_Prompt.md) for exact features, all source sheets, settings and full setup/update/build commands. See [the point-by-point audit](Water_Panda_Final_Audit.md) for evidence and limits. Generated source poses are draft artwork; CI proves functionality, not perfect animation on every user's display.

Build on Windows with Python 3.12 and Inno Setup 6:

```powershell
py -3.12 -m pip install -r requirements-build.txt
py -3.12 -m unittest discover -s tests -v
py -3.12 -m PyInstaller --noconfirm --clean WaterPanda.spec
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer\WaterPanda.iss"
```

Output: installer\output\Water_Panda_Setup.exe. Main pushes create build artifacts; version tags publish release installers after packaged Windows UI validation. There is no silent updater. Local data stays in %LOCALAPPDATA%\WaterPuppy; runtime has no external AI, email, clipboard, microphone or camera integration.
