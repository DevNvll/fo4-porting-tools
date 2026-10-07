# Glossary

Each special word of the documents, with one or two lines. The documents use one word for
one thing.

| Word | Meaning |
| --- | --- |
| additive clip | A clip that has offsets only. The game adds them to a pose. In a file of `d2x` its name ends with `_add`. Only its motion against its own first frame is data. |
| aim point | The point of the sight that must be on the view axis in the sights. `point` of `[sight]` in a set file, in Fallout 4 weapon space. |
| area | A part of the repository with its own tools and its own `port.toml`: `fnv/`, `destiny/extract/`, `destiny/port/`, `marathon/extract/`, `marathon/port/`. |
| arm entity | In Marathon: the entity with the first-person rig of the arms, its clips and its animation graph (`fp_rifle_arms`). |
| automatic clip | A clip of `[auto]`: one shot of the source that starts again at each event `weaponFire` of the vanilla automatic clip. |
| bake | The step that evaluates each source clip on the bones of the source and writes the matrix of each bone for each frame. |
| baseline | The stored results that a regress command compares new results with. For `destiny regress`: the clip folders that `destiny/port/regress.toml` names. |
| behavior source | The file `behavior/WEAPON/WEAPON.bhv` of an esx project. It gives a weapon its own animation keyword, its graph copies and its reload rules. |
| body entity | The entity of Destiny 2 with the third-person clips of the player: 72 bones, one graph. |
| clip | One animation. A clip of a source file has a name such as `fp_001_80BC8660`. A Fallout 4 clip has a name such as `WPNReload` and is one HKX file. |
| collision step | The step of the hand solver that moves a finger out of a gun part, to a floor distance, 1.15 units at most for each joint. |
| composed clip | A clip of `[compose]`: clips of the file, one after the other, with a blend at each join. |
| connect point | A named point of a Fallout 4 mesh where a part attaches: `P-Scope` on the gun, `C-Scope` on the sight. |
| content group | The tag of one gun in the tag tree of Destiny 2. It can be the weapon tag. |
| conversion file | `conversion.toml`: the file of a New Vegas conversion that replaces values that the tools assume (the name, the template, the output folder, a clip). The command needs none. |
| counted reload | One reload clip for each count of rounds in the gun, selected by a line `when ammo == N play CLIP` of a behavior source. |
| d2fo4 | The converter of `destiny/port/` (`d2fo4.py`, `./port destiny convert`). |
| d2x | The extraction tool of Destiny 2 (`destiny/extract/`). |
| data folder | `data/`: each file of a game, each result, each built mod and the local settings. Git ignores it. |
| dye | One of the three color sets of a gun of Destiny 2 (Weapon1, Weapon2, Weapon3). Each has a primary and a secondary material. |
| effect material | A Fallout 4 material with no scene light and with alpha blending (BGEM). The glass and the reticle use it. |
| esx | The program that builds a Fallout 4 mod from a project folder and that starts the game probe. It is not a part of this repository. |
| eye point | The place of the camera in weapon space in a clip in the sights. |
| first-person file | The `.glb` file of an extraction with the rig, the gun, the hands and each clip. The input of the converter. |
| fixture | A folder `data/fnv/fixtures/NAME`: the extracted New Vegas mod of a ported weapon, which `fnv regress` converts again. |
| full-pose clip | A clip with a pose for each bone. Not an additive clip. |
| gate | What must be true before the next step of a procedure starts. |
| glass | The transparent part of a sight, with its graphics. Render stage 7 of Destiny 2. |
| grip code | The start of the name of a New Vegas animation that names the grip (`1hp`, `2ha`). It is not a part of the animation name. |
| grip point | The middle of the first joints of the index and the middle finger of the right hand in the hold pose. It goes on the grip point of the template. |
| gstack | The third texture of a texture set of Destiny 2. Its green value is the smoothness, and its alpha value is the dye mask and the metal value. |
| gun entity | The entity of the gun in Destiny 2. It has its own graph, which gives the clip of the gun parts for a state. |
| hold pose | `hold = "CLIP:FRAME"`: the pose in which the hands hold the gun. It gives the place of the gun in Fallout 4 weapon space, and it is the pose `ready`. |
| idle camera | The camera of Fallout 4 that turns about the player when the game has no input for about 2 minutes. |
| kind | The role of a weapon bone (`bolt`, `magazine`). The template gives each kind a Fallout 4 bone. Key `[roles]`. |
| lock file | A file that esx keeps: `ids.lock` (the object ID of each record) and `behavior/WEAPON/WEAPON.lock` (the hashes of the vanilla graphs). In git, so that a build gives the same IDs. |
| m2x | The extraction tool of Marathon (`marathon/extract/`). It uses the modules of `d2x`. |
| manifest | `manifest.json` of an extraction: the files, the bones, the clips with their frame counts and node counts. |
| mod project | The esx project of a mod. Its hand-written files are `mods/NAME/` (in git), and the complete project is `data/mods/NAME/`. |
| node count | The count of tracks of a clip. When it is not the bone count of the rig, the clip can be a clip of a different rig. |
| NVCS | The New Vegas compatibility skeleton mod. Its first-person skeleton file gives the New Vegas skeleton of the rig folder. |
| op | One command to the game probe, such as `item.give`. |
| parts file | `parts.json` of a work folder: each shape of the gun in the space of its Fallout 4 weapon bone. A Fallout 4 model of the gun must have its shapes at these places. |
| pattern entity | The entity of Destiny 2 whose rows give a gun its tags and its rig entity. |
| piece | (1) One clip of the file inside a composed clip. `[piece_events]` gives its events. (2) One part of a Marathon weapon that is an entity with a model: the body, the magazine, the muzzle device, the sight unit. |
| plan | A TOML file with the steps of a game test for `esx probe run` (`mods/NAME/tests/*.toml`). |
| pose clip | An additive clip of 2 or 3 frames with one pose, which no state names. For some guns it puts the left hand on the gun. |
| posed folder | `extract/NAME/posed/`: the tracks of each clip with the offsets of the pose clip, from `./port destiny pose`. `[hand_pose]` names it. |
| probe | The part of esx that starts a test copy of the game with no window and takes ops. It has one session at a time for the computer. |
| receiver part | The part of a Fallout 4 weapon that has the whole gun in these mods. A second receiver part is a shader of Destiny 2. |
| regress | The command of an area that makes each ported weapon again and compares the bytes with the stored results. |
| release | `data/mods/NAME/build/release/`: the plugin and the two archives of a mod. |
| render stage | A draw pass of Destiny 2: 0 opaque, 7 transparent, 16 reticle. |
| retarget | The step that moves each pose of the source rig to the Fallout 4 skeleton. It runs in Blender. |
| reticle | The mark that the player aims with. In Destiny 2 it is a quad that a vertex shader puts before the camera. |
| rig entity | The entity of Destiny 2 with one first-person rig and its clips. |
| rig folder | A folder with files of Fallout 4 that the tools need: `data/fnv/rig` (the first-person skeleton, the vanilla clips of each template, the New Vegas skeleton) and `data/destiny/port/rig` (the vanilla clips of each template, the third-person skeleton). The `make-rig` commands make them. |
| rules file | `clips.json` of a work folder: the rules `[gun]` and `[compose]` of a set file, which the converter gives to the bake and to the checks. |
| session | One run of the game by the probe, with an ID such as `s-20261006-030507-fb32`. |
| set file | `sets/NAME.toml`: the clip of the file for each Fallout 4 clip, the rules of the weapon and the data of its model. The input of `./port destiny convert`. |
| setting | A local value: a program or a folder of the computer (`blender`, `esx`, `fo4_data`). It comes from an environment variable, then from `data/config.toml`. |
| shader | In Destiny 2: an item that gives a gun three other dyes. Also the program of a material (pixel shader, vertex shader). |
| sighted pose | `sighted = "CLIP:FRAME"`: the pose in the sights. |
| slot | One of six dye places of a mesh part of Destiny 2. In Marathon: a place of a weapon for a piece (`barrel`, `sight`, `magazine`). In Fallout 4: an attach point of a weapon (`ap_gun_Scope`). |
| stance | In the body graph of Destiny 2: `stand` or `crouch`. In the third-person retarget: the first frame of the vanilla reload. |
| state | A node of the animation graph of Destiny 2 or Marathon with a name hash, such as `idle` or `reload_1`. A tree of conditions gives its clip. |
| states file | `states.json`: the clip of each game state of a weapon. `./port destiny states` writes it. `./port marathon extract` writes it beside the `.glb` file. |
| static clip | A clip of `[static]`: one weapon place of a vanilla clip on each frame. |
| synth clip | A clip of `[synth]`: the weapon motion of a vanilla clip on a pose of the source, with the arms, the hands and the gun as one body. |
| tag | An entry of a game package, with a 32-bit hash such as `80BC8633`. Marathon also names entities, clips and textures with 64-bit hashes (the table `tag64.tsv`). |
| template | A vanilla weapon as a file (`templates/NAME.toml`): the weapon bones with their rest places, the sound names, the pose of the body, the grip point. |
| test cell | `QASmoke`, the cell of the game tests of the chats. |
| test world | A plugin with one cell that the user installs into the test folder of the probe (`esx probe install --world FILE`). `./port destiny game session NAME LABEL --world` starts the game there. |
| trace | The list of clips and events that the game started, from the op `anim.trace`. 120 ticks for each second. |
| unit | The length unit of Fallout 4. 1 m is 69.99125 units, and 1 unit is 1.43 cm. |
| vanilla | Of the game Fallout 4 with no mod. |
| variant | In Marathon: an item with no entity of its own. It uses the entity of its base item (`--art`). |
| weapon bone | A Fallout 4 bone for a gun part: `Weapon`, `WeaponMagazine`, `WeaponBolt`, `WeaponExtra1` and others. The skeleton has 13. |
| weapon tag | The tag by which the graph of Destiny 2 selects the clips of a gun: its content group, or the tag of its class. |
| `WeaponIKTargetL` | The bone on which Fallout 4 puts the left hand with IK in third person. |
| work folder | The folder with the work files of one conversion: `data/fnv/work/NAME` or `data/destiny/port/work/NAME`. |
| `WPNAssemblyPose` | The third-person clip with one pose that gives the place of the left hand on the gun for each clip of the grip. |
