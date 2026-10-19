# Water Panda v38.0.0

Keep the existing cute panda: its large warm eyes, cream tuft, small body and original core artwork. This update includes the preceding shared-size and costume corrections without using the rejected adult panda redesign.

Add sixteen matching action poses and ten finite performances: kung fu practice, secret snack, noodle break, bamboo staff practice, wobbly balance, butterfly curiosity, shadow inspection, scroll doodling, sideways tumble and wobbly heroic landing. Each performance has setup, action and recovery, appears in Activities and Behaviour, and is interrupted by reminders. These are keyframe sequences; this release does not claim a fully rigged 3D character or newly drawn inbetween frames for every action.

Organic mode now respects the activity checkboxes, shuffles enabled activities fairly and retains prank cooldowns. The old full-default activity pool gains the new performances once; later disabled choices and Manual only remain saved. A pending hunger request prevents automatic snack performances. Sideways tumble uses the actual side-roll art, separately from the somersault.

Active redraws use a 40 ms interval (previously 80 ms). Fractional desktop coordinates survive rounding for the native window, and walk/run travel, legacy offsets, falling and particle timing are adjusted to retain their intended speed. Existing water amounts, snooze, decline, reminder history, night rest and theme effects remain available. The new props have explicit foreground masks so costumes do not cover bowls, scrolls, dumplings or staffs.

Build on Windows with `Build_Windows_v38.ps1`, or use the Windows Actions workflow. Installer version is 38.0.0. Install only after a successful Windows build and packaged UI validation.

Offline checks: `python -m unittest discover -s tests -q`. Runtime-rendered review: `python tools/review_character38.py`. New art source and review images are in `artwork/v38/`. Read `RELEASE_v38.md` for current validation and limitations.

## Previous release history

# Water Panda v37.0.0

This update enables a complete Organic routine on the first upgrade. All 21 everyday activities get a turn in a shuffled queue, including Somersault, Mirror surprise and Boo. Timing varies around the chosen interval and with personality; pranks have a 15-minute cooldown. Ordinary roaming cannot starve routines. Short spontaneous runs belong to locomotion, and edge activities approach an edge first. Water, movement and hunger keep their dedicated schedules and do not create random water-history records.

Night rest defaults to 22:00–07:00 in the computer's local time, even while you work. The panda approaches the nearest lower corner, settles, sleeps with breathing, briefly checks in roughly every 20 minutes and returns to sleep. Behaviour lets you choose hours, corner and check-in interval or disable night rest. Personal/water reminders take priority, and manual actions complete before returning to rest. Equal start/end times are rejected. Subsequent saved Behaviour choices, including Manual only, are preserved.

Headgear now fits the head and turns with the actual pose. Sleep artwork keeps a mostly upright head despite a sideways torso. Reviewed inner garment/turban linings are removed from the foreground; faces and props remain visible. The original character artwork and ghost bedsheet are retained.

Install the new Windows installer after exiting the old running copy. Settings, water history and personal reminders stay in the existing WaterPuppy data folder. This release includes source and build instructions. Automated Windows evidence covers the runner's monitor; it cannot establish appearance on every Windows 11 DPI arrangement.

## Earlier features and architecture

# Water Panda v36 for Windows

A small animated desktop panda with water/custom reminders, local history, feeding, configurable routines and sixteen seasonal themes.

v36 removes Fetch, rebuilds running and cursor avoidance, adds pillar peekaboo, keeps thematic outfits during actions and gives every Panda Home page measured margins and usable wheel scrolling. Diwali/New Year/birthday fireworks and Holi colour puffs are finite click-through effects with a setting. Reminders stop effects immediately.

Download the tagged family ZIP and run `Water_Panda_Setup.exe`; Python is needed only for source development. Close the existing panda before upgrading. Local settings/history are preserved.

Full-body seasonal scene art lives in `artwork/v32`; new running, peekaboo and shaded wardrobe component art lives in `artwork/v33`. The wardrobe is fitted to each action pose rather than replacing idle artwork only. Original good activity sheets are retained. See the complete replication prompt and final audit for scope, commands and limitations.

Validation: `python -m unittest discover -s tests -v`, followed by the packaged Windows workflow. A successful tagged run publishes an installer. Actual report/screenshots and hashes accompany the family ZIP. Passing tests do not prove perfect artistry or every user display arrangement.

The Activities page now shows the active theme scene by name, plus distinct fireworks/Holi effect controls where supported. Switching themes or the automatic calendar refreshes the list. Disabled effects remain visible with an explanation; active reminders disable activity controls. v36 also corrects the ghost hood opening during left-facing walk/run poses.


## Continuous ghost cloak correction (v36)

Replace the detached neck hood and belly bib with the generated one-piece ivory hood-and-cloak assets `wardrobe_spooky_full_front.png` and `wardrobe_spooky_full_profile.png`. `ghost_cloak.py` drapes continuous source bands around the reviewed pose landmarks, mirrors profile clothing for left travel and rotates only lying/inverted poses. Preserve the original face, limbs and foreground props; never create a flat hem by clipping a rectangular margin. The previous v34 eye-opening correction alone did not repair the costume silhouette. Original cloak source is retained in `artwork/v36/ghost_cloak_source.png`. This is pose-dependent compositing, not 264 newly drawn whole-body ghost frames.


## v36 full bedsheet and playful routines

The spooky appearance is a closed floor-length ivory bedsheet in every standing, walking, running, reminder and activity pose. Do not composite original black limbs, feet or ear shapes over the fabric. Preserve only the facial opening and activity props. Preserve the existing pumpkin-carving scene, with the same closed-sheet rendering. v35 left bare limbs and an apparent bib; its costume claim was insufficient. Source artwork is retained at `artwork/v36/ghost_sheet_source.png`.

Add distinct Mirror surprise and Boo prank controls to Activities and Selected routine. Mirror uses eight generated curious/startled/embarrassed/relieved poses and the exact same dressed sprite flipped inside a generated oval mirror; attire must match on both sides for every theme. Boo uses a quiet setup, jump reveal, own startled reaction and friendly recovery with cloud dialogue. These are finite sequences, not duplicate renamed buttons. Manual playback always works. Automatic performances require the Behaviour toggle and routine selection, with at least fifteen minutes between pranks. Defaults preserve gentle routines and disable automatic pranks. Reminders interrupt immediately.

New source artwork: `artwork/v36/mirror_reactions_source.png`, `artwork/v36/mirror_prop_source.png`. New runtime asset files: `assets/pack_mirror_0.png` through `_7.png` and `assets/mirror_prop.png`; `playful_activities.py` handles finite phases and reflection composition.
