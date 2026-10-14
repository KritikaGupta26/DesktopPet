# Water Panda v37.0.0 source package

This is updated application source with all runtime assets. It does not include a newly built Windows EXE. Publishing the build branch was blocked by automatic approval review, so packaged Windows checks remain pending. No old installer has been renamed or included as v37.

## Run the updated app

Exit the previous Water Panda copy. With Python 3.12 and the Windows Python launcher installed, double-click Run_Water_Panda.bat. The launcher checks Tkinter and Pillow and installs Pillow 11.3.0 if needed. It closes an older WaterPanda.exe process and runs the actual v37 source using the existing local settings, water history and reminder database.

## Build an installer

Install Python 3.12 and Inno Setup 6. In PowerShell from this folder, execute .\Build_Windows_v37.ps1. It installs the pinned build dependencies, runs regressions, builds the app, exercises the packaged Windows UI with isolated data, and produces installer\output\Water_Panda_Setup.exe only after checks pass. The build script does not install the resulting EXE automatically.

## Changes

- All 21 everyday actions run through an Organic routine with a shuffled fair queue, personality pacing and varied intervals. The old activity mode upgrades once to Organic; later choices are preserved.
- Somersault is included. Mirror surprise and Boo have a 15-minute prank cooldown. Feeding, movement, water and pointer controls retain their independent settings.
- Due routines can take a turn during ordinary roaming; manual movement, edge approaches and foreground reminders keep priority. Organic roaming occasionally includes short runs.
- Night rest uses local 22:00–07:00 defaults. It approaches a lower corner, settles, sleeps despite keyboard activity, briefly opens an eye and returns to sleep. Hours, corner and check-in interval are configurable. Reminders remain available.
- Headgear sizing, mirrored direction and pose orientation are corrected. Sleeping head orientation is handled separately from the torso. Reviewed rear garment/turban linings are removed from foreground rendering. The original ghost bedsheet renderer and foreground props remain.

## Validation limits

Audit_v37 contains local regression results and costume contact sheets. The structural render checks establish decoding, costume presence and transparent canvas corners. They do not certify every artistic detail, every animation transition, a Windows installer, or Windows 11 DPI behavior. The new native harness exercises automatic actions and night sleep/check-in/reminder priority, but those additions have not yet run on Windows.

The earlier family installer is v36.0.1. It will not acquire these changes by opening the source ZIP; run this source or build/install the new EXE.
