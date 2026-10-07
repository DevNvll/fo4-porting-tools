# Marathon: the extraction of a weapon and of its first-person rig

This folder has `m2x`: the tools of `d2x` (`destiny/extract/`, made for Destiny 2, build of
2020) on the packages of Marathon (the Tiger engine, a later version). The weapon of the first
work is the **M77 Omnipositor**. Its result is in `data/marathon/extract/out/m77_omnipositor/`,
and pictures and one video are in `data/marathon/extract/validation/`. The first-person file
of the result is the input of the Fallout 4 port (`../README.md`;
`../port/sets/m77_omnipositor.toml`; `../../destiny/port/README.md`, "The M77 of Marathon";
`../../mods/M77/`).

No file of `d2x` and no file of the game is changed. The programs here use the modules of
`d2x` as a library, and they only read the game folder.

## Result

| Item | Result |
| --- | --- |
| Packages | 629 package files open, 1,032,829 entries. |
| Item | `M77 Omnipositor`, item hash `DF4263CA`, found by its name in the string tables. |
| Models | 5 pieces: the body (2,468 triangles), the magazine (2,739), a second magazine for the reload, the muzzle device (5,448; the slot `barrel`) and the sight unit (14,173: a rear sight with a box, and a front sight). |
| Places of the pieces | 4 pieces have their place on the weapon, from the named points of the gun entity. The second magazine has none. |
| Textures | 13 textures of 7 materials, as PNG files, and each material as a texture set of Destiny 2 (albedo, normal, gstack). |
| Skeleton of the weapon | 10 bones: `b_handle`, `b_magazine`, `b_bolt`, `b_bullet_1`, `b_bullet_2`, `b_casing`, `b_mag_release`, `b_safety`, `b_trigger`, `b_bolt_handle`. |
| Clips of the weapon | 15 clips of the animation set of the weapon, each decoded with no error. 10 are for this skeleton. The reload has 105 frames. |
| First-person rig | The arm entity `fp_rifle_arms`: 91 bones (the body of the player, with the 10 bones of the weapon on the grip bone of the right hand). It is the rig of Destiny 2: the same bone names and bone axes. |
| First-person clips | The animation graph of the arm entity has 93 states. 85 have a clip for this weapon (the tag `rifle`): 97 clips, each decoded with no error. 68 are for this rig and are in the file. |
| Files | `m77_omnipositor_weapon.glb` (4 pieces on the skeleton, 10 animations), `m77_omnipositor_first_person.glb` (the rig, the 4 pieces, 78 animations), one `.glb` for each piece, `textures/`, `manifest.json`, `states.json`, `raw/`. 160 files, 37.6 MB. |

In `data/marathon/extract/validation/`: `m77_weapon_all_pieces.jpg` shows the weapon file,
`m77_pieces.jpg` shows four pieces alone, `m77_first_person_clips.jpg` has frames of five
first-person clips, and `m77_reload_1.mp4` is the reload clip of the weapon (3.5 s; made
before the muzzle device and the sight unit had their place).

## How to run it

`./port doctor` shows what is there and what is missing. The settings are in
`data/config.toml` (`config.example.toml` has each one): `marathon_game` is the game folder
(it has `packages/` and `bin/x64/`), and `blender` is Blender 4.5.

```sh
./port destiny setup          # the environment of d2x: the clones, the package reader, the Python environment
./port marathon setup         # the Oodle 9 shim, the link to the Oodle library of the game, tag64, the table of the 64-bit tag hashes

./port marathon find "M77"
./port marathon extract "M77 Omnipositor" --art "M77 Assault Rifle" \
    --hands data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
./port marathon render data/marathon/extract/out/m77_omnipositor/m77_omnipositor_weapon.glb \
    data/marathon/extract/work/m77.png --views side,quarter
./port marathon regress       # the extraction again in a scratch folder, and the comparison of the bytes
./port marathon notes dxil 80A60033          # the pixel shader of a material, as text
./port marathon tag64         # after an update of the game: the table of the 64-bit tag hashes again
```

`./port marathon` lists each command. The extraction needs 13 to 17 seconds.

* `--art ITEM`: an item with no row in the art table of the game (a variant of another
  weapon) uses the entity of the item ITEM. `find` prints `no entity of its own` for such an item.
* `--hands FILE.glb` puts the hand mesh of a first-person file of Destiny 2 (a result of
  `./port destiny extract`) on the rig: it is not a mesh of Marathon, and it is there for
  pictures only. The stored result of the M77 was made with it.
* `--arms NUMBER` selects another arm entity of the weapon (the manifest has the list).
* `--out OUT`: the files go into `OUT/NAME/`. Default: `data/marathon/extract/out`.
* `MARATHON_PACKAGES` names another packages folder than `packages` of the game folder.

Each program runs with no `./port`. A program that reads the packages needs the Python of the
environment of `d2x`; it finds `portkit` and `d2x` by itself. From the root of the repository:

```sh
bash marathon/extract/setup.sh [--table] [--force]
PY=data/destiny/extract/venv/bin/python
PYTHONPATH=destiny/extract $PY marathon/extract/m2x_extract.py --find "M77"
PYTHONPATH=destiny/extract $PY marathon/extract/m2x_extract.py "M77 Omnipositor" --art "M77 Assault Rifle"
PYTHONPATH=destiny/extract $PY marathon/extract/regress.py
PYTHONPATH=destiny/extract $PY marathon/extract/notes/describe.py 80A7C262
python3 marathon/extract/tools/render_glb.py FILE.glb OUT.png      # it starts Blender
```

### What the setup makes

`setup.sh` writes below `data/marathon/extract/` only. It is safe to run again: a step that is
complete is skipped. When a thing is missing (a C compiler, cargo, the game folder, a part of
`d2x`), the other steps run, the end of the output names each missing thing with what to do,
and the exit code is 1.

| File | How |
| --- | --- |
| `runtime/liboodle-data-shared.so` | `cc -O2 -fPIC -shared -o ... oodle9/oodle9.c -lpthread` (`CC` names another compiler). Linux on x86-64 only. |
| `runtime/oo2core_9_win64.dll` | A link to `bin/x64/oo2core_9_win64.dll` of the game folder. The library is a file of the game: it is not in this repository. |
| `runtime/tag64`, `target/` | `cargo build --release --locked` of `tag64/`, with the clone of `tiger-pkg` that the setup of `d2x` made (`data/destiny/extract/vendor/tiger-pkg`). You can delete `target/` after the build. |
| `notes/tag64.tsv` | `runtime/tag64 PACKAGES goliath`, with the lines sorted. `--table` makes it again. |

The last step of the setup opens the packages and reads 50 entries. This needs the shim and
the library of the game, so it proves the runtime folder.

From `d2x`, `m2x` uses the Python environment, the package reader
(`data/destiny/extract/target/release/libtigerpkg_ffi.so`) and the two clones
(`data/destiny/extract/vendor/`). It does not use the runtime folder of `d2x` (the Oodle 3
shim): `m2x` gives the package reader its own runtime folder.

`tiger-pkg` keeps a cache of the package list in the cache folder of the user (the folder
`tiger-pkg` below `XDG_CACHE_HOME`, about 20 MB for Marathon). It is not below `data/`.

## What was necessary

"The same tools with minimal changes" is true for the package reader, the animation decoder,
the glTF writer, and the form of the data. Each class number and each offset is new.

| Part | State | What was necessary |
| --- | --- | --- |
| Package reader (`tiger-pkg`) | Works with no change | The version code `goliath`. |
| Oodle | New file | Marathon has Oodle 9, and only the Windows library. The Linux shim of `tiger-pkg` is for Oodle 3: it stopped with a segmentation fault, because the start code of the new library reads the thread block of Windows. `oodle9/oodle9.c` (208 lines) loads the library: it maps the sections, applies the relocations, gives each of the 41 imports a small function and sets the register GS for each call. |
| 64-bit tag hashes | New program | Marathon names entities, clips and textures with 64-bit hashes. The Python wrapper of `d2x` does not have them. `tag64/` (23 lines of Rust on `tiger-pkg`) prints the table: 43,853 hashes. |
| Animation decoder (`tiger-animation-parser`) | Works with 3 corrections at run time | The decoder has a version `marathon`, for an earlier build. In this build the skeleton block and the rig block start 16 bytes earlier, and a row of the rig relations has 72 bytes (52 in Destiny 2). `m2x.patch_parser()` corrects the three values in the process; the files of the decoder are not changed. |
| glTF writer (`d2x.export.build_glb`, `d2x.gltf`) | Works with no change | |
| Layouts of the data (`d2x.investment`, `entity`, `model`, `texture`, `strings`, `graph`) | New: `m2x.py` (799 lines) | Each class number is different from Destiny 2, and no public tool has the classes of Marathon. I found each one in the data. The structures are near those of Destiny 2 after Beyond Light, with other offsets. The animation graph has the layout of Destiny 2 with a larger node. |
| Shaders | New note program | A shader of Marathon is DXIL (LLVM bitcode), not the bytecode of Direct3D 11. `notes/dxil.py` makes it readable for `llvm-dis`. |
| The tools of `destiny/port/` (Destiny 2 to Fallout 4) | Work with two new options | The first-person file has the form of a file of Destiny 2. The hand of Marathon has other bone lengths: the set file of the M77 has `knuckles = "align"` and `closed_fingers = true` (`../../destiny/port/README.md`). |

## The layouts that the tools read

Each number is from an analysis of this build of the game (the programs of `notes/` print the
data that the analysis used). A table is found by its class, not by its tag.

| Thing | Class | Layout |
| --- | --- | --- |
| String container | `8080B9B8` | Hashes at 0x08, the tag of the English text at 0x18. |
| String data | `8080B9BA` | Parts at 0x08 (0x20 bytes), strings at 0x38. The text is plain UTF-8. |
| Display map, item map | `80806EF0`, `80809685` | Rows of 0x20 bytes: item hash at 0x00, tag at 0x10. 2,685 items; 2,543 have a name. |
| Display definition | `80806EF6` | String container index at 0xBC, name hash at 0xC0. |
| String container index | `808071C8` | Rows of 0x18 bytes: a 64-bit hash at 0x10. |
| Art table | `80806CAC` | Rows of 0x48 bytes: item hash at 0x00, entity assignment hash at 0x08. 2,122 rows. |
| Entity assignments | `8080B61C` | Rows of 0x18 bytes: hash at 0x00, the 64-bit hash of the entity at 0x10. |
| Entity | `8080BAAD` | Components at 0x08, rows of 12 bytes. |
| Component | `8080BADB` | Pointers at 0x10 and 0x18; the class of a block is 4 bytes before it. Skeleton `80809FB6`/`80809FB7`, rig `8080AD85`/`8080AD7E`, model `80808673`/`80808678`, weapon parts `80804603`/`80804A14`, named points `80809F75`/`80809F76`, animation `80803951`/`80803936`. |
| Model | `8080881C` | Meshes at 0x10 (0x80 bytes), scale at 0xA0, translation at 0xB0, texture coordinate scale and translation at 0xC0. A mesh has two vertex buffers, an index buffer, parts of 0x28 bytes and 26 part offsets for 25 render stages. A vertex has 24 bytes (position, normal, tangent, 16 bits each) and 4 bytes (texture coordinates). The fourth position value is the bone index. |
| Material | `808031D8` | Vertex shader at 0x58, pixel shader at 0x278, textures in rows of 0x18 bytes of the class `808086C6` (slot, 64-bit hash). The constants of the pixel shader are the last table of vectors (class `80800090`). |
| Texture header | type 32/1 | Data size at 0x00, DXGI format at 0x04, width, height, depth and array size at 0x22, the tag of the large data at 0x3C. |
| Animation set | `80803BE9` | The clips at 0x08 (rows of 0x10 bytes, a 64-bit hash at 0x08). The entries at 0x58 (rows of 0x30 bytes of the class `8080ADFF`: name hash at 0x10, clip hash at 0x20, clip index at 0x28). |
| Clip | `8080AE01` | Read by the animation decoder. |
| Named points | `80809F82` | Rows of 0x30 bytes: rotation (x, y, z, w), translation and scale, bone index at 0x24, name hash at 0x28. |
| Animation graph | `80803950` | Name table at 0x08 (state name hash, state index), states at 0x18 (kind, pointer). Kind 1: a list of (set entry, threshold). Kind 2: a tree, with the lists at 0x00, the dimensions at 0x10, the nodes at 0x20 (0x24 bytes: a tag mask of 24 bytes, value hash, child, next, link) and the groups at 0x30. |
| Tag trees | `8080ACBF` | One tree for each dimension at 0x08 (rows of 0x20 bytes, with the tags: hash, parent). The tree of each dimension number at 0x18 (16 bits each). The dimension 3 is the weapon. |
| Arm entities of a weapon | `808025AA` | A list of 64-bit entity hashes, with the source name of each one. |

Names are FNV-1 hashes, as in Destiny 2. The state names of the graph are the words of
Destiny 2 (`idle`, `fire`, `iron_sight_idle`, `ready`, `put_away`, `reload_empty`, ...). A
word list gave the bones of the weapon and of the sight unit, the 10 control names of the
rig, the slots (`barrel`, `sight`, `magazine`, `foregrip`, `chip`, `charm`, `sticker`), the
weapon tags (`rifle`, `pistol`, `shotgun`, `smg`, `sniper_rifle`, `railgun`, `dmr`, `lmg`,
`hmg`, `ar`, `magnum`, `knife`, `unarmed`, `grenade`), and `empty`, `partial`, `full`,
`stand`, `crouch`, `attachment`, `grip`, `reload_1`. 27 of the 28 point names of the
weapon, 9 bones of the arm rig and most condition values have no word.

## How the item gives the files

1. The name gives the item hash `DF4263CA` (display map, display definition, string container).
2. The art table has no row for this item. `M77 Omnipositor` is a variant of `M77 Assault
   Rifle` (its description says "Modified M77 Assault Rifle"), and that item (`6F95AD10`) has
   the row: assignment hash `B3C9A7B2`, entity `80A7C262`. `--art` gives the item with the row.
3. The entity has the skeleton, the rig, an animation set (`80A7ADB9`, 15 clips), a component
   with 8 slots, and 28 named points. Three slots have a default piece: `barrel`, `magazine`
   and `sight`. A fourth piece, the body, has no slot.
4. Each piece is an entity with a model. A piece names one point of the weapon, and its own
   point `attachment` goes there. The point of the muzzle device is on `b_handle`, at the
   front of the body (x 0.4317 m, z 0.1031 m). The point of the sight unit is on top of the
   body (x 0.0211 m, z 0.1441 m). The point of the magazine is on the bone `b_magazine`, with
   a rotation, so the magazine moves with that bone.
5. The slots component names a list of 9 arm entities (one with no body name, and one for
   each body of the player). An arm entity has the skeleton and the rig of the first-person
   body, an animation set (517 clips, 304 entries), an animation graph and the tag trees.
6. The slots component of the weapon has the tag pair `rifle` / `rifle`. For each state of
   the graph, the tree gives the set entries for that tag; an entry gives a clip.

## The first-person file

`m77_omnipositor_first_person.glb` has the form of a first-person file of `d2x`: one skin
(91 bones), the pieces as meshes `regionNN_ENTITY` on the weapon bones, the camera at
`b_utility`, and one animation for each clip. `manifest.json` has the list `first_person` and
`states.json` has the clip of each state, in the form of `destiny/port/tools/d2states.py`.

* `fp_NNN_TAG`: a clip of the arms (NNN is its place in the animation set). 68 clips.
* `weapon_NNN_TAG`: a clip of the gun entity on the same skeleton: the body bones at rest,
  the gun parts as in the clip. 10 clips. A clip of the arms does not move the gun parts in
  a reload; the weapon has that motion, and the game plays the two at the same time. The
  rest places of the gun bones are the same in the two skeletons (difference 0.000000).

The states of the M77 that the port uses: `idle` (97 frames), `iron_sight_idle` (97, one
pose), `fire` (three clips of 15 frames, with the thresholds 0.333, 0.667 and 1.0),
`iron_sight_fire` (14), `ready` (22), `put_away` (12), `reload_empty` / `reload_full`
(104 frames for the value `empty`, 72 frames for `partial`), `sprint_loop` (one pose).

## The materials

The pixel shaders say how a material uses its textures (`notes/dxil.py` prints one). The
render targets are those of Destiny 2: the color, the normal (its length has the smoothness),
and the metal value with the occlusion. `m2x.material_plates` writes each material as a
texture set of Destiny 2 (`textures/MATERIAL_albedo.png`, `_normal.png`, `_gstack.png`), so
the tools of `destiny/port/` read it with no change. The manifest has the rule of each material.

| Rule | Materials of the M77 | Content |
| --- | --- | --- |
| `palette` | The body, the two rounds in the magazine, parts of the sight unit | One texture: an atlas of flat colors (the three materials have the same atlas). The texture coordinates of a part point at a color. The smoothness is one value of the constants (0.3; 0.44 for the rounds). No normal map, no metal. |
| `detail` | The muzzle device, the magazine, the sight unit | 6 textures. Color = texture 0 (gray, with the prints) x the color of a region x a detail value. Texture 3 has the regions (red, green, blue) and the smoothness (alpha). The alpha of texture 0 is the occlusion. The metal value is texture 2, which is black here. |
| `constant` | One part of the rear sight | No texture: the color (5, 0, 0) of the constants, a red light. The file has a red surface. |

**The colors of the regions are not in the files.** A `detail` material has seven regions.
The file has the color of the region 0 only (0.216, a gray that gives the color of texture 0
with no change), and zero for the six others: a program in the material calculates them
from values of the game when it runs (the colors of the weapon). In the M77 each pixel of the
muzzle device, 60 percent of the magazine and 89 percent of the sight unit are in such a
region. The files here give each region the color of the region 0, so these three pieces
are gray.

## What is proved

Each statement names the command that proves it. I ran each command on 2026-10-06.

* **The same bytes.** `./port marathon regress` extracts each weapon of
  `data/marathon/extract/out/` again and compares each file (sha256). It prints
  `m77_omnipositor: same (160 files, 37620297 bytes)`. The stored result is the result of the
  first work, so the tools of this repository give the files of the first work. The table of
  the 64-bit tag hashes that `setup.sh` makes gives the same result as the table of the first work.
* **The packages and Oodle.** `./port marathon setup` prints
  `the packages open: 1032829 entries; 50 entries read with no error; 43853 hashes in the table`.
* **The item.** `./port marathon find "M77"` prints `DF4263CA  M77 Omnipositor  no entity of its
  own` and `6F95AD10  M77 Assault Rifle  entity 80A7C262`.
* **The counts of the table "Result".** `./port marathon extract ...` prints them, and
  `manifest.json` has them: the pieces with their triangles and their place (`pieces`), the
  textures and the rule of each material (`textures`, `materials`), the bones
  (`weapon_skeleton`), the clips with their frames and errors (`clips`), the states and the
  first-person clips (`first_person[0].states`, `first_person[0].clips`).
* **The gun bones of the two skeletons.** The extraction prints `the rest places of the gun
  parts differ by 0.000000` (`first_person[0].weapon_bone_rest_difference` of the manifest).
* **A second weapon.** `./port marathon extract "Overrun AR" --out data/marathon/extract/work/other`
  gives 3 of 4 pieces with a place, the weapon tags `887BEBCB` and `rifle`, 68 first-person
  clips and the same 10 gun bones.
* **The look.** `./port marathon render FILE.glb OUT.png` makes pictures of a file. The muzzle
  device is at the front of the body, the sight unit is on top of it, and the magazine is in
  its well (`data/marathon/extract/validation/m77_weapon_all_pieces.jpg`).
* **A layout.** `./port marathon notes find-value B3C9A7B2 --pkg investment_globals` finds the
  assignment hash of the M77 in one tag of the class `80806CAC` (the art table), and
  `./port marathon notes walk 80A7C262 --depth 1` prints the pieces of the gun entity.

## What is not proved

No command of this repository repeats these statements. Each one is a measurement of the
first work (2026-10-06), and the stored pictures are its evidence.

* 3,000 random entries were read with no error and with the correct size. (The setup reads 50.)
* The vertices of each of the 5 models have the bounds that the model tag stores (largest
  difference 0.00001 m), and the largest index of each index buffer is the vertex count
  minus 1.
* The texture coordinates of the sight unit agree with its base color texture
  (`validation/m77_sight_texture_coordinates.jpg`: each outline is on a painted area).
* The exact places of the pieces: the point of the muzzle device is at x 0.4317 m and the
  body ends at x 0.4316 m; the point of the sight unit is at z 0.1441 m and the body ends at
  z 0.1441 m.
* In each of the 68 first-person clips for this rig, the gun bone is on the grip bone of the
  right hand (0.00003 m at most). In the first frame of each clip that the port uses, the
  camera bone is at (0, 1.66, 0), as in Destiny 2 (2 mm away in the reload).
* The reload of the arms and the reload of the weapon are one motion: in each frame in which
  the magazine is out, it is in the left hand (`validation/m77_first_person_clips.jpg`, and
  the pictures of the Fallout 4 port).
* The Fallout 4 port of this file works in the game (`../../mods/M77/README.md` has the game
  test of the first work; no command here repeats a game test).
* The counts of the item tables (2,685 items, 2,543 with a name, 2,122 rows of the art table).
* The setup ran on one computer (Linux, x86-64, gcc, cargo). A second computer is not tested.
* `./port marathon notes scan-text` was stopped after 170 s with 6 places found. The complete
  scan of the first work needed 1,093 s.
* A build of the game after 2026-10-06 is not tested. A class number that is not there gives
  the message "no tag of the class ...: the layouts of this file are for another build".

## What is not correct or not done

* **No comparison with the game.** The game was not started, and no reference picture is
  here. "Correct" is from the data and from the pictures of Blender.
* **The variant.** The item definitions of `M77 Omnipositor` and of `M77 Assault Rifle`
  differ in one index (0xFC and 0xF9 at 0x918) and in three small values. The tools do not
  read the table that the index points into. The files are those of the gun entity of
  the base item.
* **The colors of the regions** (see "The materials"). Emission is not done.
* **The hands.** The file has no hand mesh of Marathon: the arm entities have no model, and
  I did not look for the model of a body. `--hands` puts the hand mesh of Destiny 2 on the
  bones. The hand bones of Marathon have other lengths (the forearm is 1.2 cm longer, the
  palm 0.7 cm shorter, some finger bones are 10 to 23 percent shorter), so that mesh does
  not fit exactly.
* **The second magazine** (an entity below the magazine piece) has no place: no point names it.
* **A weapon with other bones.** `V75 SCAR` has a skeleton of 14 bones with other names. Its
  pieces get their places and its weapon file is made, but its first-person file is not
  correct: the arm entity that it names has the 10 gun bones of the M77, not the bones of
  this weapon. The extraction then prints `the rest places of the gun parts differ by
  1.000000`. I did not find how the game joins the two skeletons.
* **The sight unit is rigid in the files of the weapon.** It has 4 bones of its own
  (`b_anim`, one with no name, `b_scope_1`, `b_scope_2`) and a rig; its clips are not read.
* **The body has no moving part.** Each of its vertices is on `b_handle`. The clips move
  `b_bolt` and `b_bolt_handle`, and no extracted mesh is on these bones.
* **Only the opaque parts of the highest detail** are in the files. `--stages` and
  `--all-detail` give the others (the decals of the body, glass). Those were not examined.
  `regress` cannot repeat a result that was made with one of the two options: the manifest
  does not record them.
* **Clips with another node count.** 29 of the 97 clips of the states have another node
  count than the rig (states of other actions of the player). They are not in the file.
* **The conditions of a state** (stand or crouch, and others) have hashes with no word for
  most values. The port uses the first choice of each state; for `idle` that is the clip
  with the stance value `ACE6F0CE`, which I read as "stand" from its place in the tree.
* **The newer animation system.** An arm entity has a second set of animation data (classes
  `80803B54` and `808039DB`, with 435 clip references). It is not read. I do not know which
  of the two the game uses for a state; the graph that the tools read has the state names of
  Destiny 2 and gives clips that fit (the frame counts, the pictures).
* **The frame rate of 30** is the value of Destiny 2, not a value from the files.
* **The vertex layout** is from the size of a vertex (24 and 4 bytes), not from the shader.
  A model with other sizes is not supported, and a skinned mesh with weights is not read.
* **The Oodle loader** is new code with small replacement functions for the imports. It
  decoded each entry of this work; it has no other test.
* **One process, one game.** `m2x.patch_parser()` changes the animation decoder for the
  process. A process that calls it must not read a rig of Destiny 2.

## Folders

In the source tree, `marathon/extract/`:

| File or folder | Content |
| --- | --- |
| `m2x.py`, `m2x_extract.py` | The layouts of Marathon, and the extraction program. |
| `setup.sh` | Makes the runtime folder and the table of the 64-bit tag hashes. |
| `regress.py` | The extraction of each stored weapon again, and the comparison of the bytes. |
| `port.toml` | The commands of `./port marathon ...`, and what each one needs. |
| `oodle9/oodle9.c` | The source of the Oodle 9 loader. |
| `tag64/` | The source of the program for the 64-bit tag hashes. |
| `tools/render_glb.py` | Pictures of a `.glb` file with Blender. |
| `notes/` | Analysis programs: `scan_text.py`, `class_graph.py`, `paths.py`, `find_value.py`, `describe.py`, `walk.py`, `dxil.py` (`./port marathon notes NAME`). |

Below `data/marathon/extract/` (not in git):

| Folder | Content |
| --- | --- |
| `runtime/` | The built Oodle 9 loader, a link to the library of the game, and the built program `tag64`. |
| `target/` | The cargo build folder of `tag64`. |
| `notes/` | `tag64.tsv`, and the results of the analysis programs (`class_graph.txt`, `paths.tsv`, `scan_omnipositor.txt`). |
| `out/m77_omnipositor/` | The result. |
| `validation/` | Pictures and the reload video. |
| `work/` | Work pictures; `work/_regress/` is the scratch folder of `regress`, with the log of each extraction. |

The models, the textures and the animations are assets of Marathon (Bungie). Do not publish them.
