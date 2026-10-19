# Appearance review, based on v37

Base commit: a5acb6424dd8d79796a1563e948fb96485a281c1.

This is an appearance change for review, not a packaged Windows release.

## Changes

- Replace the four independently enlarged upright sprite rows with one sequence-level fitting rule. Keep uniform aspect ratio, a shared floor, and a consistent front/profile head scale. Wide props and acrobatic poses retain safe canvas margins.
- Fit from the original texture resolution. Keep one scale for each animation sequence and exact mirrored left/right gait frames.
- Pass transformed head and torso landmarks to the wardrobe renderer, rather than applying coordinates from unscaled artwork.
- Fit seated and walking garments to the anatomical torso instead of small disconnected cream patches. Keep paws, paw pads, food and glasses in front of clothing.
- Use the profile garment surface for resting bodies. Place resting scarves at the neck and tilt headgear with the sleeping head.
- Remove the profile ghost's sharp neck kink. Use a gravity-aligned hood/blanket for sleep rather than rotate and stretch the standing hem. Close the unused original face hole before restoring the actual resting face.

## Review and validation

`python -m unittest discover -s tests -q`

`python tools/review_appearance.py /absolute/output/directory`

For preview regeneration without the full render audit, append `--preview-only`.

The preview invokes the application's actual `_load_images` and `Wardrobe.dress` paths. It does not use a separate drawing approximation.

Tests cover shared head scale and ground position, source-frame canvas margins, exact mirrored gait, preservation of seated paw colours, resting scarf placement and the sleeping ghost's transparent background.

These checks establish offline rendering and logic behaviour. This change has not been built into a new Windows installer or launched on Windows. The wider snoring pose and acrobatic sequences remain bounded by the available artwork; no character anatomy has been repainted.
