## v28.0.0

Fixes the walking-in-place behavior seen in the hover recording. The panda stands while its hover cloud pauses travel, then resumes walking when the cloud closes. Existing screen-edge roaming and water-hour settings are retained.

# Water Panda v27 for Windows

A local desktop panda with water tracking, hula-hoop movement breaks, wristwatch personal reminders, bamboo feeding and configurable automatic activities.

Download Water_Panda_Setup.exe from the latest tagged GitHub release, close the old copy and install. The installer has a panda-face icon and needs no Python or administrator rights. Your local history and settings are preserved.

Double-click opens Panda Home. Right-click contains Home, roaming, Water now, water Pause/Resume, Add reminder and Exit. Reminder dialogue is an in-canvas cloud above the panda's right side. Home supplies all 27 activity controls, a 19-item selectable routine pool, scrollable behaviour settings, history, CSV export and inline Undo confirmation.

**Not yet now recovers after eight seconds without requiring Pause.** It logs nothing and keeps the next water reminder 30 minutes away. Snooze is ten minutes. Water accepted at 100/200/300 ml triggers a thank-you bow.

v26 replaces rig walking with six coherent side-profile phases, combines duplicate grooming/rest/log controls, improves compact clouds and jump clearance, fixes tray registration and local database connection handling, and prevents Panda Home being covered by the ordinary pet.

See [the complete replication prompt](Water_Panda_Replication_Prompt.md) for exact features, all source sheets, settings and full setup/update/build commands. See [the point-by-point audit](Water_Panda_Final_Audit.md) for evidence and limits. Generated source poses are draft artwork; CI proves functionality, not perfect animation on every user's display.

Build on Windows with Python 3.12 and Inno Setup 6:

```powershell
py -3.12 -m pip install -r requirements-build.txt
py -3.12 -m unittest discover -s tests -v
py -3.12 -m PyInstaller --noconfirm --clean WaterPanda.spec
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "installer\WaterPanda.iss"
```

Output: installer\output\Water_Panda_Setup.exe. Main pushes create build artifacts; version tags publish release installers after packaged Windows UI validation. There is no silent updater. Local data stays in %LOCALAPPDATA%\WaterPuppy; runtime has no external AI, email, clipboard, microphone or camera integration.

## v26 changes

Behaviour > Water reminder hours adds From/Until times. Enable Only ask during these hours and save. Daytime and overnight ranges work; equal times mean all day. Automatic water offers end at the closing time, snoozes wait for the next opening when needed, and Water now remains available anytime. Existing users retain all-day behaviour until enabling the window.

Play on log now starts cheerful setup/balancing immediately, without the bored edge shuffle. Cloud text is larger, buttons use compact readable labels and water amounts remain explicitly labelled in ml. The previous Not yet recovery remains eight seconds.

## v27 screen edges

Removed the extra 42px bottom clearance and 24px manual walk inset. Regular roaming can choose all four screen edges. Cursor Follow keeps its usual interior distance, but approaches the screen boundary when the pointer is near it. The full transparent pet canvas stays inside the physical desktop bounds; artwork margins remain to prevent clipping.
