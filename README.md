## v30.0.2 interaction-size correction

Idle, drag/cursor-follow, petting and sad rows now share the walk row's 450px maximum full-body height and 489px ground baseline at the 512px source canvas. Use one scale per entire row, preserving genuine bending between frames. Previously idle was slightly too large and the drag/petting rows were smaller. This is runtime scaling of the existing full-resolution artwork, not regenerated art. Unit checks verify scale, ground alignment and unclipped alpha bounds for every frame in these four rows.

# v30 transition fix

The 11:11 recording showed vertical jumps around cloud resizing and the right-click menu. Previous checks only verified the settled layout and missed a stale image displayed at the new window origin before the next tick. Rebuild and flush the scene synchronously during resize. Close ordinary chatter before posting the context menu; suppress hover, movement and scheduled behavior while the menu is posted. Keep previous v29 fixes.

Regression: 85 unit tests pass. Native Windows validation now checks the immediate rendered anchor across 20 cloud open/close cycles and posted-menu behavior, in addition to existing reminder, activity and edge checks. No new artwork is included. Artistic consistency and physical multi-monitor gaps remain limitations.

# Water Panda v29 for Windows

Fixes hover interruptions, cloud-induced position shifts, expanded-cloud dragging, stale bored-walk state, offscreen ledge destinations and malformed activity settings. See Water_Panda_Final_Audit.md for the complete audit and limits.

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
