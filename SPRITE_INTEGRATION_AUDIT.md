# Sprite integration audit: v17 versus v18

**No, the full expanded ZIP was not integrated in v17.** Existing app behaviours and newly integrated artwork are different things. Most older behaviours remained available but retained the old sprites.

| Supplied sheet | v17 use | v18 use | Still missing from this sheet |
|---|---|---|---|
| 01 water offer | All 8 frames | Retained | Jump/wave attention prelude not connected to this reveal |
| 02 walk | None | None | All new walk frames; old walk remains |
| 03 run | None | None | All new run frames; old run remains |
| 04 jump | None | None | Full articulated jump; old activity remains |
| 05 interactions | None | None | Wave, petting, cursor follow and cursor avoidance rows |
| 06 expressions | None | None | Smile/blink, ear rub, bored shuffle and sad rows |
| 07 reminders | Watch row only, 6 frames | Retained | Alternate offer, drink-water and alternate hoop rows |
| 08 activities | None | None | Kung fu, edge bamboo hang, yawn/stretch and sleep rows |
| 09 hula hoop | All 8 frames | Retained | None from this sheet |
| 10 bamboo and log | None | Eating row, 4 frames | Carry bamboo, sit on log, balance on log |
| 11 games | None | None | Peekaboo, chase ball, catch ball, victory |
| 12 manners | None | None | New bow, greeting, clap and kiss rows; separate generated bow remains |
| 13 floor poses | None | None | Sploot, side roll, belly scratch, lazy stretch |
| 14 silly play | None | None | Dance, wiggle, sneeze, hiccup |
| 15 rest and groom | None | None | Sit-down transition, wash face, wake-up, snoring |
| 16 fetch | None | None | New pickup/return artwork; existing fetch uses old artwork |
| 17 somersault | None | None | Articulated forward roll; existing rotation uses an old sprite |

Meditation is **not present in this ZIP**. v18 adds a separately generated 512 px meditation pose with gentle breathing motion. It is one detailed pose, not a new multi-frame meditation sheet. Sitting idle and bow also use separate generated artwork rather than the supplied sheets.

## What to supply or improve next

Priority: walk, run, jump, wave, kung fu, sleep/yawn, somersault and fetch. These were not upgraded using the new sheets. First try correcting the existing supplied drafts rather than regenerating all art blindly.

For each action supply separate numbered transparent PNG frames where possible, at least 512 px per frame, with the same panda identity, camera, body scale and foot baseline. Keep all ears, paws, props and curved feet inside the crop with padding. Include frame timings, loop/once/hold behaviour, action name and facing direction. Preserve actual airborne height in jump frames. Props must stay attached to the same paws. Return animations should connect naturally to idle.

A full meditation sequence would additionally need settle-in, eyes-closing, several subtle breathing frames and wake-up. The v18 detailed pose fixes the source-resolution issue but does not supply those transitions.

## v18 behaviour

Panda Home has a dedicated Behaviour page. Default rest between walks is now 30 seconds instead of 90. Cursor games are separately switchable and off by default; they respect the roaming toggle. The cursor response no longer opens chatter that stalls its motion. Sleep can be disabled while keeping roaming enabled. Rest between walks, inactivity yawn threshold, inactivity sleep threshold, automatic activity and activity interval are saved. Default is Manual only. Automatic activity is an explicitly selected Meditate or Feed bamboo routine, not a random picker. It waits while reminders, dragging, chatter, sadness or another activity is active. Feed bamboo is also available as a manual activity; it is not a hunger simulation.

Water remains every 30 minutes, unless paused or snoozed. Personal reminders use saved due dates. Movement follows its enabled interval. Cursor reactions and walking destinations retain their existing logic.

## UI and verification

v18 replaces the cramped scalloped bubble with a wider, softer cloud. Water controls have larger spacing. Custom reminder titles are separated from the subtitle and use measured wrapping. All automatic reminder/chatter content remains on the pet canvas. Panda Home is still a manually opened settings/history window.

Automated checks cover snooze without logging, final water pose hold, on-canvas dialogue, asset presence, activity scheduling priority and settings validation. Windows build validation is separate from real desktop appearance testing. Different DPI settings, multi-monitor edge placement and end-user visual quality still require Windows runtime verification.
