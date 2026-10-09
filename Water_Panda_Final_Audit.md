# v29 audit and fixes

The 9 October 10:24 recording showed hover interruptions during movement. The audit also found geometry, stale-action, Windows API and malformed-settings defects.

| Area | Finding / result |
| --- | --- |
| Hover and cursor follow | Hover total cloud now opens only while idle. It no longer interrupts walking, following or escaping. Deliberate chatter still pauses travel and displays standing. |
| Cloud anchoring | Opening and closing a cloud preserves the panda's screen position. Use upper-right normally, left near the right edge and below near the top. Same canvas, no new popup. Buttons and text keep their readable orientation/order. |
| Dragging with clouds | Drag uses screen-pointer displacement from the panda anchor, rather than switching between root-window and panda coordinates. Can reach all edges with the cloud open. |
| Bored approach | Removed unreachable duplicate branch that hid the slow full-body shuffle. Ordinary Walk also clears a stale pending edge action. |
| Ledges | Clamp destinations to the desktop; a window near the top cannot send the panda above the screen. |
| Throw and jump | Upward throws bounce at the top. Jump displacement respects available space above the panda. |
| Fetch and reminders | Fetch waits while a general reminder is active. |
| Settings | Invalid list/dict activity values are discarded rather than raising an unhashable-value startup exception. |
| Windows integration | Use absolute Win32 placement for negative monitor coordinates; explicitly type pointer-sized arguments for fullscreen/ledge checks. Correct idle-time calculation across the 32-bit last-input tick wrap. |
| Water | Reviewed 100/200/300 logging-once, Not yet 8-second recovery, Snooze 10 minutes, Pause/Resume, daily/overnight windows, manual override and personal-reminder preemption. Regression and native checks retained. |
| Other reminders | Reviewed personal due-date storage, Done/Snooze, movement timer and shared cloud actions. |
| All activities / artwork | Existing activity-dispatch/native renderer checks retained. All 262 exported pack PNGs decode and have nonempty alpha bounds inside the canvas. No new artwork is claimed. |
| Data / UI / packaging | Existing history, totals, CSV, confirmed Undo, Home, tray, persistent settings, icon and installer checks retained. |

Local regression suite: 81 tests passed. Packaged Windows results are recorded in the included report after the build.

Limits: these checks cannot certify perfect artistic gait or every physical multi-monitor/DPI combination. The current bounds are the virtual desktop rectangle; gaps between disjoint monitors remain an unverified limitation. Sprite alpha padding is preserved. No AI services, email access, battery watcher or browser-tab watcher were added.

## v28 recording fix

- Reproduction: hover over a walking/following panda. The total-water cloud stops travel but previously left the walk frames running.
- Fix: paused locomotion renders standing and resets gait phase. Resume walking after the cloud closes; no artwork replacement in this release.
- Regression coverage: paused walk/run/follow rendering, resume after chatter, cursor stand-off rest. Native Windows checks include real pointer movement, hover cloud pause, standing capture and movement resume.
- Previous v27 edge behavior and v26 water hours remain covered.

# v27 edge-travel update

Supersedes previous 42px bottom clearance and manual walking side inset. Ordinary roaming can visit all four edges. Cursor Follow uses zero additional standoff near the screen boundary while keeping the interior 140px distance. Clamp the complete 180×184 pet canvas within physical desktop bounds, including negative virtual-desktop coordinates. Preserve artwork padding, reminder cloud bounds, v26 water hours and all other behaviours. No walk artwork is replaced in this patch.

# v26 update contract

This update supersedes the older v25 log and cloud instructions below. Add persisted optional daily water hours in Behaviour with From/Until fields, validation, overnight support and start-inclusive/end-exclusive boundaries. Equal hours mean all day. Existing installations default to the old all-day behaviour until enabled. Scheduled offers close at the end; snoozes wait for the next window when needed. Manual Water now works at any time. Preserve the eight-second Not yet recovery and water history.

Play on log directly uses cheerful setup for four seconds and balancing for twelve seconds, without bored edge travel. Keep the bored edge routine separate. Increase cloud main/body/button text to readable 15/13/12–14 pixel fonts; compact button labels retain ml context. Do not claim unrelated walking defects fixed without concrete reproduction.

# Water Panda v25: point-by-point audit

This audit separates implemented functionality, native executable evidence and visual limitations. The original source pack contains draft generated poses; neither regression tests nor build success proves perfect anatomical continuity. See BUILD_MANIFEST.json and Windows_UI_Evidence/report.json in the family ZIP for the delivered commit, hashes, native checks and screenshots.

## Latest reported bug

Not yet now sets a bounded eight-second sad reaction and a 30-minute water deadline. _tick calls _update_water_response each cycle; expiration clears the state and resumes normal behaviour without Pause. It does not log water. Local regression and native executable checks cover this exact path.

## Requirement coverage

All requirement IDs in the complete prompt appear exactly once below. “Implemented” denotes the v25 code/asset route, not a claim that artwork is artistically perfect.

| ID | Requirement | Implementation/evidence and limit |
| --- | --- | --- |
| R001 | Continue the existing standalone Windows desktop panda in KritikaGupta26/DesktopPet. Do not replace it with a ChatGPT Pet or silently rewrite the stack. | Repository, v25 installer configuration and delivered ZIP/prompt/audit; no ChatGPT Pets integration. |
| R002 | Deliver a Windows EXE installer with panda-face icon, a shareable family ZIP, full replication prompt and requirement-by-requirement audit. | Repository, v25 installer configuration and delivered ZIP/prompt/audit; no ChatGPT Pets integration. |
| R003 | Use GitHub for source and future tagged installer updates. Provide complete clone, pull, build and installer update commands. | Repository, v25 installer configuration and delivered ZIP/prompt/audit; no ChatGPT Pets integration. |
| R004 | Close the old running copy before upgrades; preserve settings, water history and personal reminders. Show version 25 in Panda Home. | Repository, v25 installer configuration and delivered ZIP/prompt/audit; no ChatGPT Pets integration. |
| R005 | Use the Riya Odedara Matchi guide as inspiration for a gentle, cheeky wellness companion and deliberate privacy. Its product-access claims are not app requirements. | Repository, v25 installer configuration and delivered ZIP/prompt/audit; no ChatGPT Pets integration. |
| R006 | Keep the established soft cream and charcoal panda identity, expressive face, rounded proportions and polished 3D animated-film style. Avoid pixel art and green outlines. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R007 | Use high-resolution transparent source poses, high-quality downsampling and consistent perceived body scale across standing, walking, sitting, resting and meditation. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R008 | Preserve complete ears, feet, paws, body curves and props. No flat cropped base, painted floor line or cut character. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R009 | Walking must use full coherent poses, opposite arm/leg coordination, readable contacts, passing phases and controlled cadence. Do not animate separated limb parts or translate one fixed pose. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R010 | Use six selected v25 side-profile walk phases from the new atlas, mirror them for left travel and synchronize ground travel with the animation cycle. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R011 | Keep the original run distinct from walking; make follow and avoid change actual desktop position rather than only pose. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R012 | Jump has anticipation, airborne and landing poses with enough transparent vertical clearance to avoid clipped ears. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R013 | Wave with the same paw across frames; use a genuine torso bow with readable depth. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R014 | Keep one recognizable somersault. Remove the redundant side-roll control rather than offering the same animation under two names. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R015 | Use a wristwatch gesture for actual personal reminders and a waist-level hula hoop for movement breaks. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R016 | Water glass belongs to the same visual style and stays attached to the paws. Bring it from behind, around the side, then offer with both paws. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R017 | Water offer plays once and holds the last pose while awaiting an answer. Drinking triggers a thank-you bow. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R018 | Bored approach should be a slow head-down shuffle toward the nearest edge, followed by slow log sitting and balancing. Do not display a bamboo staff randomly in open desktop space. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R019 | Hang on bamboo at an edge, with correct travel direction and screen bounds. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R020 | Meditation uses the high-resolution seated pose with gentle breathing. Do not promise new settle/exit artwork unless it is actually created and verified. | HD pose and gentle breathing implemented; new meditation settle/exit artwork has not been generated. |
| R021 | Inspect every source sheet, exported pose, playback route, scale, alpha edge, clipping and timing. Code tests alone cannot certify artistic perfection. | Runtime sprite routes, manifest/export tests, accepted walk previews and captured UI. Draft source artwork still requires subjective user-device review. |
| R022 | Ask for water every 30 minutes and provide Ask for water now. | Reminder regression tests and packaged Windows UI checks; bounded Not yet, no logging, snoozes and water deferral. |
| R023 | Offer 100, 200 and 300 ml choices; each accepted click logs once. No fixed daily intake target. | Reminder regression tests and packaged Windows UI checks; bounded Not yet, no logging, snoozes and water deferral. |
| R024 | Not yet must dismiss the offer, show a brief eight-second reaction, then return to normal automatically. Never remain stuck on “I will wait” until Pause. | Reminder regression tests and packaged Windows UI checks; bounded Not yet, no logging, snoozes and water deferral. |
| R025 | Not yet logs nothing and schedules the next ordinary water reminder 30 minutes later. | Reminder regression tests and packaged Windows UI checks; bounded Not yet, no logging, snoozes and water deferral. |
| R026 | Water Snooze postpones the reminder by 10 minutes without logging. | Reminder regression tests and packaged Windows UI checks; bounded Not yet, no logging, snoozes and water deferral. |
| R027 | Pause water for one hour; Resume restores reminders. Pausing water must not close an unrelated personal reminder. | Reminder regression tests and packaged Windows UI checks; bounded Not yet, no logging, snoozes and water deferral. |
| R028 | Custom timed reminders may preempt a water offer; when dismissed or snoozed, resume the deferred offer without logging or overlapping clouds. | Reminder regression tests and packaged Windows UI checks; bounded Not yet, no logging, snoozes and water deferral. |
| R029 | All pet chatter, water, movement, hunger and personal reminder dialogue uses rounded cloud-shaped canvas artwork above and to the right of the panda. | Canvas clouds, pixel wrapping, inline validation, native screenshots and button-bounds checks at simulated font scales. |
| R030 | Clouds must remain proportionate to the panda. Use compact text and pixel-measured wrapping, not oversized square dialogue boxes. | Canvas clouds, pixel wrapping, inline validation, native screenshots and button-bounds checks at simulated font scales. |
| R031 | No separate native reminder pop-up windows. Panda Home/settings and the explicit CSV save chooser are normal user-requested windows. | Canvas clouds, pixel wrapping, inline validation, native screenshots and button-bounds checks at simulated font scales. |
| R032 | Water includes Not yet and Snooze; movement and personal reminders include Done and Snooze. | Canvas clouds, pixel wrapping, inline validation, native screenshots and button-bounds checks at simulated font scales. |
| R033 | Movement reminders show the hula-hooping panda, have a configurable enabled state and interval, and ask the user to move. | Canvas clouds, pixel wrapping, inline validation, native screenshots and button-bounds checks at simulated font scales. |
| R034 | Personal reminders accept a title, date and future local time, including 1 PM, 1:00 PM and 13:00. Store due instants consistently in UTC and display local time. | Canvas clouds, pixel wrapping, inline validation, native screenshots and button-bounds checks at simulated font scales. |
| R035 | Validate reminder input inline. Keep full titles in Home while wrapping and ellipsizing long cloud titles. | Canvas clouds, pixel wrapping, inline validation, native screenshots and button-bounds checks at simulated font scales. |
| R036 | Ensure button labels stay inside cloud buttons under tested text scaling. Clamp window movement to desktop work areas. | Canvas clouds, pixel wrapping, inline validation, native screenshots and button-bounds checks at simulated font scales. |
| R037 | Allow dragging, petting and double-click opening of Panda Home. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R038 | Keep right-click and tray menus minimal: Home, roaming on/off, water now, water pause/resume, add reminder and Exit. No old test-automation menu. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R039 | Default pointer mode is Off. Hover alone must not make the panda escape. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R040 | Persistent Follow and Avoid settings must perform actual motion; manual activity actions are temporary. Follow can run when ordinary roaming is disabled. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R041 | Roaming works independently of hover. Provide rest interval and walk cadence settings. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R042 | Provide Calm, Balanced and Playful personalities with deliberate pacing and behaviour choices. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R043 | Use configurable Gentle routine, Selected routine or Manual only. Let users select the automatic activity pool and its interval. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R044 | Automatic activities must not repeatedly replace a manual action or reminder. Pause ambient activity while the user configures Panda Home. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R045 | Group wash face, ear rub and belly scratch as one Grooming sequence. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R046 | Group yawn/stretch, lazy stretch, sleep and wake-up as one Wind down sequence. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R047 | Group bored edge approach, sitting on log and balancing as one Play on log activity. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R048 | Keep feed, water, movement, pointer control and locomotion out of the generic automatic activity pool. Their own controls and schedules govern them. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R049 | Add configurable hunger reminders. Hungry panda asks for bamboo; one click feeds it and resets hunger timing. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R050 | Use a coherent bamboo eating sequence and a separate hunger deadline, not arbitrary repeated eating animations. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R051 | Keep fetch as chase, pickup/catch, return/offer and celebration. Keep peekaboo as the supplied animation; do not claim an advanced window-occlusion game. | Existing animation and fetch route implemented; advanced occlusion/game scoring and dedicated carrying gait are not supplied. |
| R052 | Keep kung fu, sploot, dance, sneeze, hiccup, clap, kiss, wave, bow, petting, meditation and celebration useful through selected automatic routines or direct controls. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R053 | Apply fullscreen hiding and inactivity settings. Keep important alerts visible according to the implemented priority. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R054 | Panda Home should not be covered by the ordinary pet window. Make Behaviour settings scrollable on smaller screens. | Activity catalog, explicit grouped sequences, configurable 19-item pool, native activity dispatch, live OS pointer-follow and feeding checks. |
| R055 | Keep water totals, entry history, recent daily chart, seven-day summaries and CSV export in Home. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R056 | Undo asks for inline confirmation and deletes only the latest entry after confirmation; no disruptive modal confirmation. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R057 | Persist name, personality, routines, timing, pointer mode, roaming, sound, fullscreen, sleep and hunger preferences. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R058 | Keep pats/adoption age and remembered home position, restoring positions within valid screen bounds. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R059 | Keep settings and SQLite data local in %LOCALAPPDATA%\WaterPuppy. Close every SQLite connection properly. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R060 | Use correct 64-bit Windows ctypes signatures and verify that the real tray icon registers. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R061 | No runtime AI service, microphone, camera, clipboard inspection, screen-content reading, email access or file organization is implied by this app. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R062 | The guide’s battery warning, excessive-tab warning, Pomodoro, email notifications, content drafting and file organization are future optional integrations, not implemented core features. | Explicitly outside core v25: these guide ideas are not implemented or implicitly enabled. |
| R063 | Diagnostic screenshot capture runs only in the explicit --verify-ui build harness with isolated data, not as ordinary user monitoring. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R064 | Check existing settings migration and UTC reminder migration without deleting user records. | Local SQLite/settings, proper connection closure, native tray/export/undo/persistence checks; no runtime AI or content monitoring. |
| R065 | Account for all 17 original sheets, 240 original frame slots and 47 source rows, including 45 distinct groups and two alternate variants. | 47-row manifest, 17-sheet inventory, original draft provenance, six-frame walk replacement, packaged CI evidence and release validation. |
| R066 | Preserve raw source sheets and the manifest. A source row can be reused, grouped, retained as an alternate or replaced; disclose which instead of claiming 47 separate controls. | 47-row manifest, 17-sheet inventory, original draft provenance, six-frame walk replacement, packaged CI evidence and release validation. |
| R067 | Keep rejected v24 walk exports archived for traceability. Do not bundle unused rig-walk assets in the installed app. | 47-row manifest, 17-sheet inventory, original draft provenance, six-frame walk replacement, packaged CI evidence and release validation. |
| R068 | Include actual walk previews and native Windows UI evidence with the family ZIP. | 47-row manifest, 17-sheet inventory, original draft provenance, six-frame walk replacement, packaged CI evidence and release validation. |
| R069 | Run the complete regression suite, packaged Windows UI checks, tray check, real pointer movement check, reminders, snoozes, feeding, settings and all visible activity routes. | 47-row manifest, 17-sheet inventory, original draft provenance, six-frame walk replacement, packaged CI evidence and release validation. |
| R070 | Validate installer output, executable header, ZIP integrity and equality of the installer bytes inside and outside the ZIP. | 47-row manifest, 17-sheet inventory, original draft provenance, six-frame walk replacement, packaged CI evidence and release validation. |
| R071 | Report Windows runner checks separately from a user-device visual check. Windows Server runner results do not prove every Windows 11 monitor/DPI arrangement. | 47-row manifest, 17-sheet inventory, original draft provenance, six-frame walk replacement, packaged CI evidence and release validation. |
| R072 | Deliver one final coherent version and identify remaining limitations explicitly. Do not label unfinished artistry perfect. | 47-row manifest, 17-sheet inventory, original draft provenance, six-frame walk replacement, packaged CI evidence and release validation. |

## Concrete v25 repairs

- Water Not yet recovers after eight seconds without Pause; next water is still 30 minutes away.
- Replaced rejected limb-rig walking with six selected coherent side-view poses and synchronized cadence/personality pace.
- Grouped Grooming, Wind down and log sequence; removed redundant side-roll and inert personal-watch preview controls.
- Enabled 19 selected automatic activities, avoiding interruption of manual actions and configuration sessions.
- Compact top-right clouds, pixel-measured title wrapping, smaller proportional dialogue, inline validation/undo feedback.
- Live Follow movement, hunger click-to-feed, reminder Snooze/Done, water deferral for scheduled custom alerts.
- Full vertical jump clearance, slower edge shuffle/log stages, nearest-edge direction corrections.
- Panda Home overlay suppression and scrollable Behaviour controls.
- 64-bit tray API fixes, SQLite connection closure and UTC custom-reminder migration.

## Validation and limits

Local regression suite: 57 passing tests before final Windows build. Native Windows CI builds the real windowed executable, exercises its tray and UI and publishes screenshots/results. The exact final result is recorded in the delivery validation supplement and build manifest, rather than claiming a user laptop was tested.

The native runner is Windows Server, not the user's Windows 11 desktop. Simulated Tk font scaling checks do not prove every physical mixed-DPI or multi-monitor configuration. User-device visual review remains necessary. The six-frame walk is a reviewed replacement, not a promise of animation-studio anatomical perfection. Original draft poses remain in several activities; repeated source alternatives are not exposed as duplicate features. Meditation is HD breathing, without newly generated entry/exit animation. Peekaboo does not implement advanced real-window hiding/scoring, and fetch does not include a new dedicated continuous carrying gait. These limits are disclosed rather than treated as completed artwork.

Guide ideas for battery, tabs, Pomodoro, email, writing, file management and screen intelligence are optional future work, not missing v25 integrations. No silent app auto-updater is built; use the installer-update command or GitHub source commands in the prompt. If a requirement involves actual monitor clipping or artistic timing, inspect it on the user's device after installing and give a timestamp/pose reference for any remaining defect.
