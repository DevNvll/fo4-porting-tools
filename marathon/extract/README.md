# Marathon: the extraction of a weapon and of its first-person rig

This folder has `m2x`. It runs the `d2x` tools from `destiny/extract/`, made for the 2020
build of Destiny 2, on Marathon's packages. Marathon uses a later version of the Tiger
engine. The first work extracted the M77 Omnipositor. Its result is in
`data/marathon/extract/out/m77_omnipositor/`, with pictures and one video in
`data/marathon/extract/validation/`. The result's first-person file is the input of the
Fallout 4 port. For the port, see `../README.md`, `../port/sets/m77_omnipositor.toml`, "The
M77 of Marathon" in `../../destiny/port/README.md`, and `../../mods/M77/`.

Nothing here changes a `d2x` file or a game file. The programs use the `d2x` modules as a
library and only read the game folder.

## Result

| Item | Result |
| --- | --- |
| Packages | 629 package files open, 1,032,829 entries. |
| Item | `M77 Omnipositor`, item hash `DF4263CA`, found by its name in the string tables. |
| Models | 5 pieces: the body (2,468 triangles), the magazine (2,739), a second magazine for the reload, the muzzle device (5,448; the slot `barrel`) and the sight unit (14,173; a rear sight with a box, and a front sight). |
| Places of the pieces | 4 pieces have their place on the weapon, from the named points of the gun entity. The second magazine has none. |
| Textures | 13 textures for 7 materials, as PNG files, plus each material as a Destiny 2 texture set (albedo, normal, gstack). |
| Skeleton of the weapon | 10 bones: `b_handle`, `b_magazine`, `b_bolt`, `b_bullet_1`, `b_bullet_2`, `b_casing`, `b_mag_release`, `b_safety`, `b_trigger`, `b_bolt_handle`. |
| Clips of the weapon | 15 clips in the weapon's animation set, all decoded without error. 10 are for this skeleton. The reload has 105 frames. |
| First-person rig | The arm entity `fp_rifle_arms`, with 91 bones: the player's body, plus the weapon's 10 bones on the grip bone of the right hand. It is the Destiny 2 rig, with the same bone names and bone axes. |
| First-person clips | The arm entity's animation graph has 93 states. 85 have a clip for this weapon, the tag `rifle`. That makes 97 clips, all decoded without error. 68 are for this rig and are in the file. |
| Files | `m77_omnipositor_weapon.glb` (4 pieces on the skeleton, 10 animations), `m77_omnipositor_first_person.glb` (the rig, the 4 pieces, 78 animations), one `.glb` for each piece, `textures/`, `manifest.json`, `states.json`, `raw/`. 160 files, 37.6 MB. |

`data/marathon/extract/validation/` has the pictures. `m77_weapon_all_pieces.jpg` shows the
weapon file, `m77_pieces.jpg` shows four pieces alone, and `m77_first_person_clips.jpg` has
frames from five first-person clips. `m77_reload_1.mp4` is the weapon's reload clip, 3.5 s
long, made before the muzzle device and the sight unit had their place.

## How to run it

`./port doctor` shows what is set up and what is missing. The settings are in
`data/config.toml`, and `config.example.toml` lists them. `marathon_game` is the game folder,
the one with `packages/` and `bin/x64/`. `blender` is Blender 4.5.

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

`./port marathon` lists the commands. The extraction takes 13 to 17 seconds.

* `--art ITEM` is for an item without a row in the game's art table, which is a variant of
  another weapon. The extraction then uses the entity of ITEM. `find` prints
  `no entity of its own` for such an item.
* `--hands FILE.glb` puts the hand mesh from a Destiny 2 first-person file, which
  `./port destiny extract` makes, on the rig. It is not a Marathon mesh and is only there
  for pictures. The stored M77 result was made with it.
* `--arms NUMBER` selects another of the weapon's arm entities. The manifest lists them.
* `--out OUT` puts the files into `OUT/NAME/`. The default is `data/marathon/extract/out`.
* `MARATHON_PACKAGES` names a packages folder other than `packages` in the game folder.

Every program also runs without `./port`. One that reads the packages needs the Python of
the `d2x` environment, and it finds `portkit` and `d2x` by itself. From the repository root:

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

`setup.sh` writes only below `data/marathon/extract/`. It is safe to run again, because it
skips any step that is complete. When something is missing, such as a C compiler, cargo, the
game folder or a part of `d2x`, the other steps still run. The output ends with every
missing thing and what to do about it, and the exit code is 1.

| File | How |
| --- | --- |
| `runtime/liboodle-data-shared.so` | `cc -O2 -fPIC -shared -o ... oodle9/oodle9.c -lpthread`. `CC` names another compiler. Linux on x86-64 only. |
| `runtime/oo2core_9_win64.dll` | A link to `bin/x64/oo2core_9_win64.dll` in the game folder. The library is a game file, so it is not in this repository. |
| `runtime/tag64`, `target/` | `cargo build --release --locked` of `tag64/`, against the `tiger-pkg` clone that the `d2x` setup made in `data/destiny/extract/vendor/tiger-pkg`. You can delete `target/` after the build. |
| `notes/tag64.tsv` | `runtime/tag64 PACKAGES goliath`, with the lines sorted. `--table` makes it again. |

The last setup step opens the packages and reads 50 entries. That needs the shim and the
game's library, so it proves the runtime folder.

From `d2x`, `m2x` uses the Python environment, the package reader
`data/destiny/extract/target/release/libtigerpkg_ffi.so` and the two clones in
`data/destiny/extract/vendor/`. It does not use the `d2x` runtime folder, which holds the
Oodle 3 shim. `m2x` gives the package reader a runtime folder of its own.

`tiger-pkg` keeps a cache of the package list in the user's cache folder, in `tiger-pkg`
below `XDG_CACHE_HOME`. It is about 20 MB for Marathon and is not below `data/`.

## What was necessary

"The same tools with minimal changes" is true for the package reader, the animation decoder,
the glTF writer and the form of the data. Every class number and every offset is new.

| Part | State | What was necessary |
| --- | --- | --- |
| Package reader (`tiger-pkg`) | Works unchanged | The version code `goliath`. |
| Oodle | New file | Marathon has Oodle 9, and only as a Windows library. The `tiger-pkg` Linux shim is for Oodle 3. It stopped with a segmentation fault, because the new library's start code reads the Windows thread block. `oodle9/oodle9.c`, 208 lines, loads the library. It maps the sections, applies the relocations, gives each of the 41 imports a small function and sets the GS register for every call. |
| 64-bit tag hashes | New program | Marathon names entities, clips and textures with 64-bit hashes, which the `d2x` Python wrapper does not have. `tag64/`, 23 lines of Rust on `tiger-pkg`, prints the table of 43,853 hashes. |
| Animation decoder (`tiger-animation-parser`) | Works with 3 corrections at run time | The decoder has a `marathon` version, for an earlier build. In this build the skeleton block and the rig block start 16 bytes earlier, and a row of the rig relations has 72 bytes, against 52 in Destiny 2. `m2x.patch_parser()` corrects the three values in the process, and the decoder's files stay unchanged. |
| glTF writer (`d2x.export.build_glb`, `d2x.gltf`) | Works unchanged | |
| Layouts of the data (`d2x.investment`, `entity`, `model`, `texture`, `strings`, `graph`) | New: `m2x.py` (799 lines) | Every class number differs from Destiny 2, and no public tool has the Marathon classes. I found each one in the data. The structures are close to those of Destiny 2 after Beyond Light, with other offsets. The animation graph has the Destiny 2 layout with a larger node. |
| Shaders | New note program | A Marathon shader is DXIL (LLVM bitcode), not Direct3D 11 bytecode. `notes/dxil.py` makes it readable for `llvm-dis`. |
| The tools of `destiny/port/` (Destiny 2 to Fallout 4) | Work with two new options | The first-person file has the form of a Destiny 2 file. The Marathon hand has other bone lengths, so the M77 set file has `knuckles = "align"` and `closed_fingers = true`. See `../../destiny/port/README.md`. |

## The layouts that the tools read

Every number comes from an analysis of this game build, and the programs in `notes/` print
the data the analysis used. The tools find a table by its class, not by its tag.

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

Names are FNV-1 hashes, as in Destiny 2. The graph's state names are the Destiny 2 words
(`idle`, `fire`, `iron_sight_idle`, `ready`, `put_away`, `reload_empty`, ...). A word list
gave the bones of the weapon and the sight unit, the rig's 10 control names, the slots
(`barrel`, `sight`, `magazine`, `foregrip`, `chip`, `charm`, `sticker`), the weapon tags
(`rifle`, `pistol`, `shotgun`, `smg`, `sniper_rifle`, `railgun`, `dmr`, `lmg`, `hmg`, `ar`,
`magnum`, `knife`, `unarmed`, `grenade`), and `empty`, `partial`, `full`, `stand`, `crouch`,
`attachment`, `grip`, `reload_1`. No word was found for 27 of the weapon's 28 point names, 9
bones of the arm rig and most condition values.

## How the item gives the files

1. The name gives the item hash `DF4263CA`, through the display map, the display definition
   and the string container.
2. The art table has no row for this item. `M77 Omnipositor` is a variant of
   `M77 Assault Rifle`, and its description says "Modified M77 Assault Rifle". That item,
   `6F95AD10`, has the row: assignment hash `B3C9A7B2`, entity `80A7C262`. `--art` gives the
   item with the row.
3. The entity has the skeleton, the rig, an animation set (`80A7ADB9`, 15 clips), a component
   with 8 slots, and 28 named points. Three slots have a default piece: `barrel`, `magazine`
   and `sight`. A fourth piece, the body, has no slot.
4. Each piece is an entity with a model. A piece names one point on the weapon, and its own
   point `attachment` goes there. The muzzle device's point is on `b_handle`, at the front
   of the body (x 0.4317 m, z 0.1031 m). The sight unit's point is on top of the body
   (x 0.0211 m, z 0.1441 m). The magazine's point is on the bone `b_magazine`, with a
   rotation, so the magazine moves with that bone.
5. The slots component names a list of 9 arm entities, one without a body name and one for
   each player body. An arm entity has the skeleton and the rig of the first-person body, an
   animation set with 517 clips and 304 entries, an animation graph and the tag trees.
6. The weapon's slots component has the tag pair `rifle` / `rifle`. For each state of the
   graph, the tree gives the set entries for that tag, and an entry gives a clip.

## The first-person file

`m77_omnipositor_first_person.glb` has the form of a `d2x` first-person file: one skin with
91 bones, the pieces as meshes `regionNN_ENTITY` on the weapon bones, the camera at
`b_utility`, and one animation per clip. `manifest.json` has the list `first_person`, and
`states.json` has the clip of each state in the form of `destiny/port/tools/d2states.py`.

* `fp_NNN_TAG` is a clip of the arms, where NNN is its place in the animation set. There
  are 68.
* `weapon_NNN_TAG` is a clip of the gun entity on the same skeleton, with the body bones at
  rest and the gun parts as in the clip. There are 10. In a reload, a clip of the arms does
  not move the gun parts. The weapon has that motion, and the game plays the two together.
  The gun bones rest in the same places in both skeletons, with a difference of 0.000000.

The port uses these M77 states: `idle` (97 frames), `iron_sight_idle` (97, one
pose), `fire` (three clips of 15 frames, with the thresholds 0.333, 0.667 and 1.0),
`iron_sight_fire` (14), `ready` (22), `put_away` (12), `reload_empty` / `reload_full`
(104 frames for the value `empty`, 72 frames for `partial`), `sprint_loop` (one pose).

## The materials

The pixel shaders say how a material uses its textures, and `notes/dxil.py` prints one. The
render targets are those of Destiny 2: the color, the normal, whose length carries the
smoothness, and the metal value with the occlusion. `m2x.material_plates` writes each
material as a Destiny 2 texture set, `textures/MATERIAL_albedo.png`, `_normal.png` and
`_gstack.png`, so the `destiny/port/` tools read it as they are. The manifest has the rule
for each material.

| Rule | Materials of the M77 | Content |
| --- | --- | --- |
| `palette` | The body, the two rounds in the magazine, parts of the sight unit | One texture, an atlas of flat colors that the three materials share. The texture coordinates of a part point at a color. The smoothness is one value of the constants, 0.3, or 0.44 for the rounds. No normal map, no metal. |
| `detail` | The muzzle device, the magazine, the sight unit | 6 textures. Color = texture 0 (gray, with the prints) x the color of a region x a detail value. Texture 3 has the regions (red, green, blue) and the smoothness (alpha). The alpha of texture 0 is the occlusion. The metal value is texture 2, which is black here. |
| `constant` | One part of the rear sight | No texture. The color is (5, 0, 0) of the constants, a red light. The file has a red surface. |

The colors of the regions are not in the files. A `detail` material has seven regions. The
file only has the color of region 0, which is 0.216, a gray that leaves the color of texture
0 unchanged. The other six are zero, because a program in the material calculates them at
run time from game values, the colors of the weapon. In the M77, every pixel of the muzzle
device, 60 percent of the magazine and 89 percent of the sight unit are in such a region.
The files here give every region the color of region 0, so these three pieces are gray.

## What is proved

Each statement names the command that proves it. I ran them all on 2026-10-06.

* The extraction gives the same bytes. `./port marathon regress` extracts every weapon in
  `data/marathon/extract/out/` again and compares the sha256 of every file. It prints
  `m77_omnipositor: same (160 files, 37620297 bytes)`. The stored result comes from the first
  work, so the tools in this repository give the files of the first work. The table of 64-bit
  tag hashes that `setup.sh` makes gives the same result as the table from the first work.
* The packages open and Oodle decodes them. `./port marathon setup` prints
  `the packages open: 1032829 entries; 50 entries read with no error; 43853 hashes in the table`.
* The item is found. `./port marathon find "M77"` prints
  `DF4263CA  M77 Omnipositor  no entity of its own` and
  `6F95AD10  M77 Assault Rifle  entity 80A7C262`.
* The counts in the table "Result". `./port marathon extract ...` prints them, and
  `manifest.json` records them. `pieces` has the pieces with their triangles and their place,
  `textures` and `materials` have the textures and the rule for each material,
  `weapon_skeleton` has the bones, and `clips` has the clips with their frames and errors.
  `first_person[0].states` and `first_person[0].clips` have the states and the first-person
  clips.
* The gun bones match in the two skeletons. The extraction prints
  `the rest places of the gun parts differ by 0.000000`, and the manifest has that value as
  `first_person[0].weapon_bone_rest_difference`.
* A second weapon extracts.
  `./port marathon extract "Overrun AR" --out data/marathon/extract/work/other` gives 3 of 4
  pieces with a place, the weapon tags `887BEBCB` and `rifle`, 68 first-person clips and the
  same 10 gun bones.
* `./port marathon render FILE.glb OUT.png` makes pictures of a file. In
  `data/marathon/extract/validation/m77_weapon_all_pieces.jpg` the muzzle device is at the
  front of the body, the sight unit is on top of it, and the magazine is in its well.
* You can check a layout.
  `./port marathon notes find-value B3C9A7B2 --pkg investment_globals` finds the M77's
  assignment hash in one tag of the class `80806CAC`, the art table.
  `./port marathon notes walk 80A7C262 --depth 1` prints the pieces of the gun entity.

## What is not proved

No command in this repository repeats these statements. Each is a measurement from the
first work, on 2026-10-06, and the stored pictures are its evidence.

* 3,000 random entries were read without error and with the correct size. The setup reads 50.
* The vertices of each of the 5 models have the bounds that the model tag stores, with a
  largest difference of 0.00001 m. The largest index of each index buffer is the vertex count
  minus 1.
* The sight unit's texture coordinates agree with its base color texture. In
  `validation/m77_sight_texture_coordinates.jpg` every outline is on a painted area.
* The exact places of the pieces. The muzzle device's point is at x 0.4317 m and the body
  ends at x 0.4316 m. The sight unit's point is at z 0.1441 m and the body ends at
  z 0.1441 m.
* In each of the 68 first-person clips for this rig, the gun bone is on the grip bone of the
  right hand, at most 0.00003 m away. In the first frame of every clip the port uses, the
  camera bone is at (0, 1.66, 0), as in Destiny 2. In the reload it is 2 mm away.
* The reload of the arms and the reload of the weapon are one motion. In every frame where
  the magazine is out, it is in the left hand. `validation/m77_first_person_clips.jpg` and
  the pictures of the Fallout 4 port show it.
* The Fallout 4 port of this file works in the game. `../../mods/M77/README.md` has the game
  test from the first work, and no command here repeats a game test.
* The counts of the item tables: 2,685 items, 2,543 with a name, 2,122 rows in the art table.
* The setup ran on one computer, with Linux, x86-64, gcc and cargo. A second computer is not
  tested.
* `./port marathon notes scan-text` was stopped after 170 s with 6 places found. The complete
  scan in the first work took 1,093 s.
* A game build after 2026-10-06 is not tested. A missing class number gives the message
  "no tag of the class ...: the layouts of this file are for another build".

## What is not correct or not done

* Nothing was compared with the game. The game was not started, and no reference picture is
  here. "Correct" comes from the data and from the Blender pictures.
* The item definitions of `M77 Omnipositor` and `M77 Assault Rifle` differ in one index,
  0xFC and 0xF9 at 0x918, and in three small values. The tools do not read the table the
  index points into. The files are those of the base item's gun entity.
* The colors of the regions are not in the files, as "The materials" says. Emission is not
  done.
* The file has no Marathon hand mesh. The arm entities have no model, and I did not look for
  the model of a body. `--hands` puts the Destiny 2 hand mesh on the bones. Marathon's hand
  bones have other lengths: the forearm is 1.2 cm longer, the palm 0.7 cm shorter, and some
  finger bones are 10 to 23 percent shorter. So that mesh does not fit exactly.
* The second magazine, an entity below the magazine piece, has no place, because no point
  names it.
* A weapon with other bones gets a wrong first-person file. `V75 SCAR` has a skeleton of 14
  bones with other names. Its pieces get their places and its weapon file is made, but its
  first-person file is not correct. The arm entity it names has the 10 gun bones of the M77,
  not this weapon's bones. The extraction then prints
  `the rest places of the gun parts differ by 1.000000`. I did not find how the game joins
  the two skeletons.
* The sight unit is rigid in the weapon's files. It has 4 bones of its own (`b_anim`, one
  with no name, `b_scope_1`, `b_scope_2`) and a rig, but its clips are not read.
* The body has no moving part. All its vertices are on `b_handle`. The clips move `b_bolt`
  and `b_bolt_handle`, but no extracted mesh is on those bones.
* Only the opaque parts at the highest detail are in the files. `--stages` and
  `--all-detail` give the others, the decals of the body and glass. Those were not examined.
  `regress` cannot repeat a result made with either option, because the manifest does not
  record them.
* 29 of the 97 clips of the states have a different node count from the rig. They belong to
  states of other player actions, and they are not in the file.
* The conditions of a state, stand or crouch and others, have hashes with no word for most
  values. The port uses the first choice of each state. For `idle` that is the clip with the
  stance value `ACE6F0CE`, which I read as "stand" from its place in the tree.
* The newer animation system is not read. An arm entity has a second set of animation data,
  in the classes `80803B54` and `808039DB`, with 435 clip references. I do not know which of
  the two the game uses for a state. The graph the tools read has the Destiny 2 state names
  and gives clips that fit, going by the frame counts and the pictures.
* The frame rate of 30 is the Destiny 2 value, not a value from the files.
* The vertex layout comes from the size of a vertex, 24 and 4 bytes, not from the shader. A
  model with other sizes is not supported, and a skinned mesh with weights is not read.
* The Oodle loader is new code with small replacement functions for the imports. It decoded
  every entry of this work and has no other test.
* One process can read one game. `m2x.patch_parser()` changes the animation decoder for the
  process, so a process that calls it must not read a Destiny 2 rig.

## Folders

In the source tree, `marathon/extract/`:

| File or folder | Content |
| --- | --- |
| `m2x.py`, `m2x_extract.py` | The Marathon layouts, and the extraction program. |
| `setup.sh` | Makes the runtime folder and the table of 64-bit tag hashes. |
| `regress.py` | Extracts every stored weapon again and compares the bytes. |
| `port.toml` | The `./port marathon ...` commands, and what each one needs. |
| `oodle9/oodle9.c` | The source of the Oodle 9 loader. |
| `tag64/` | The source of the program for the 64-bit tag hashes. |
| `tools/render_glb.py` | Pictures of a `.glb` file with Blender. |
| `notes/` | Analysis programs, which `./port marathon notes NAME` runs: `scan_text.py`, `class_graph.py`, `paths.py`, `find_value.py`, `describe.py`, `walk.py`, `dxil.py`. |

Below `data/marathon/extract/`, which is not in git:

| Folder | Content |
| --- | --- |
| `runtime/` | The built Oodle 9 loader, a link to the game's library, and the built program `tag64`. |
| `target/` | The cargo build folder of `tag64`. |
| `notes/` | `tag64.tsv`, and the results of the analysis programs (`class_graph.txt`, `paths.tsv`, `scan_omnipositor.txt`). |
| `out/m77_omnipositor/` | The result. |
| `validation/` | Pictures and the reload video. |
| `work/` | Work pictures. `work/_regress/` is the scratch folder of `regress`, with the log of each extraction. |

The models, textures and animations are Marathon assets and belong to Bungie. Do not publish
them.
