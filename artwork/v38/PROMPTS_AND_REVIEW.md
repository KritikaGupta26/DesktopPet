# Character extension art

Reference: `assets/pack_happy_idle_0.png`, the existing cute character.

Generated with the built-in image tool. The requested identity was unchanged: large warm brown eyes, oversized round head, cream tuft, tiny snout, short black limbs and small body. The adult panda redesign was rejected and is excluded.

The new transparent 4×4 sheet adds noodles (two poses), dumpling balance/catch, belly rub, drawing/showing a scroll, sneaking, staff ready/turn, butterfly curiosity (two poses), shadow inspection, startle, heroic landing and bashful recovery.

`tools/integrate_character_extensions.py` extracts complete connected silhouettes, removes stray alpha fragments, retains detached props, pads each frame, and creates reviewed foreground masks. Existing pack frames are preserved.

`tools/review_character38.py` loads the actual application sprites and costume fitter, renders review boards and keyframe GIFs, and checks costume bounds. The GIF shows the supplied keyframes; it does not demonstrate newly drawn inbetween frames for every action.
