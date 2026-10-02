# v19 complete sprite collection integration

**All 17 supplied sheets are now integrated: 240 source poses, 47 mapped sequences, plus 16 mirrored walk/run frames.** The 47 sequences include two alternate reminder variants, so the pack describes 45 distinct action groups. Every sequence is available in the scrollable Panda Activities page and in the automatic-activity selector. No supplied sheet remains unused.

## Connected behaviour

Normal roaming and cursor escape use the new eight-frame walk/run sequences, mirrored for leftward travel. Idle/sad expressions, petting, bowing after intake, inactivity yawning and sleep, kung fu, dance, floor poses and somersaults use the supplied sequences. Meditation remains the separate detailed pose because it is not in this pack.

Water now plays a jump/wave prelude, reveals the glass using all eight offer frames, then holds its final pose until answered. Movement uses the hoop sequence; personal reminders use the watch sequence. Amount controls, declining water, history and ten-minute snooze remain. The alternate offer, drink-water and alternate hoop rows are also selectable activities.

Bamboo feeding uses the eating row. Hanging is routed to a screen edge before playback. Log sitting/balancing use the new prop-bearing frames with deliberately slow timing. Fetch retains the existing placement/navigation engine and now uses supplied ball/pickup/return artwork. Peekaboo, chase, catch, victory, greetings, clapping, kisses, side rolls, belly scratches, wiggles, grooming, hiccups, waking and snoring are all available as activities.

The existing behaviour settings remain: 30-second default walking rest, optional cursor games, inactivity thresholds, sleep toggle, chosen automatic activity and its interval. Manual only is the default. Reminders, sadness, dragging and active actions take priority over scheduled activities. Manual edge activities can approach the edge even with autonomous roaming disabled.

## What was prepared

All source grids were inspected. Fractional grid boundaries are retained in assets/sprite_collection_manifest.json. Crops remove small neighbouring-frame fragments while keeping sizable detached props such as ground balls. Per-action shared scale and face-size estimation reduce character-size changes. Grounding uses a shared baseline and preserves pose proportions; jump playback supplies an airborne arc. Transparent padding surrounds each frame. One switched-paw wave frame and the corresponding greeting frame are mirrored for consistency. All 47 animations have desktop-size GIF previews in the project ZIP. The manifest records modes, timing, crops and corrections.

The preparation tool is tools/integrate_sprite_collection.py. Regeneration needs Pillow, NumPy and SciPy; these are preparation dependencies, not new app runtime dependencies. Idle expression playback has longer neutral holds and short blink frames.

## What genuinely remains pending

- **Real Windows visual acceptance:** actual desktop playback, scaling/DPI, screen-edge dragging and multi-monitor placement have not been executed in this workspace. Packaging success is not proof of those checks.
- **Source-art continuity:** all poses are integrated, but generated art still changes facial angle, limb length and some props between poses. Individual sequences may need targeted replacement after playback review. Integration does not mean every draft became a production-quality animation.
- **Advanced hide-and-seek gameplay:** the supplied sequence is peekaboo. Hiding behind an actual window, discovery rules and scoring are not implemented by those four poses.
- **Fetch polish:** placement and returning exist, but the supplied artwork is pickup/offer rather than a full continuous carrying run. Catch/chase gallery activities do not add a physics-based ball game. A carrying gait and consistent ball-only sprite would improve this.
- **Meditation transitions:** the detailed meditation pose is separate. Settle-in, breathing variants and waking transitions need a new sheet if desired.
- **Compact reminder titles:** long custom titles are shortened in the cloud; the full title stays in Panda Home.

## Validation

Automated validation accounts for every sheet and all 240 source poses, checks decoded PNGs and transparent margins, distinguishes once-and-hold from loop playback, routes every sequence to the renderer, checks hanging goes to an edge, preserves water snooze/history semantics and checks reminder priority. All 47 GIF previews were decoded. These are asset and behaviour checks, not live Windows visual or gameplay acceptance.
