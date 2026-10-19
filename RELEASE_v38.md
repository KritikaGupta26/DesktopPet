# Water Panda v38 integrated update

## Included

- Preserve the original cute character and all 240 original pack frames. The rejected adult redesign is not in this project.
- Include the preceding shared head scale, floor alignment, costume layering and ghost canvas corrections.
- Add 16 matching poses, explicit foreground prop masks, and 10 complete performance timelines with setup and recovery.
- Respect activity checkboxes in Organic mode. Extend the previous complete-default pool once; preserve later choices. Keep prank cooldowns and pending hunger requests.
- Give sideways tumble its own art instead of redirecting it to the somersault.
- Increase active redraws from 80 ms to 40 ms. Retain subpixel positions and normalize legacy offsets, particles and gravity.
- Keep water logging, ten-minute snooze, brief decline response, watch reminders, hula hoop, nighttime corner rest, themes and effects. Reminder dispatch cancels a performance in progress.

## Verification

- Offline regression suite: 155 tests passed. A focused character/costume rerun covers the final staff-fit adjustment.
- Runtime render sweep: 1,292 variants checked, zero canvas-edge clipping failures.
- All 648 pre-existing PNG assets were compared byte-for-byte against the appearance-review baseline; none changed.
- `artwork/v38/review/render_report.json` records the actual clipping sweep.
- The Windows workflow runs regression tests, builds the EXE, exercises the packaged UI (including the new performances), and creates an installer only if those checks succeed.

## Limits

This remains a keyframe sprite application, not a fully rigged 3D model. Sixteen new poses do not constitute newly painted inbetween frames for every existing activity. The 40 ms setting is a redraw interval, not proof of a sustained frame rate on every PC. The existing Tk colour-key renderer still has hard alpha at the outer silhouette.

The long Po-inspired idea catalogue is a design backlog. It is not a claim that every proposed prop, expression and themed story has been drawn and shipped.

Windows build and launch evidence must be read from the actual build run for this commit. Offline renders alone cannot certify an installer.
