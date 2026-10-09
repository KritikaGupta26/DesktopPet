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
