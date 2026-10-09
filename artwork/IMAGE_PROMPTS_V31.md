# v31 asset-generation instructions

Built-in image_gen was used, with transparent_background=true. Raster assets are extracted and packaged by tools/prepare_walk31.py and tools/prepare_themes31.py; no cutout limb rig is used.

## Walk first half
Reference: established cream/charcoal baby-panda face/body. Four right-facing side-profile poses in a single-row transparent atlas: near-arm back-left / near-leg front-right heel contact; near leg takes weight with far foot lifting back-left; near foot under hip with far knee passing. Same full-body scale, ground baseline, camera, fur and face. Same-side arms and legs move in opposite directions. The fourth generated candidate is excluded from actual playback because its near-leg occlusion remains ambiguous.

## Walk opposite half
Four right-facing side-profile poses in a single row. Near arm forward-right, near foreground thigh and foot back-left. Far leg front-right is behind the near thigh and partly occluded by belly. Far heel contacts front-right while near toes are back-left; far leg takes weight while near foot lifts; far foot under hip while near knee passes. Two naturally attached arms and legs, soft weighty animated-film rendering, same character identity, no cropping, text, floor or props. The fourth source candidate is excluded from playback.

## Seasonal prop atlas
4x4 equal-cell true-transparent atlas, no pandas, text or religious figures. Row-major: pumpkin/leaves; friendly jack-o-lantern with witch hat; clay/copper diya and marigolds; three Holi powder bowls; dandiya/marigolds; harvest cornucopia; Christmas present/pine; gold star/confetti; pink heart gift/rose; pastel one-candle cake; modak plate/marigolds; flute/peacock feather; damru/bel leaf/crescent; spring blossoms; sunflower; snowflake/pinecone. Rounded high-quality 3D materials consistent with the panda, complete isolated groups and generous margins. Remove gradient/background alpha completely while preserving opaque objects and exact cell layout.

## User-selected sheet correction
Exact edit source: upload/image-edit-target-04f63839cfb831b8.png. In the top-right fourth cell, keep near hand forward-right but put the visible near thigh/foot back-left and the partly occluded far leg front-right. Preserve all seven other cells, ground, size, 4x2 layout, face and fur. The opposite-half first pose is the supporting anatomy reference. Do not substitute a different sheet as the edit target.
