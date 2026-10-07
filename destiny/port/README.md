# Destiny 2 first-person clips for Fallout 4

`d2fo4` converts the first-person clips of a Destiny 2 weapon to Fallout 4 clips. Its input
is the first-person file that `d2x` in `destiny/extract/` writes, a `.glb` with the rig, the
gun, the hands and one animation per clip. One command does the conversion.

```sh
S=destiny/port/sets
./port destiny convert /path/the_last_word_first_person.glb --set $S/the_last_word.toml -o /path/out
./port destiny convert /path/khvostov_7g_02_first_person.glb --set $S/khvostov_7g_02.toml -o /path/out
./port destiny convert /path/hammerhead_first_person.glb --set $S/hammerhead.toml -o /path/out
./port destiny convert /path/the_chaperone_first_person.glb --set $S/the_chaperone.toml -o /path/out
./port destiny convert /path/the_huckleberry_first_person.glb --set $S/the_huckleberry.toml -o /path/out
./port destiny convert /path/the_last_word_first_person.glb --clip fp_001_80BC8660=WPNReload -o /path/out
```

The `--set` form converts the whole clip set of a weapon: 24 clips for The Last Word, a hand
cannon; 27 for the Khvostov 7G-02, an auto rifle; 27 for Hammerhead, a machine gun; 30 for
The Chaperone, a shotgun with a lever; and 27 for The Huckleberry, a submachine gun. The
`--clip` form converts single clips. The output folder gets one HKX clip per Fallout 4 clip,
and the same input always gives the same bytes. The command prints the events of each clip.

The tools do for the Destiny rig what `fnv-fo4-port`, the `fnv/` area of this repository,
does for the New Vegas rig. They are built on four parts of it:

* the finger solver, `fnv/tools/blender/solver.py`
* the HKX writer and reader, `fnv/tools/port_hkx.py` and `fnv/tools/anim_fo4.py`
* the archive reader, `fnv/tools/ba2.py`
* the rig folder `data/fnv/rig/`, which has the Fallout 4 first-person skeleton and the hand
  meshes, and `fnv/rig/finger_tips.json`

They read these files where they are and change none of them. The files in `fnv/tools/` are
those of the `fnv-fo4-port` repository at commit `83dcd2d`, branch `animation-only`.

One more step converts the third-person reload of a weapon, the player's body with the gun.
See "The third-person clips".

```sh
./port destiny convert /path/hammerhead_first_person.glb --set destiny/port/sets/hammerhead.toml third --third-output /path/out
```

For a new weapon, follow the procedure in `docs/porting/destiny.md`, under the repository
root. `docs/porting/troubleshooting.md` lists each known problem with its sign and its rule,
and `docs/porting/lessons.md` has the lessons from the ports.

`mod/TheLastWord/`, `mod/Khvostov/` and `mod/Hammerhead/` are esx projects, one per weapon,
each with the model, the textures, the records and the clips. `mod/TexMechanica/` is a
single esx project that puts The Last Word, The Chaperone and The Huckleberry in one plugin,
`TexMechanica.esp`. `./port mod build NAME` packs a project with `esx build`, as "The weapon
for Fallout 4" describes. "This area in the monorepo" says where each folder named here is.

| Option | Meaning |
| --- | --- |
| `--set FILE` | The set file of a weapon, `sets/NAME.toml`. It names the clip of the file for each Fallout 4 clip, extra events, and the clips that take the weapon motion of a vanilla clip. "The keys of a set file" lists the keys. |
| `--clip CLIP=NAME` | A clip of the file and the name of its Fallout 4 clip. Repeat it for more clips. |
| `-o OUT` | The output folder. Default `data/destiny/port/out/WEAPON`. |
| `--template NAME` | The vanilla weapon that supplies the weapon bones, the sound names and the pose of the body bones. Default `revolver44`. A set file names its own template, one of `revolver44`, `combatrifle` and `combatrifle_parts`. |
| `--hold CLIP[:FRAME]` | The hold pose. It fixes where the gun sits in Fallout 4 weapon space. Default: the first frame of the first clip of the file. |
| `--event NAME:FRAME=TEXT` | An event of a clip. It replaces or adds to the events that the tools find. |
| `--skip SHAPE` | A shape of the parts file to leave out of the finger collision. |
| `--name`, `--work` | The name and the location of the work folder. Default `data/destiny/port/work/WEAPON`. |

## This area in the monorepo

This area is `destiny/port/`. `docs/ARCHITECTURE.md` describes the structure of the
repository. Run every command in this document from the repository root. `./port destiny`
lists the commands of the area, `./port destiny COMMAND --help` shows the arguments of one,
and `./port doctor` shows what your computer is missing. Each program also runs on its own,
so `./port destiny convert ...` is `python3 destiny/port/d2fo4.py ...`.

The source files are in git. Everything a tool makes goes under `data/`, which is not. This
document uses short names for these paths.

| Name in this document | Path |
| --- | --- |
| `d2fo4.py`, `tools/`, `check/`, `sets/`, `templates/`, `notes/` | In `destiny/port/`. |
| `rig/d2_hands.json` | `destiny/port/rig/d2_hands.json`, a measurement file, in git. |
| `extract/NAME/`, `work/NAME/`, `out/NAME/`, `validation/NAME/`, every other file of `rig/` | In `data/destiny/port/`. |
| `mod/NAME/` | The esx project `data/mods/NAME/`. Its hand-written files are in `mods/NAME/`, see `mods/README.md`. |
| `marathon/` | `marathon/extract/` has the `m2x` tools, `marathon/port/` the set file of the M77, and `data/marathon/extract/` the results. |
| `fnv-fo4-port` | `fnv/` of this repository, the Fallout 4 library. Its rig folder is `data/fnv/rig/`, and its `finger_tips.json` is `fnv/rig/finger_tips.json`. |
| `destiny-weapons`, `d2x` | `destiny/extract/`, the extraction tool. Its Python environment is `data/destiny/extract/venv/`. |

| Command | Program | What it does |
| --- | --- | --- |
| `./port destiny convert` | `d2fo4.py` | Converts the clips of a set file to Fallout 4 clips. |
| `./port destiny model` | `tools/d2model.py` | Writes the model, the materials, the textures and the sight of a weapon into `data/mods/NAME/`. |
| `./port destiny make-rig` | `tools/make_rig.py` | Writes the vanilla clips of each template into `data/destiny/port/rig/`. |
| `./port destiny states`, `dyes`, `reticle`, `third`, `pose` | `tools/d2states.py`, `d2dyes.py`, `d2reticle.py`, `d2third.py`, `d2pose.py` | Read Destiny 2 data that the extraction does not have. These five import `d2x`, so `./port` starts them with the Python of the `d2x` environment. |
| `./port destiny points` | `tools/d2points.py` | Prints the muzzle, the eye point and a map of the sight, for a set file. |
| `./port destiny check ...` | `check/` | `validate`, `gun`, `gun-on-grip`, `touch`, `touch-table`, `contact`, `contact-table`, `fingers`, `render`, and the picture programs `sheet`, `look-sheet`, `frame-sheet`, `hand-sheet`, `video`, `strip`, `video-sheet`, `third-sheet`. |
| `./port destiny game ...` | `check/` | The game tests `session`, `record`, `third`, `reloads`, `sight`, `trace`, `shots`, `all`, `results`. |
| `./port destiny regress` | `check/regress.py` | The regression of the clips, described below. |
| `./port destiny notes ...` | `notes/` | Programs that analyze the game data. |
| `./port mod build NAME` | `portkit` | Copies `mods/NAME/` into `data/mods/NAME/` and runs `esx build` there. |

The local settings are in `data/config.toml`, and `config.example.toml` lists them. Each one
can also come from an environment variable: `blender` from `BLENDER`, `esx` from `ESX_BIN`,
`fo4_data` from `FO4_DATA`, `proton` from `PROTON_DIR`. `fo4_data` is the `Data` folder of
Fallout 4. No program has a path of one computer in it.

A set file can be in any folder. The tools look for the files and folders it names beside
the `.glb` file, not beside the set file. That applies to `folder` of `[hand_pose]` and of
`[third]`, to `dyes`, to `file` of `[model.sight]` and to the files of `[model.shaders]`.
`folder` of `[third]` has a second place. If it is not beside the `.glb` file, it is a path
under `data/destiny/port/`.

`./port destiny regress [--only NAME]` is the regression. It converts every ported weapon
again into `data/destiny/port/work/_regress/NAME/` and compares the bytes of each HKX file
with the baseline folders that `destiny/port/regress.toml` names. Those hold clips of
`data/destiny/port/out/` and of `data/mods/`. The exit code is 1 if a clip differs. Run it
after every change to a tool. The run of 2026-10-06, after the tools moved into this
repository, covered 6 weapons, the five Destiny 2 guns and the M77, with 162 first-person
clips, 16 third-person clips and 6 power armor clips. 0 differed.

The regression only compares against the stored clips. `./port baseline check` proves that
nobody replaced a stored clip or a release, because `baselines.sha256`, in the repository
root and in git, has the sha256 of each one. Run it after the regression passes. Run
`./port baseline update` only for a change that the user accepted. `out/the_chaperone` and
`out/the_huckleberry` are older results and not a baseline. The clips of those two weapons
are in `data/mods/TexMechanica`.

## The clip set of The Last Word

The set file is `sets/the_last_word.toml`. The clip for each game state comes from Destiny
2's animation graph, through the table in `HANDOFF.md` of the extraction,
`data/destiny/extract/handoff/the_last_word_v1/`.

| Fallout 4 clip | Source |
| --- | --- |
| `WPNIdleReady`, `WPNIdleReadyA` to `D` | `idle`, `fp_000_80BC8633`, 97 frames |
| `WPNIdleSighted`, `WPNIdleSightedWobble` | `iron_sight_idle`, `fp_007_80BC8637`, 97 frames |
| `WPNFireSingleReady`, `A`, `B` | `fire`, `fp_054_80BC8650`, 30 frames. The left hand fans the hammer. |
| `WPNFireSingleSighted` | `iron_sight_fire`, `fp_055_80BC8651`, 33 frames |
| `WPNEquip`, `WPNEquipFast` | `ready`, `fp_040_80BC864A`, 33 frames, with a spin of the gun |
| `WPNUnEquip` | `put_away`, `fp_005_80BC8662`, 5 frames, and the last pose on 8 more frames |
| `WPNReload` | `reload_empty`, `reload_full`, `reload_special`, `fp_001_80BC8660`, 127 frames |
| `WPNSprint` | `sprint_loop`, `fp_018_80BC863E`, 20 frames |
| `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNJumpImpactLand`, `WPNIdleGunDown` | Weapon motion of the vanilla .44 clip, on the Destiny hold pose or sighted pose |

* `sprint_enter` and `sprint_exit` have no clip, because the Fallout 4 graph blends from the
  idle to the sprint loop and back.
* A clip with vanilla weapon motion takes only the rigid motion of the weapon bone from the
  vanilla clip, relative to the vanilla ready pose. That motion moves the whole Destiny
  pose, arms, hands and gun, as one body, so the hands stay on the gun. The camera bone and
  the events are those of the vanilla clip.
* The bone `Camera Control` has the values of the vanilla clips: -5.49 on Z in a clip in the
  sights, 9.51 in the sprint, 0 in every other clip.
* `[hold_end]` repeats the last pose of a clip at its end. The game's first-person graph,
  `GunBehavior`, has a trigger in the state `WPNUnEquip` 0.233 s before the end of the
  put-away clip, and that trigger removes the gun. The Destiny clip is 0.133 s long, so the
  game removed the gun at the first frame, before the hand moved. The game test found this.
  With 8 more frames the clip is 0.4 s long and the game removes the gun at 0.167 s, when it
  is out of view. The videos and numbers for `WPNUnEquip` in `validation/` cover the 5
  source frames. The 8 extra frames are copies of the last one.
* The events are `weaponFire` at frame 0 of each shot, the sound `EquipUp` at frame 0 of the
  equip clips, the two steps of the sprint loop at frames 6 and 16, where the camera bone is
  lowest, and the reload events, which come from the motion of the parts.
* The graph blends `WPNIdleSightedWobble` into the sighted idle with the weight `AimWobble`.
  The vanilla clip has the hands and the sights of the .44, and the reader cannot read it,
  because like every vanilla idle it is in the lossless format. So this clip is the sighted
  idle again. The pose is correct, but the gun does not wobble.
* Melee, grenade, mine and the additive clips (jiggle, pitch, turn, jump) are the vanilla
  .44 clips. In the melee clip and the two throw clips the hands have the pose of the
  vanilla .44. A melee clip with the weapon motion of the vanilla clip was tried. That clip
  turns the gun far to the side, and with the arms moving as one body with the gun, the
  shoulders go through the view.

## The Khvostov 7G-02

The set file is `sets/khvostov_7g_02.toml`, with the template `combatrifle`. There was no
extraction of this weapon, so the file comes from `d2x`, this repository's extraction tool,
with its output in this area's `extract/` folder. The tool and its own output folder do not
change.

```sh
D=data/destiny/port
./port destiny extract "Khvostov 7G-02" --arms "Ancient Apocalypse Grips" --out $D/extract
./port destiny states $D/extract/khvostov_7g_02/manifest.json -o $D/extract/khvostov_7g_02/states.json
```

The extraction writes three first-person files, because the weapon's pattern entity links to
three rig entities. `khvostov_7g_02_first_person.glb`, with 76 bones and 133 clips, is the
one for this weapon. In the pattern entity, the Khvostov's row (content group `879A579B`)
has the tag pair `rifle` / `879A579B` and the rig entity `80BC5EE4`, which is the entity of
that file. The other two files are rigs of other rifles.

The extraction's state table in `manifest.json` has no `idle`, `ready`, `put_away` or
`reload` for this weapon, because its rule for the weapon tags is proved for a hand cannon
only. So `tools/d2states.py` reads the game's animation graph again. It takes the weapon's
tags from that row of the pattern entity: the weapon tag, each tag above it, and the top of
the tag tree. It also follows a weapon node of the graph that leads to one more condition.
`extract/khvostov_7g_02/states.json` is its result.

| Fallout 4 clip | Source |
| --- | --- |
| `WPNIdleReady` | `idle`, the first choice, `fp_001_80BC5F49`, 97 frames |
| `WPNIdleReadyA`, `C` | `idle`, the second choice, `fp_057_80BC5EF6`, 71 frames. The gun moves 0.8 units. |
| `WPNIdleReadyB`, `D` | `idle`, the third choice, `fp_056_80BC5EF5`, 35 frames. The gun moves 1.3 units. |
| `WPNIdleSighted`, `WPNIdleSightedWobble` | `iron_sight_idle`, `fp_015_80BC5F3D`, 97 frames, with the move of `[sight]` |
| `WPNEquip`, `WPNEquipFast` | `ready`, `fp_068_80BC5EF8`, 30 frames. The Khvostov's own clip, under its own tag. |
| `WPNUnEquip` | `put_away`, `fp_004_80BC5F51`, 4 frames, and the last pose on 8 more frames |
| `WPNReload` | `reload_empty`, `reload_full`, `fp_067_80BC5EF7`, 105 frames. The Khvostov's own clip. |
| `WPNFireSingleReady`, `A`, `B`, `WPNFireSingleSighted`, `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNFireAutoSighted` | Weapon motion of the vanilla combat rifle clip, on the Destiny hold pose or sighted pose. The bolt moves as in the vanilla clip. |
| `WPNSprint` | Motion of the vanilla sprint clip relative to its own first frame, on Destiny's sprint pose (`fp_008_80BC5F50`) |
| `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNJumpImpactLand`, `WPNIdleGunDown` | Weapon motion of the vanilla combat rifle clip, on the Destiny hold pose or sighted pose |

* The Destiny graph gives the state `idle` three clips, with the thresholds 0.962, 0.981 and
  1.0. I read them as the limits of a random choice, 96, 2 and 2 percent. The game data does
  not say what the numbers are. The second and third clips start and end in the idle pose,
  so they are the four clips that Fallout 4 plays now and then instead of the idle.
* In the Destiny graph the states `fire` and `iron_sight_fire` have no entry for this
  weapon's tags, so the game plays no first-person rig clip for its shot. Each shot clip
  therefore has the recoil motion of the vanilla combat rifle on the Destiny pose, and the
  charging handle goes 3.67 units to the rear in each shot, as the vanilla bolt does. In the
  Destiny reload it goes 3.11 units. An automatic clip has 20 shots in 67 frames.
* Destiny's clip in the sights is the same clip for every rifle, and the game aligns each
  weapon's sight at run time. In that clip the eye is at z 11.55 of Fallout 4 weapon space,
  above this gun's sight housing at z 10.18. `[sight]` gives the aim point, the center of
  the reticle on the glass of the sight, at z 8.86. Each clip in the sights gets the move
  that puts that point on the view axis, 2.69 units up, on every bone but the camera bone.
  The first game check found this, with the window of the sight below the center of the
  screen. Before the work on the reticle, the aim point was the center of the housing's
  window, at z 8.75, a move of 2.80 units.
* The rifles' sprint loop is one pose in the file. No bone moves in its 20 frames. So the
  sprint clip has the motion of the vanilla sprint on that pose.
* `b_magazine` is the magazine. `bone_68719972`, a name hash, is the charging handle, and
  `[roles]` gives it the kind `bolt`. `b_safety` has no vertex.
* The Destiny rig holds a rifle with two hands. The tools need no change for that, because
  each wrist goes where the source wrist is.

## Hammerhead

The set file is `sets/hammerhead.toml`, with the template `combatrifle_parts`. The file
comes from the extraction tool, as for the Khvostov.

```sh
D=data/destiny/port
./port destiny extract "Hammerhead" --arms "Ancient Apocalypse Grips" --out $D/extract
./port destiny states $D/extract/hammerhead/manifest.json -o $D/extract/hammerhead/states.json
```

The extraction writes one first-person file, with 87 bones and 96 clips. In the pattern
entity, Hammerhead's row (content group `445AABC7`) has the tag pair `rifle` /
`machine_gun`. Here the weapon tag is the tag of the weapon class, not the content group as
for the Khvostov. `tools/d2states.py` reads the weapon tag from the row in both cases.

| Fallout 4 clip | Source |
| --- | --- |
| `WPNIdleReady` | `idle`, the first choice, `fp_042_80BBC9E4`, 97 frames |
| `WPNIdleReadyA`, `C` | `idle`, the second choice, `fp_054_80BBC9F1`, 71 frames |
| `WPNIdleReadyB`, `D` | `idle`, the third choice, `fp_023_80BBC9D8`, 51 frames |
| `WPNIdleSighted`, `WPNIdleSightedWobble` | `iron_sight_idle`, `fp_018_80BBC9D5`, 97 frames, with the move of `[sight]` |
| `WPNFireSingleReady`, `A`, `B` | `fire`, `fp_009_80BBC9CB`, 21 frames (the tag `machine_gun`) |
| `WPNFireSingleSighted` | `iron_sight_fire`, `fp_048_80BBC9E9`, 21 frames, with the move of `[sight]` |
| `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack` | Automatic fire from `fp_009_80BBC9CB` (`[auto]`) |
| `WPNFireAutoSighted` | Automatic fire from `fp_048_80BBC9E9` (`[auto]`) |
| `WPNEquip`, `WPNEquipFast` | `ready`, `fp_013_80BBC9CF`, 30 frames |
| `WPNUnEquip` | `put_away`, `fp_014_80BBC9D0`, 4 frames, and the last pose on 8 more frames |
| `WPNReload` | `reload_empty`, `reload_full`, `reload_special`, `fp_008_80BBC9CA`, 180 frames |
| `WPNSprint` | Motion of the vanilla sprint clip relative to its own first frame, on Destiny's sprint pose (`fp_037_80BBC9E1`, one pose) |
| `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNJumpImpactLand`, `WPNIdleGunDown` | Weapon motion of the vanilla combat rifle clip, on the Destiny hold pose or sighted pose |

* The gun has 12 moving parts, and most of their bones have a hash instead of a name.
  `[bones]` gives each one its Fallout 4 bone. The ammunition box is `WeaponMagazine`, the 8
  belt links are `WeaponMagazineChild1` to `5` and `WeaponExtra1` to `3`, the top cover with
  the sight is `WeaponOptics1`, its latch is `WeaponOptics2`, and the charging handle is
  `WeaponBolt`. That uses 12 of the 13 weapon bones of the Fallout 4 skeleton. The template
  `combatrifle_parts` is `combatrifle` plus the bones `WeaponExtra2` and `WeaponExtra3`,
  which the vanilla mesh does not have.
* In the file's bind pose the belt is a straight line to the left of the gun.
  `part_rest = "hold"` makes each part's rest place its place in the hold pose, so a vanilla
  third-person clip shows the belt as it is in the idle.
* Destiny has one clip for a shot, 21 frames long. The gun kicks 1.9 units in the first two
  frames. `[auto]` makes an automatic clip from it, with the length and the events of the
  vanilla automatic clip, 67 frames and 20 shots. At each `weaponFire` event the shot starts
  again from its first frame. `fnv-fo4-port` has the same rule.
* In Destiny's clip in the sights the eye is at z 11.55, the same place as for the Khvostov,
  since every rifle uses that clip. This gun's reticle is on the glass of its sight at z
  14.95 (see "The glass of the sight and the reticle"), so each clip in the sights moves
  3.40 units down. Before the work on the reticle, the aim point was the center of the
  housing's window, at z 15.1, a move of 3.55 units.
* In the reload, the box gives `ReloadMagOut` at frame 21 and `ReloadMagIn` at frame 48, and
  the charging handle gives `ReloadBoltOpen` and `ReloadBoltClose` at frames 137 and 145.
  `reloadComplete` is at frame 105, 2 frames after the cover closes. When the box goes in,
  the cover is still open and the belt is not in the gun.

## The Chaperone

The set file is `sets/the_chaperone.toml`, with the template `combatrifle`. The file comes
from the extraction tool, as for the Khvostov.

```sh
D=data/destiny/port
./port destiny extract "The Chaperone" --arms "Ancient Apocalypse Grips" --out $D/extract
./port destiny states $D/extract/the_chaperone/manifest.json -o $D/extract/the_chaperone/states.json
./port destiny dyes "The Chaperone" -o $D/extract/the_chaperone/dyes.json
./port destiny reticle "The Chaperone" -o $D/extract/the_chaperone/sight.json
```

The extraction writes one first-person file, with 77 bones and 101 clips. The weapon tag is
`shotgun`, and the gun's content group, `7FDE2191`, has its own clips for the shot, the draw
and the lever.

| Fallout 4 clip | Source |
| --- | --- |
| `WPNIdleReady` | `idle`, the first choice, `fp_002_80BBD611`, 99 frames |
| `WPNIdleReadyA`, `C` | `idle`, the second choice, `fp_053_80BBD630`, 71 frames |
| `WPNIdleReadyB`, `D` | `idle`, the third choice, `fp_033_80BBD625`, 35 frames |
| `WPNIdleSighted`, `WPNIdleSightedWobble` | `iron_sight_idle`, `fp_012_80BBD61B`, 97 frames, with the move of `[sight]` |
| `WPNFireSingleReady`, `A`, `B` | `fire`, `fp_071_80EF3E35`, 36 frames (a clip of The Chaperone) |
| `WPNFireSingleSighted` | `iron_sight_fire`, `fp_074_80EF3E38`, 37 frames, with the move of `[sight]`. The left hand moves the lever. |
| `WPNEquip`, `WPNEquipFast` | `ready`, `fp_072_80EF3E36`, 24 frames (a clip of The Chaperone) |
| `WPNUnEquip` | `put_away`, `fp_007_80BBD616`, 4 frames, and the last pose on 8 more frames |
| `WPNReload1` to `WPNReload6`, `WPNReload` | Three clips of the file, one after the other (`[compose]`), with 1 to 6 shells: 91, 118, 145, 172, 199 and 226 frames. `WPNReload` is the clip with 6 shells. |
| `WPNSprint` | Motion of the vanilla sprint clip relative to its own first frame, on Destiny's sprint pose (`fp_045_80BBD628`) |
| `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNJumpImpactLand`, `WPNIdleGunDown` | Weapon motion of the vanilla combat rifle clip, on the Destiny hold pose or sighted pose |

* `b_pump` is the lever with the trigger guard, on `WeaponBolt`. `b_shell` is the shell that
  the hand puts in, on `WeaponMagazine`. `bone_8E40D42D` is the gate of the loading port, on
  `WeaponExtra1`.
* Destiny has no single clip for a shotgun reload. Its graph plays three states.
  `reload_enter` has 16 frames, in which the gun turns up. The state `6C41757C` plays once
  per shell and has 28 frames, in which the left hand puts one shell in. `chamber_1` has 49
  frames and is a clip of The Chaperone. In it the right hand turns the gun once around the
  lever, which opens and closes. `[compose]` joins these into one clip for each count of
  shells from 1 to 6. The shell clip does not end in the pose it starts in, because the left
  hand is 34 cm away, below the view. `blend` takes that difference to zero over the first 3
  frames of the next clip. The shell is behind the camera when Destiny does not show it, so
  `cut` keeps it out of the blend.
* The mod's behavior source, `mod/TexMechanica/behavior/thechaperone/thechaperone.bhv`, has
  one line for each count of rounds, from `when ammo == 5 play WPNReload1` to
  `when ammo == 0 play WPNReload6`. esx makes a state and an IDLE record for each line, and
  the game plays the clip with as many shells as the gun has room for.
* `[piece_events]` gives the events of each of the three clips, and each use of a clip adds
  its events. They are the shell sound at frame 10 of each shell clip (the sound of the
  vanilla double-barrel shotgun), `reloadComplete` at frame 12 of the last shell clip, the
  two lever sounds, and `reloadEnd` at frame 40 of `chamber_1`. The left hand is back on the
  gun at frame 30.
* The shot at the hip does not move the lever. The gun kicks and comes back in 36 frames.
  The clip in the sights does move it, in frames 14 to 22. Destiny has no other first-person
  rig clip for the lever after a shot.
* The gun has a glass between the two horns of its rear sight, with two red rings, and a
  reticle (see "The glass of the sight and the reticle"). The center of the rings is at z
  8.85. In Destiny's clip in the sights the eye is at z 9.61, so each clip in the sights
  moves 0.76 units up.
* The hand clips belong to the shotgun class, and in them the left hand is 0.9 cm from this
  gun. `[hand_pose]` gives each clip the gun's pose clip, `fp_050_80BBD62D_add` (see "The
  left hand on the gun").

## The Huckleberry

The set file is `sets/the_huckleberry.toml`, with the template `combatrifle`. The commands
are those of The Chaperone with the name "The Huckleberry". The extraction writes one
first-person file, with 76 bones and 116 clips. The weapon tags are those of the submachine
gun, and the reload is a clip of this gun.

| Fallout 4 clip | Source |
| --- | --- |
| `WPNIdleReady` | `idle`, the first choice, `fp_052_80BC118C`, 96 frames |
| `WPNIdleReadyA` to `D` | `idle`, the second and the third choice, `fp_058_80EF5690`, 35 frames |
| `WPNIdleSighted`, `WPNIdleSightedWobble` | `iron_sight_idle`, `fp_059_80BC1193`, 98 frames, with the move of `[sight]` |
| `WPNFireSingleReady`, `A`, `B` | `fire`, `fp_049_80BC1189`, 26 frames |
| `WPNFireSingleSighted` | `iron_sight_fire`, `fp_060_80BC1194`, 19 frames, with the move of `[sight]` |
| `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack` | Automatic fire from `fp_049_80BC1189` (`[auto]`) |
| `WPNFireAutoSighted` | Automatic fire from `fp_060_80BC1194` (`[auto]`) |
| `WPNEquip`, `WPNEquipFast` | `ready`, `fp_057_80BC1191`, 30 frames |
| `WPNUnEquip` | `put_away`, `fp_056_80BC1190`, 4 frames, and the last pose on 8 more frames |
| `WPNReload` | `reload_empty` and `reload_full`, `fp_105_80EF5694`, 91 frames (a clip of The Huckleberry), with the gun parts of `fp_103_80EF5692_add` |
| `WPNSprint` | Motion of the vanilla sprint clip relative to its own first frame, on Destiny's sprint pose (`fp_055_80BC118F`, one pose) |
| `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNJumpImpactLand`, `WPNIdleGunDown` | Weapon motion of the vanilla combat rifle clip, on the Destiny hold pose or sighted pose |

* This gun's rig has 76 bones, among them the gun bone and three parts. But each hand clip
  (the idle, the shot, the reload) has 77 nodes. It belongs to a rig with four gun parts,
  and its raw tracks have four parts after the gun bone, at other rest places. The extracted
  file has the gun bones of these clips in the wrong place. The gun bone is at the world
  origin, not in the hand, and a render of the file shows the hands with no gun. Most of
  this file's clips with 76 nodes have the same fault. Only 2 of the 59 full-pose clips have
  the gun in the hand. In those 2 clips, and in every full-pose clip of the three other guns
  that has the node count of its rig (32, 66 and 23 clips), the gun bone is on the right
  hand's grip bone, `b_r_grip`, with no offset. So `[gun] rest = true` puts the gun there in
  every clip, with each part at its rest place.
* The motion of the parts is in a second clip, `fp_103_80EF5692_add`, an additive clip with
  76 nodes and the same frame count as the reload. `[gun.parts]` gives each part its motion
  from that clip, relative to the clip's first frame, on its rest place. The barrel housing
  (`bone_B36093C2`, `WeaponBolt`) goes 7.1 cm forward from frame 3 to frame 61. Those are
  the frames in which the left hand is away from its place on the gun, so the two clips are
  one reload. The magazine, `b_magazine`, comes out at frame 8, turns, and is back in place
  at frame 31. Then it turns around twice below the left hand, in frames 39 to 62.
* The additive clip of the shot moves only `bone_D7A79DD5`, which has no vertex, so the gun
  parts do not move in a shot.
* The glass of the sight has a border, four marks and a reticle. The center between the left
  and right marks is at z 9.59. In Destiny's clip in the sights the eye is at z 10.34, so
  each clip in the sights moves 0.75 units up.
* In the hand clips the left hand has the pose of the class, and its wrist is 2.5 cm from
  where a clip of this gun has it. `[hand_pose]` gives each clip the gun's pose clip,
  `fp_090_80BC11A5_add` (see "The left hand on the gun").

## The left hand on the gun

Most hand clips in a first-person file belong to the weapon class. Their left hand is posed
for the class's gun and does not hold every gun of the class. With these clips the left hand
of The Chaperone did not touch the gun in the game, with its nearest vertex 1.0 cm away, and
the left hand of The Huckleberry was not at its place on the magazine. The retarget was
correct, since the Destiny hand in the file is the same distance away, 0.9 cm.

A gun's file also has short additive clips, 2 or 3 frames of offsets only, that no state of
the graph names. Some of them hold one pose, an offset for the left wrist and for each joint
of its fingers. With the right one, the left hand is on this gun.

| Gun | Pose clip | Its offsets |
| --- | --- | --- |
| The Chaperone | `fp_050_80BBD62D_add` | The left wrist moves 2.7 cm to the rear and 0.9 cm up, and turns 19 degrees. The fingers close (the second joint of the index finger turns 57 degrees). |
| The Huckleberry | `fp_090_80BC11A5_add` | The left wrist moves 1.4 cm to the front, 1.8 cm down and 1.1 cm to the left, with other finger angles. It is the difference between the idle and `fp_093_80BC11A8`, a clip of this gun with one pose and with the gun in the hand. |

```sh
M=data/destiny/port/extract/the_chaperone/manifest.json
./port destiny pose $M --list                    # each short additive clip with its offsets
./port destiny pose $M --measure --pose 80BBD62D --hold fp_002_80BBD611:0
./port destiny pose $M --pose 80BBD62D --hold fp_002_80BBD611:0 \
    --clip fp_002_80BBD611 --clip fp_012_80BBD61B ...             # each clip of the set file
```

`--measure` prints the distance from each Destiny hand to the gun without and with the pose
clip. The last command writes `extract/NAME/posed/CLIP.npz` for each clip, with the tracks
of every bone after the pose clip's offsets. The program adds the offsets to the rig's
controls and solves the rig again with the extraction's decoder. Only the left hand and its
fingers get the offsets (`--bones`), and the left arm follows the wrist.
`[hand_pose] folder = "posed"` in the set file makes `tools/d2bake.py` read these tracks
instead of the file's clip. For The Huckleberry the command also takes `--gun-on-grip`, the
rule of `[gun] rest = true`.

A frame gets the offsets with a weight. It is 1 while the left wrist is less than 3 cm from
its place in the hold pose, measured in the space of the gun, and 0 beyond 8 cm. So the hand
has the pose only while it is on the gun. That is every frame of an idle or a shot, the
first 4 frames of The Chaperone's `reload_enter`, no frame of its shell clip, and 30 of the
91 frames of The Huckleberry's reload.

`check/touch.py` measures the result. The table shows, for the hold pose, the percent of
left-hand vertices nearer than 0.5 cm to the gun, and in parentheses the percent nearer than
1.5 cm.

| Gun | Destiny hand, before | Destiny hand, with the pose clip | Fallout 4 hand, before | Fallout 4 hand, with the pose clip |
| --- | --- | --- | --- | --- |
| The Chaperone | 0.0 % (2.2 %); the nearest vertex is 0.90 cm away | 1.7 % (14.0 %) | 0.0 % (2.0 %); the nearest vertex is 1.02 cm away | 5.2 % (22.0 %) |
| The Huckleberry | 14.9 % (38.7 %) | 19.8 % (50.2 %) | 12.4 % (41.2 %) | 20.9 % (62.3 %) |

The right hand has 32 % (72 %) on The Chaperone and 21 % (48 %) on The Huckleberry, and the
pose clip does not change it. The three earlier guns do not have this fault. With the file's
clips the left Fallout 4 hand has 5.6 % (22.3 %) on the Khvostov, 5.1 % (11.7 %) on
Hammerhead and 10.6 % (46.7 %) on The Last Word. The left hand of The Chaperone holds the
gun with its thumb on the left side of the barrel cover and its fingers below it. The palm
does not touch. `validation/NAME/hand_distance.txt` has the values for each clip of The
Chaperone and The Huckleberry, and `validation/NAME/left_hand_before_after.jpg` shows the
hold pose in the game. The values for the three earlier guns come from runs of
`check/touch.py` on the hold pose in the first chat (2026-10-06). No file stores them.

The second solve of the rig changes the left hand, its fingers and the left arm. The matrix
of every other bone changes by at most 0.0008 in the hold clip, which is rounding. The
third-person clips of the two guns were made again, because the step `third` uses results of
the first-person steps. Their bytes changed, but the line pictures of the source above the
result, `third_person_source_result.png`, are the same files as before, byte for byte.

The extraction does not say which state uses a pose clip, so the pose clip is a choice, and
the measurements made it. For The Chaperone the second candidate, `fp_035_80BBD626_add`, has
the same offsets with the opposite sign, and with it the hand is 1.0 cm from the gun.

## The M77 of Marathon

The set file is `marathon/port/sets/m77_omnipositor.toml`, with the template `combatrifle`.
The weapon is from the game Marathon, which has a later version of the Destiny 2 engine. Its
file comes from the tools of `marathon/`, not from `./port destiny extract`.
`marathon/README.md` has the extraction, and `marathon/port/README.md` has the commands of
the port.

```sh
./port marathon extract "M77 Omnipositor" --art "M77 Assault Rifle" \
    --hands data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
./port destiny convert data/marathon/extract/out/m77_omnipositor/m77_omnipositor_first_person.glb \
    --set marathon/port/sets/m77_omnipositor.toml -o /path/out
```

The first-person file has the form of a Destiny 2 file (91 bones, 68 clips of the arms and
10 clips of the weapon), and `d2fo4.py` reads it unchanged. Marathon's rig is the Destiny
rig, with the same bone names, the same bone axes (a bone points along its local Z and bends
about its local Y), the camera bone `b_utility` at the same place, and the gun bone on
`b_r_grip` in every clip (0.0000 m). The weapon tag is `rifle`.
`marathon/out/m77_omnipositor/states.json` has the clip of each state.

| Fallout 4 clip | Source |
| --- | --- |
| `WPNIdleReady`, `A` to `D` | `idle` (stand), `fp_049_80A5E5CA`, 97 frames |
| `WPNIdleSighted`, `WPNIdleSightedWobble` | `iron_sight_idle`, `fp_012_80A5E5B1`, 97 frames (one pose), with the move of `[sight]` |
| `WPNFireSingleReady`, `A`, `B` | `fire`, with its three clips `fp_113_80A5E849`, `fp_114_80A5E6A5` and `fp_019_80A5E641`, 15 frames each |
| `WPNFireSingleSighted` | `iron_sight_fire`, `fp_020_80A5E66F`, 14 frames, with the move of `[sight]` |
| `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNFireAutoSighted` | Automatic fire from `fp_113_80A5E849` and `fp_020_80A5E66F` (`[auto]`) |
| `WPNEquip`, `WPNEquipFast` | `ready`, `fp_004_80A5E847`, 22 frames |
| `WPNUnEquip` | `put_away`, `fp_003_80A5E6E8`, 12 frames, and the last pose on 3 more frames |
| `WPNReload` | `reload_empty` and `reload_full` for an empty gun, `fp_088_80A5E82E`, 104 frames, with the gun parts of `weapon_000_80A5E484` |
| `WPNSprint` | Motion of the vanilla sprint clip relative to its own first frame, on Marathon's sprint pose (`fp_005_80A5E863`, one pose) |
| `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNJumpImpactLand`, `WPNIdleGunDown` | Weapon motion of the vanilla combat rifle clip, on the Marathon hold pose or sighted pose |

* A clip of the arms does not move the gun parts. The weapon entity has its own clip for
  them, and Marathon plays the two together. The file has the weapon's clips on the same
  skeleton, named `weapon_NNN_TAG`, and `[gun.parts]` gives the reload its parts. The
  lengths give the pair, 104 and 105 frames. The reload of a gun with rounds has 72 frames,
  as does a second clip of the weapon. The pictures agree. The left hand has the magazine in
  every frame in which it is out.
* The reload is that of an empty gun. The bolt is 3.15 units to the rear from the first
  frame, and the left hand pulls the bolt handle at frame 76. The bolt has no mesh, since
  the body of the gun is one rigid mesh in Marathon, so only the events show it: the sound
  `BoltOpen` at frame 76, from `[events]`, and `BoltClose` at frame 82. The magazine gives
  `MagOut` at frame 15, `MagIn` at frame 58 and `reloadComplete` at frame 60.
* The gun has iron sights. The sight unit has two named points, 27.2 cm apart at one height,
  and I read them as the aim point and the eye point. The first one is `point` of `[sight]`,
  (0, 0.49, 7.62), the top of the front post. In the clip in the sights the eye is at z
  11.18, so each clip in the sights moves 3.56 units up. Marathon aligns the sight at run
  time, as Destiny does.
* The hands use `knuckles = "align"`. Marathon's hand bone is at another place in the hand.
  The forearm is 1.2 cm longer and the palm 0.7 cm shorter than in Destiny. With the two
  wrists at one place, the knuckles of the Fallout 4 hand are 1.42 units from the source
  knuckles, against 0.50 for Destiny, and the thumb root is 0.64 units away. With `align`
  the wrist moves 1.02 units, to the middle of the two, and each is then 0.41 units away.
  The mean distance of a fingertip to its place went from 1.06 to 0.64 units.
* A closed finger needs `closed_fingers = true`. In the reload the left index finger is a
  hook on the bolt handle, in frames 74 to 83. Every point of the source finger was nearer
  to the Fallout 4 knuckle than the first finger bone is long, so the rule of the source
  line put that bone on the line behind the fingertip, and the finger pointed at the wrist.
  That was a turn of 170 degrees in one frame, and the user saw it at frame 78. With the new
  rule a closed finger keeps the bends of its last two bones, with its tip at the source
  fingertip, and the knuckle takes the difference. The code is `finger_path` in
  `tools/blender/d2solver.py`. The largest distance of a fingertip to its place in the
  reload went from 6.20 to 2.15 units.
* The five Destiny ports do not have these two rules. After the tools changed, every pose
  file of the five sets equals the file from before (largest difference 0.0).
* `marathon/m2x_extract.py` writes each Marathon material as a Destiny 2 texture set, so
  `tools/d2model.py` reads it unchanged and with no dyes. See "The materials" in
  `marathon/README.md`.

What is proved, with the files in `validation/m77/` and the list in `mod/M77/README.md`:

* `summary.txt` has the numbers of each clip. The gun is at most 0.0102 units from the
  source gun. No finger joint bends back. The first joint of a thumb does, by 3.3 to 4.9
  degrees in the reload and 3.5 degrees in the put-away. The largest finger turn in one
  frame that the source does not have is 0.0 to 2.5 degrees in 6 clips, 11.2 and 11.7
  degrees in a shot clip and in the put-away, and 61.8 degrees in the reload. That last one
  is at frame 83, where the hand lets the bolt handle go and the source finger turns 92
  degrees.
* `reload_bolt_handle_frames.jpg` shows the left hand on the bolt handle in frames 74 to 84,
  the source above the result, from three sides.
* The game test ran 40 ops, 0 failed (`game_test.mp4`, `game_test.log`, `game_frames.jpg`,
  `game_reload_frames.jpg`). In the sights the top of the front post is at the center of the
  picture (`game_sights_center.jpg`).

For what is not correct or not done, see `mod/M77/README.md`. The main points:

* The model is that of the base item `M77 Assault Rifle`.
* Three pieces are gray, because Marathon calculates their colors at run time.
* The hand measurements are those of the Destiny hand mesh.
* There is no third-person clip of Marathon.
* There is no comparison with Marathon, because the game was not started.

## The keys of a set file

| Key | Meaning |
| --- | --- |
| `template` | The template weapon, `templates/NAME.toml`. |
| `knuckles` | `"align"` moves each wrist of the Fallout 4 rig until the thumb root and the mean of the four knuckles are at the same distance from those of the source hand (`knuckle_shift` in `tools/blender/d2solver.py`). Use it for a rig whose hand bone is at another place in the hand than Destiny's, such as the M77 of Marathon. Default: each wrist is at the source wrist. |
| `closed_fingers` | With `true`, a closed finger (a hook on a handle, a fist) keeps the bends of its last two bones, with its tip at the source fingertip (`finger_path` in the same file). Default: each joint is on the line of the source finger. |
| `hold`, `sighted` | Each is `CLIP:FRAME`. `hold` is the hold pose, which gives the place of the gun and is the pose `ready`. `sighted` is the pose in the sights. |
| `[poses]` | More named poses for `[synth]`, such as `sprint = "CLIP:FRAME"`. |
| `[roles]` | The kind of a weapon bone of the file that `tools/d2rig.py` does not have, such as `bone_68719972 = "bolt"`. The template gives each kind its Fallout 4 bone. |
| `[bones]` | The Fallout 4 bone of a weapon bone of the file, with no kind, such as `bone_9EE2ED5C = "WeaponOptics1"`. The template must have that bone. |
| `part_rest` | With `"hold"`, the rest place of each part is its place in the hold pose. Default: its place in the bind pose of the file. |
| `[auto]` | Automatic fire. Fallout 4 clip = the clip of one shot of the file. The clip has the length and the events of the vanilla clip with the same name, and the shot starts again at each event `weaponFire`. |
| `[clips]` | Fallout 4 clip = clip of the file, or a clip of `[compose]`. |
| `[gun]` | Rules for the gun bones of every clip of the file, applied by `tools/d2bake.py`. `rest = true` puts the gun bone on the grip bone of the right hand and each part at its rest place, as for The Huckleberry. In `[gun.parts]`, `CLIP = "CLIP2"` makes the gun parts of CLIP move as they do in CLIP2, against the first frame of CLIP2, on their rest place. |
| `[hand_pose]` | `folder = "posed"` names the folder, beside the file of the gun, with the tracks of `tools/d2pose.py` (`CLIP.npz`). A clip with such a file has these tracks in place of its own. They are the clip with the offsets of a pose clip of the gun on the left hand. See "The left hand on the gun". |
| `[compose.NAME]` | A new clip NAME. `clips` is a list of clips of the file, one after the other, and `"CLIP*3"` is three times the clip. The first frame of a clip is on the last frame of the clip before it. `blend` is the count of frames in which a difference between the two poses goes to zero. `cut` lists the bones with no such blend. |
| `[piece_events]` | `CLIP = [[FRAME, "TEXT"], ...]` gives the events of a clip when it is a part of a clip of `[compose]`. Each use gives its events, and a frame less than zero is before the clip. A Fallout 4 clip from a clip of `[compose]` has these events and those of `[events]`, and none from the motion of the parts. |
| `[events]` | More events of a clip, as `NAME = [[FRAME, "TEXT"], ...]`. `{sound}` is the sound name of the template. |
| `[hold_end]` | `NAME = COUNT` puts the last pose of a clip on COUNT more frames at its end. |
| `[sight]` | `point` is the aim point of the sight in Fallout 4 weapon space. `clips` lists the clips of the file in the sights. Each one gets the move that puts the point on the view axis in its first frame. |
| `[synth]` | Clips with vanilla weapon motion. `NAME = "ready"` or `"sighted"` takes the motion of the vanilla clip NAME against the vanilla ready (or sighted) pose and puts it on that pose of the file. `NAME = { pose = "sprint", reference = "wpnsprint" }` puts it on the pose of `[poses]`, against the first frame of the vanilla clip `reference`. |
| `[static]` | `NAME = { pose, vanilla, frame, frames }` puts one weapon place of a vanilla clip on every frame. |
| `[third]` | The third-person clips, from the step `third`. "The third-person clips" says why each key is there. `folder` is the folder with the files of `tools/d2third.py`, beside the file of the gun or else a path below `data/destiny/port/`. Default `third_person`. `gun` is `"stance"` (default) or `"source"`, and with `blend` (frames) it says where the gun is. `right_hand` is `"hold"` (default, the grip of the first-person hold pose) or `"source"`. `align` lists the weapon bones whose first motion gives the count of frames between the events of the first-person clip and of this clip. Default: the bolt of the template. `[third.clips]` is Fallout 4 clip = state file. `[third.poses]` is Fallout 4 clip = `CLIP:FRAME`, one pose of a third-person clip. `[third.events]` has more events, as `[events]`. `[third.compose.NAME]` and `[third.piece_events]` work as `[compose]` and `[piece_events]`, with state files. `[third.parts]` is state file = the first-person clip that gives the motion of the gun parts. `[third.hold_end]` adds frames of the last pose. `silent` lists the clips with no sound event. `[third.power_armor]` is Fallout 4 clip = the vanilla clip of the power armor that is copied under that name. |
| `[model]` | The model of the gun for the esx project. Its keys are `name`, `muzzle`, `[model.materials]`, `dyes` (the dyes file of the gun), `[model.shaders]` (NAME = the dyes file of a shader), and the texture weights `specular` (default 0.9) and `occlusion` (default 0.5). |
| `[model.materials]` | `TAG = "Name"` gives the name of the Fallout 4 material and of its textures for one material of the file. TAG is the tag of the texture set. That is `plate_set` of each mesh in `manifest.json`, and the start of the file names in `textures/`. `80EF39D0 = "Barrel"` gives `Barrel.bgsm` and `Barrel_d.dds`. A material with no line has its tag as its name. |
| `[model.sight]` | The glass of the sight and the reticle, as a second part of the weapon. Its keys are `file` (the file of `tools/d2reticle.py`), `source` (its entity), `template` and `template_shapes` (the vanilla mesh with the two effect shaders), `glass_scale`, and `texture_format` (default `bc7`). `[[model.sight.glass]]` is one table for each glass material, with `material`, the colors `red`, `green`, `blue`, and `alpha` (default 1). `[model.sight.reticle]` has `material`, `texture`, the colors `red`, `green`, `blue`, `alpha`, `limit`, `brightness`, `center` (its place on the glass), `distance` and `eye` (its size), `scale`, `gap`. |

## What you need

`./port doctor` checks each of these things and says how to make what is missing.

* Python 3.11 or later with `numpy`. The model and the picture programs also need `Pillow`.
* Blender 4.5. The setting `blender` names the program, in `data/config.toml` or in the
  environment variable `BLENDER`. The default is `blender` in the `PATH`. It runs with no
  window.
* `fnv/` of this repository (the tools of `fnv-fo4-port`) with its rig folder
  `data/fnv/rig/`. `./port fnv make-rig --nvcs /path/to/NVCS/Skeleton.nif` makes the
  skeleton, and `./port fnv make-rig --arm-meshes` makes the arm meshes that the check
  programs read. The environment variable `PORT_RIG` names another rig folder.
* The clips of the template weapon in `rig/` (`data/destiny/port/rig/`). They are game
  files, so make them once from your own files, found through the setting `fo4_data` or
  `--data`:

  ```sh
  ./port destiny make-rig
  ```

* `rig/d2_hands.json` (`destiny/port/rig/d2_hands.json`), the measurements of the Destiny
  hand mesh against the Fallout 4 hand mesh. The file is in git.
  `./port destiny measure-hands FILE.glb` makes it again in 70 seconds, as
  `data/destiny/port/rig/d2_hands.json`. Copy that file to `destiny/port/rig/` when the
  measurements must change.
* `esx` for the model and the game test, through the setting `esx` or `ESX_BIN`. The five
  programs that read the Destiny 2 packages, `states`, `dyes`, `reticle`, `third` and
  `pose`, need the `d2x` environment, which `./port destiny setup` makes.

## The steps

`./port destiny convert FILE.glb --clip ... STEP ...` runs only the steps that you name.

| Step | What it does |
| --- | --- |
| `bake` | Evaluates each clip on the bones of the file (80 for The Last Word, 76 for the Khvostov, 87 for Hammerhead) and writes the bone matrices in Fallout 4 world space (`tools/d2bake.py`). |
| `parts` | Puts the gun meshes into Fallout 4 weapon space, each on its weapon bone (`tools/d2parts.py`, `work/NAME/parts.json`). |
| `retarget` | Moves each pose to the Fallout 4 first-person skeleton, in Blender (`tools/blender/d2retarget.py`, `d2solver.py`). It also makes the clips with vanilla weapon motion, and gives a clip in the sights the move of `[sight]`. |
| `hkx` | Writes the HKX clips with their events, and reads each one again to compare it with the poses (`tools/d2hkx.py`). The rotations have 48 bits, as in every vanilla clip. |
| `install` | Copies the clips into the output folder. |
| `third` | Not in "all steps", so name it. Retargets each clip of `[third]` to the Fallout 4 third-person skeleton (`tools/blender/d3retarget.py`), writes the HKX clip and copies it into the folder of `--third-output`. It needs the results of the steps `parts`, `retarget` and `hkx`. |

## What the conversion does

* The file has +Y up, +Z forward and +X to the left, in meters. Fallout 4 has +Z up, +Y
  forward and +X to the right, in game units. The scale is the true scale, 1 m = 69.99125
  units. At this scale the upper arm and the forearm of the two rigs have the same lengths
  to 6 percent and the palm (wrist to knuckle) to 5 percent, and the two hand meshes have
  the same size. The finger bones match less well. The first bone of the ring finger is 22
  percent longer in the Destiny rig, and the finger rules are there for that.
* The camera is the bone `b_utility`, the first-person eye point. Its rest place, (0, 1.66,
  0), goes where the Fallout 4 camera bone is, and that bone follows the motion of
  `b_utility` in the clip, 2.9 units in the reload. So the picture from the Fallout 4 camera
  is the picture from the Destiny camera.
* A Destiny bone points along its local Z, +Z on the right side and -Z on the left, and
  bends about +Y. A Fallout 4 bone points along +X and bends about -Z for a finger or +Z for
  an elbow. `tools/d2rig.py` has a constant matrix for each source bone that converts one to
  the other. The values come from the clip data of the two rigs, not from an assumption.
* The two hand bones do not point the same way in the hand. A fit of the palm skin of the
  two hand meshes gives one more constant rotation, 9.3 degrees, the same value mirrored for
  the two hands. With it the distance between the two skins goes from 0.73 to 0.35 units.
  Each wrist is at the source wrist.
* There is no arm solve. The forearm lies on the source forearm and the upper arm is
  parallel to the source upper arm, so the shoulder is at most 1.7 units from the source
  shoulder, and it is out of view. The file has no data for the twist bones, so they follow
  the rule of the vanilla clips: `ForeArm2` and `ForeArm3` have 1/3 and 2/3 of the twist of
  the hand, and `UpperTwist1` and `UpperTwist2` have -2/3 and -1/3 of the twist of the upper
  arm.
* The fingers use the rules of `fnv-fo4-port` unchanged: each joint on the line of the
  source finger, the skin center of the Fallout 4 finger on the skin center of the source
  finger (`skin_center`), a least bend for each joint (`min_bend` 0.3), and the collision
  with the gun parts with its time filter.
* The rule "one plane for each finger" is new (`--planar on`). The Fallout 4 palm is 0.8
  units wider than the Destiny palm, so the knuckles are at different places, and the
  collision step moves a joint in any direction. With the joints on the source line only,
  the joint after the knuckle turned sideways by 20 to 38 degrees, which a finger cannot do
  and no vanilla clip has. Now each finger lies in the plane through its knuckle and the
  source fingertip that is nearest to the plane of the source finger. The knuckle takes the
  sideways turn, the two other joints are hinges, and the fingertip is at its place.
* A Destiny first-person clip has useful poses of the arms and the weapon only. Every other
  bone takes its pose from the first frame of the template weapon's ready clip.
* The gun is rigid-skinned, with one weapon bone for each vertex. Its grip point, the middle
  of the first joints of the right index and middle fingers in the hold pose, goes on the
  grip point of the template weapon. Each part follows its Destiny bone exactly:

  | Destiny bone | Part | Fallout 4 bone |
  | --- | --- | --- |
  | `b_handle` | frame, barrel, grip | `Weapon` |
  | `b_release_1` | crane | `WeaponMagazine` |
  | `b_release_2` | yoke (it slides on the crane) | `WeaponMagazineChild2` |
  | `b_chamber` | cylinder | `WeaponMagazineChild1` |
  | `b_ammo` | rounds | `WeaponMagazineChild5` |
  | `b_hammer` | hammer | `WeaponExtra1` |
  | `b_trigger` | trigger (no mesh of its own) | `WeaponTrigger` |
  | `b_release_button` | cylinder latch (no mesh of its own) | `WeaponBolt` |

  `work/NAME/parts.json` has each shape of the gun in the space of its Fallout 4 bone, with
  texture coordinates. A Fallout 4 model of the gun must have its shapes at these places.
* The events of a reload come from the motion of the parts: `ReloadBoltOpen` when the crane
  leaves its place, `ReloadMagIn` when the rounds are back in the cylinder,
  `ReloadBoltClose` when the crane is back, `reloadComplete` 2 frames later, and
  `initiateStart` and `reloadEnd` when the left hand is back. The sound names are those of
  the vanilla .44 revolver.

* Every spline clip of the vanilla pistol, revolver and submachine gun folders has 48-bit
  rotations. The writer of `fnv-fo4-port` asks for 40-bit rotations, with steps of 0.04
  degrees. Over the seven bones from the collarbone to the weapon, that made a noise of 0.03
  to 0.09 units at the muzzle from frame to frame, more than the motion of the idle clip. So
  `tools/d2hkx.py` gives the writer the game's format. The function can write both formats,
  and the file of that repository does not change. The error of the gun against the source
  went from 0.15 to 0.009 units.

## The weapon for Fallout 4

`mod/TheLastWord/` is the esx project `data/mods/TheLastWord/`, with its hand-written files
in `mods/TheLastWord/`. `esx build` makes `TheLastWord.esp`, `TheLastWord - Main.ba2` and
`TheLastWord - Textures.ba2` in `mod/TheLastWord/build/release/`.

```sh
SET=destiny/port/sets/the_last_word.toml
./port destiny convert FILE.glb --set $SET -o data/mods/TheLastWord/behavior/thelastword/animations/first_person
./port destiny model FILE.glb --set $SET --mod TheLastWord
./port mod build TheLastWord
```

`./port destiny model` reads `work/the_last_word/parts.json` (`--parts`) and the setting
`fo4_data` (`--data`), and writes into `data/mods/NAME/`. `--mod NAME` gives the name, and
the default is `name` of `[model]`. `./port mod build NAME` copies the files of `mods/NAME/`
into `data/mods/NAME/` and runs `esx build` there.

* `tools/d2model.py` writes the model file of the gun,
  `meshes/Weapons/TheLastWord/TheLastWord.glb`, which the build makes the mesh from, along
  with its job file, 12 textures and 4 materials. The model has the shapes of the parts
  file, each below the node of its Fallout 4 weapon bone, and the node `ProjectileNode` at
  the bore, from `[model]`.
* The textures come from the three files of each Destiny texture set and from the dyes of
  the gun (see "The dyes and the shaders of Destiny"). `_d` is the base color, `_n` is the
  normal map, and `_s` has the specular value in red and the smoothness in green. Each
  material is the material of the vanilla .44 with these textures.
* `items/10-thelastword.toml` is the weapon, a copy of the vanilla .44 with a capacity of 8,
  one receiver part that has the whole gun, no flag `Bolt Action`, and a recipe at the
  chemistry station. The ammunition, the sounds and the third-person clips are those of the
  .44.
* `behavior/thelastword/thelastword.bhv` gives the weapon its own animation keyword and
  graph copies with `weapon TheLastWord like Anims44`, and puts the 24 clips first in the
  folder list. A clip that the project does not have is the vanilla .44 clip.
* See `mod/TheLastWord/README.md` for the checks and for what is not proved.

`mod/Hammerhead/` is the project of Hammerhead. It has the records of the Khvostov project,
with other names and a capacity of 60, and `sets/hammerhead.toml`. It has three more
receiver parts for the shaders and a sight part for the glass and the reticle. See
`mod/Hammerhead/README.md`. `mod/Khvostov/` has a sight part too.

`mod/Khvostov/` is the project of the Khvostov, made with the same three commands and
`sets/khvostov_7g_02.toml`. Its weapon is a copy of the vanilla combat rifle with the
automatic receiver, a capacity of 30 and one receiver part that has the whole gun. Its
behavior source is `weapon Khvostov like AnimsCombatShotgun`, because the combat rifle has
the graphs and the clips of the combat shotgun, and it puts the 27 clips first in the folder
list. See `mod/Khvostov/README.md`.

## The dyes and the shaders of Destiny

Destiny does not have the colors of every gun in its textures. A gun has three dyes, the
channels Weapon1, Weapon2 and Weapon3, and a shader item of the game gives it three other
dyes. Each dye has a primary and a secondary material: a tint, a metal value, a smoothness
range, the same three for the worn surface, and two detail textures. The game's gear shader
puts them on the gun. Each mesh part has one of the six slots, and the alpha value of the
gstack texture says what each pixel does. A pixel at 40 to 255 takes the dye, and the value
is also the wear mask. A pixel at 0 to 32 keeps the color of the albedo texture, and the
value is the metal value.

| Gun | Pixels with a dye | Default dyes |
| --- | --- | --- |
| The Last Word | 0 percent | The colors are in the albedo texture. Its dyes are locked. |
| Khvostov 7G-02 | Less than 0.1 percent | The colors are in the albedo texture. |
| Hammerhead | 93 percent of the body and of the belt, 50 percent of the sight | Black paint and steel; dark gray; red metal and silver metal |

```sh
D=data/destiny/port
./port destiny dyes "Hammerhead" -o $D/extract/hammerhead/dyes.json                # the default dyes
./port destiny dyes "Hammerhead" --shader "Golden Trace" \
    -o $D/extract/hammerhead/dyes_golden_trace.json                               # the dyes of a shader item
./port destiny dyes --list "Trace"                                                 # find shader items
```

* `tools/d2dyes.py` reads the dyes from the game packages: the values of each dye, its two
  detail textures, and the dye slot of each mesh part. Its text says how this game build
  stores them. The extraction tool reads the dye indexes of an item and does no more with
  them.
* `tools/d2shade.py` does the gear shader for each pixel of the textures. Its formula is
  that of the public shader `DeltaDesigns/sbox_destiny_2_gear_shader` on GitHub, a copy of
  the game's shader for a different engine. It applies the tint as an overlay on the gray
  albedo, the wear between the worn and the new material, the smoothness range, the metal
  value and the detail textures.
* `tools/d2model.py` uses it for each texture set. `dyes` of `[model]` names the dyes file
  of the gun. `[model.shaders]` names more dyes files, one per shader, and each one gets its
  own textures, materials and model file.
* Fallout 4 has no dyes, so in the esx project a shader is a second receiver part with the
  same mesh and its own textures. The player changes it at the weapons workbench.
  `mod/Hammerhead` has the default look and three shaders of Destiny: Golden Trace, Calus's
  Selected and Monochromatic.

Fallout 4 has a diffuse texture, one specular value and a gloss value for each pixel, and no
metal value. The first version of `tools/d2model.py` gave each metal pixel a specular value
of 0.7 to 0.9, and a dark metal was light gray in the game, because the reflection of the
environment was too bright. Now the specular value comes from the reflectance of the
surface, which is 0.04 for a surface that is not a metal and the base color for a metal. The
specular value is 0.9 times the square root of the reflectance's luminance, and more for a
smooth surface. A metal keeps its base color in the diffuse texture. `specular` and
`occlusion` of `[model]` change the two weights. The median specular value of the body
texture is now 0.12 for Hammerhead and 0.13 for the Khvostov.

What is proved, in `validation/materials_before_after.jpg` and
`validation/hammerhead/shaders_game.jpg`:

* The reading of the dye values fits known shaders of the game. Golden Trace has a gold
  metal on black, with tint 0.97, 0.58, 0.10 and metal 1. Monochromatic has only grays. The
  worn material of a painted surface is a bare metal.
* In the game Hammerhead is black with red and steel parts, and the three shader parts give
  it the colors of their shaders, in first person and in third person. The game attaches
  each shader part to the weapon, by `item.give` with the part.
* In the game the Khvostov is a dark worn metal, and The Last Word is darker than before.
* For The Last Word and the Khvostov the plugin and the main archive of the release have the
  same bytes as before. Only the texture archive is different. The clips did not change.

What is not correct or not done:

* The meaning of each of the 27 vectors of a dye in this game build is my reading of the
  values. The public sources have the order of a different build, with 21 vectors. 8 vectors
  have no meaning in the tools, which do not use them.
* The detail textures are placed as in the public shader, at 5 times the texture
  coordinates. The game has a second set of texture coordinates for them, which the
  extraction does not have, so the size of the detail pattern can differ from the game.
* Not done: emission (the lights of a gun), iridescence, fuzz and transmission. The three
  shaders of `mod/Hammerhead` have an iridescence value of 33, 35 or 25 on a part of their
  materials, and the default dyes of Hammerhead have none. So the colors that iridescence
  adds at a low view angle are not in the game.
* A smoothness range with a negative size gives a smoothness of 0, as in the public shader.
  The black of Golden Trace is such a case. It is not known if the game does the same.
* Fallout 4 has a white specular color, so the reflection of a colored metal such as gold or
  red has no color. The color is in the diffuse texture.
* There is no reference picture of Destiny here, so "as in Destiny" is from the dye values,
  not from a comparison of pictures. The light of the test cell gives every dark surface a
  green tint, and the vanilla .44 has the same tint there.
* The game test videos, `game_test.mp4` of each gun, are older than this change and show the
  light gray guns. `validation/hammerhead/game_test_default_shader.mp4` is a new recording
  of Hammerhead with the default shader.
* The shader parts were tested with the probe, not at the weapons workbench of the game.

## The glass of the sight and the reticle

The extraction of a gun has only the parts of the render stage `opaque`. A sight with a
glass has parts in two more stages. `tools/d2reticle.py` reads them from the game packages.
It uses the modules of `destiny/extract/d2x` and does not change them.

* `transparent` has the glass with its graphics. Each part is on a weapon bone, like the
  opaque parts.
* `reticle` has one quad at the origin, with the texture of the reticle. Its vertex shader
  puts it on the aim axis with a matrix that the game calculates.

```sh
D=data/destiny/port
./port destiny reticle "Hammerhead" -o $D/extract/hammerhead/sight.json
./port destiny reticle "Khvostov 7G-02" -o $D/extract/khvostov_7g_02/sight.json
./port destiny shader-text $D/extract/hammerhead/sight/8152996A_ps.dxbc
```

The output has the meshes and, for each material, its two shaders (`sight/TAG_ps.dxbc`,
`sight/TAG_vs.dxbc`), its textures, the values of its constant buffer, and the constants and
the bytes of the expression program that calculates more values at run time.
`tools/dxasm.py` prints the instructions of a shader. The sight of Hammerhead, the entity
`region21_8152995B`, has four parts.

| Part | Material | Content |
| --- | --- | --- |
| The reticle: a quad of 1.74 x 1.77 cm | `8152996A`, with the texture `8152B71D` (512 x 512) | A ring with a bar at each side. |
| The glass: an octagon of 3.4 x 3.9 cm, on the bone of the top cover | `81529958`, with the texture plates `81529969` of the entity | Two arcs, a line with a triangle at each side, a border, and marks at the left and at the right. |
| Three symbols of 0.2 cm at the lower edge of the glass | `8152B6AD`, the same plates | The three symbols in the corners of the plate. |
| The octagon again | `81532F58` | It reads the stencil of the picture and puts red light on some objects and on their edge. Not done. |

The rules, from the pixel shader of each material:

* For the glass, color = red x RED + green x GREEN + blue x BLUE, where red, green and blue
  are the three values of the albedo plate, and alpha = the green value of the gstack plate.
  The picture is color x alpha + scene x (1 - alpha). The expression program calculates RED,
  GREEN and BLUE from six inputs of the game, which the files do not name. The values in the
  set file are those of one state. Input 5 is at 1, so the lines are bright and the border
  shows. Inputs 0 and 4 are at 0. With them on, the border becomes bright red and the marks
  white.
* For the reticle, color = red x (1, 1, 1) + green x (2.5, 0, 0), and the picture is blue x
  color + scene x (1 - 0.5 x blue). It shows only when input 3 is 0.99 or more. I read this
  input as the fraction of the move into the sights. The files do not name it.
* The size of the reticle comes from its angle. The vertex shader puts the quad 2.25 m in
  front of the camera, so the player sees it at an angle of 0.44 degrees. The quad in the
  Fallout 4 model is on the glass, 31.2 units from the eye point of the clip in the sights,
  where the same angle is 0.24 units. The first version of this work gave the quad the size
  it has in the file as a part of the gun, 1.22 units, half the width of the glass. That
  reticle was 5 times too large.
* The reticle goes at the center of the two arcs and the two lines of the glass, at the
  texture coordinate (0.5, 0.5). That is the point (0, 13.87, 14.95) of weapon space.
  `[sight]` has this point, so the view axis of each clip in the sights goes through the
  reticle.

The sight of the Khvostov, the entity `region21_8152332A`, has three parts, each on the bone
of the gun.

| Part | Material | Content |
| --- | --- | --- |
| The reticle: a quad of 1.74 x 1.77 cm | `8152C446`, with the texture `80BC0F0D` (128 x 128) | A dot with four arcs around it. |
| The glass: 55 vertices, 4.0 x 3.4 cm | `81523323`, with the texture plates `81523328` of the entity | A red mark at the left and at the right, one mark below, and a dark edge. |
| A second glass: 1012 vertices | `8152331F`, with three textures | Dust and a mirror picture with a weight of 0.09 at most, and a dark green tint. Not done. |

* The reticle has the pixel shader of Hammerhead's reticle with other values: color = red x
  (1, 1, 1) + green x (8, 0, 0). Its vertex shader puts the quad 1.1 m in front of the
  camera. That is an angle of 0.91 degrees, or 0.41 units on the glass, 25.9 units from the
  eye point.
* For the glass, color = red x RED + a mirror picture of the scene, and the picture is color
  x a + scene x (1 - 0.5 x a), with a = the green value of the gstack plate. RED is 0.8194
  red with no alarm and 3.0 red with the alarm, the same kind of inputs as for Hammerhead.
  `alpha = 0.5` of the glass table gives this rule. The mirror picture is not done.
* The reticle goes in the middle between the two marks at the sides, at the texture
  coordinate (0.499, 0.499). That is the point (0, 8.61, 8.86) of weapon space. The connect
  point `P-Scope` is on the node `KhvostovReceiver`, because the sight is a rigid part of
  the gun.

What `tools/d2model.py` makes from `[model.sight]`:

* `meshes/Weapons/Hammerhead/HammerheadSight.glb`, with the glass and the reticle. The glass
  is one shape of 21 vertices, the octagon and the three symbols. The reticle is one quad,
  at a right angle to the weapon axis and 0.02 units in front of the glass. Only its face to
  the eye shows.
* `SightGlass_d.dds` (1024 x 1024) and `Reticle_d.dds` (512 x 512), each with alpha, in the
  format BC7, and the effect materials `SightGlass.bgem` and `Reticle.bgem`. The materials
  take no scene light, use alpha blending and do not write depth. Fallout 4 blends texture x
  scale x a + scene x (1 - a), so the reticle texture has color / 2.5 and a = 0.5 x blue,
  and its material has the scale 5.
* `HammerheadSight.template.nif`. `esx` makes no new effect shader, but it keeps the effect
  shader of a template. The template is the vanilla mesh
  `Meshes/Weapons/CombatShotgun/CombatShotgunReflexSightDot.nif` with the names and the
  texture paths of this weapon. Two of its shapes get the geometry, and its three other
  shapes go away. Each of the two shapes has its place at the center of its new geometry,
  because a template shape keeps its 16-bit vertex values, which have a step of 1/64 unit at
  20 units from the place of the shape.
* The connect point `P-Scope` on the bone `WeaponOptics1` in every model of the gun. The
  sight has `C-Scope`, and the item file has the part `HammerheadSight`, a copy of the
  standard sights of the combat rifle, in the scope slot. The game puts the sight on that
  bone, so the glass moves with the top cover in the reload.

What is proved for Hammerhead, by game tests in the cell `QASmoke` with pictures of 1280 x
720, in `validation/hammerhead/red_dot_game.jpg`:

* In the sights the center of the dot is at (639.6, 359.4) of the picture. The center of the
  picture is (640, 360).
* The dot is 4 pixels wide, in the center of the two arcs, between the two triangles of the
  lines. From the hip the dot is on the glass.
* In the reload the top cover opens, and no part of the glass stays at its old place. After
  the reload the glass is on the cover again.
* The 5 clips in the sights are new, with the gun 0.15 units higher in them. The 22 other
  clips have the same bytes as before.

What is proved for the Khvostov, in `validation/khvostov_7g_02/red_dot_game.jpg`:

* In the sights the center of the reticle is at (639.1, 359.6) of the picture.
* The reticle is 11 pixels wide, a ring with a dot in it. At this size the four arcs are one
  ring. The two red marks are at its left and at its right, and the edge of the glass is
  dark.
* From the hip and in the reload the glass and the reticle are on the sight.
* The 5 clips in the sights are new, with the gun 0.11 units lower in them. The 22 other
  clips have the same bytes as before.

What is not correct or not done:

* The colors of the glass are those of one state, and the choice of the state is mine. The
  files do not name the inputs that change them in Destiny.
* Not done: the moving grid in the glow of the glass (15 percent of the color), the change
  of the brightness of the glass with time (from 1 to 5.5, where the material has 2), and
  the red marks on objects behind the glass.
* The reticle always shows, like the dot of a vanilla reflex sight. In Destiny it shows only
  in the sights.
* The reticle is on the glass. When the gun moves in the sights, in the idle or a shot, the
  dot moves with the gun. In Destiny the dot is always on the aim axis.
* The angle of 0.44 degrees is correct for Fallout 4 only if Destiny draws the gun and the
  reticle with the same projection. There is no reference picture of Destiny here. `scale`
  of `[model.sight.reticle]` changes the size.
* At 1280 x 720 the dot is 4 pixels wide, so its ring and its two bars are one spot.
* Hammerhead has four more transparent parts, three on the body with 432 vertices and one on
  the top cover with 85 vertices. `tools/d2reticle.py` lists them. They are not in the
  model.
* The reticle of the Khvostov has an edge value of 8, which is red. In Fallout 4 its ring is
  white with a pink edge and a red glow. There is no reference picture of Destiny to compare
  it with.
* `esx render` does not draw an effect material and gives the note `SCENE_NOT_DRAWN`, so
  only a game test shows the glass.
* The sight part was tested with the probe, not at the weapons workbench of the game.

## The third-person clips

Fallout 4 has few third-person clips of its own for a weapon. For the combat rifle they are
4 files in `Meshes/Actors/Character/Animations/Weapon/CombatShotgun/Player`: the reload
`WPNReload`, a hold pose `WPNAssemblyPose`, and two shot clips that move only gun parts.
Every other third-person clip, for idle, walk, aim and shot, is a clip of the grip of the
weapon, which many weapons share. So the only third-person clip of its own that a weapon
shows is its reload.

The extraction of a gun has no third-person clip of the body. Those clips are in Destiny's
player body entity, `80BAB778`, which has one animation set with 1467 clips of 72 bones and
one graph with 332 states. `tools/d2third.py` reads them. It uses the modules of
`destiny/extract/d2x` and does not change them.

```sh
D=data/destiny/port
./port destiny third $D/extract/hammerhead/manifest.json
./port destiny third $D/extract/khvostov_7g_02/manifest.json
./port destiny third data/destiny/extract/handoff/the_last_word_v1/manifest.json \
    -o $D/extract/the_last_word/third_person
```

* A state of the graph has a tree of conditions. Dimension 3 is the weapon tags, as in the
  first-person graph. Dimension 1 is the stance, `stand` or `crouch`, stored as the FNV-1
  hashes of those two words. A leaf is a clip.
* The reload is the state `EB22859A`, the hash of the word `reload_1`. Its leaves have a
  body clip for each kind of gun, and two of the three guns have one of their own. The
  Khvostov has the clip `80BB2A1D`, 105 frames, under `rifle` / its content group. The
  machine gun has `80C0C56C`, 169 frames, under `rifle` / `machine_gun`, and that is the
  clip for Hammerhead. The Last Word has the reload of a pistol, `80BB27A5`, 127 frames.
* The body clip plays with a clip of the gun parts. The gun entity has a graph of its own,
  and its states have the same name hashes as the states of the body. So the gun-parts clip
  for a state is the leaf of that state in the gun's graph. For the three guns above it is
  the clip with the same frame count as the body clip. For a state that the gun's graph does
  not have, the gun has its parts at rest. The gun is on the bone `b_r_grip` of the body.
* The tag list of a weapon is that of the first-person clips: the content group, the tags
  above it in the tag tree, then `rifle`. The weapon type of the manifest comes after the
  content group only when the tag tree does not have it. A leaf with the stance `811C9DC5`,
  the hash of an empty word, is for every stance.
* A third-person clip moves the upper body only. The pelvis and the legs do not move in it.
* The output is `extract/NAME/third_person/reload.npz`, with the world matrix of each bone
  of the body and of the gun for each frame, and `states.json`, with each state that has a
  leaf for the weapon.

The step `third` of `d2fo4.py` makes the Fallout 4 clips, in `tools/blender/d3retarget.py`.
The two games have different bodies and stances, so the clip is the Fallout 4 stance with
the Destiny motion on it.

* The stance is the first frame of the template's vanilla third-person reload,
  `third_ready`. The pelvis and the legs keep that pose.
* The gun follows one of two rules. With `gun = "stance"`, used for the Khvostov, the gun's
  motion relative to its own first frame goes on its place in the stance, so it starts and
  ends where the vanilla clips have it. With `gun = "source"`, used for Hammerhead and The
  Last Word, the gun keeps its Destiny place relative to the right shoulder, and over the
  first and the last 8 frames it goes from the stance to that place and back. Destiny holds
  a machine gun at the hip in its reload, 19 units below the shoulder. With the first rule
  the left arm is up to 8.3 units too short for the source's hand places, and 3.7 units for
  The Last Word.
* For the left hand, each source frame moves as one body until its gun lies on the gun. The
  hand then keeps its Destiny place relative to the gun. The finger rules are those of the
  first-person retarget.
* The right hand of the source counts as on the grip while it has moved less than 4 units
  from the first frame. While it is, it takes its place and its fingers from the
  first-person hold pose, because the vanilla reload has a right hand that does not move on
  the grip. The Destiny third-person clips move the right hand 1 to 3 units on the grip and
  open its fingers. When the hand goes away, as for the charging handle of Hammerhead in 31
  of 169 frames, it follows the source.
* In the upper body, the spine, the neck, the head and the collarbones take their rotation
  from the stance, plus the turn of the source bone relative to its first frame. The arms
  are a two-bone solve from the shoulder to the wrist, with the elbow at the point nearest
  to the source elbow.
* The game puts the left hand on the bone `WeaponIKTargetL` with IK. Every vanilla clip has
  it on the left hand, 0.3 units or less away on each frame, so here it gets the matrix of
  the left hand. With this bone at its rest place, the origin of the gun, the game pulled
  the left hand to the grip. That was the fault of the first test.
* `[third.poses]` makes `WPNAssemblyPose` from the first frame of the reload. The game takes
  the place of the left hand on the gun in every third-person clip from this pose. A test
  with a wrong pose had the left hand at the grip in the idle too. With the pose from the
  reload, the left hand holds the handguard of this gun, not that of the combat rifle.
* The events are those of the first-person reload, some frames earlier or later. The shift
  is the count by which the bolt, or the parts of `align`, starts to move later in the
  third-person clip. It is +3 frames for the Khvostov, -2 for Hammerhead and 0 for The Last
  Word.

The clips go into `behavior/NAME/animations/third_person/` of a project, and `esx build`
puts that folder first in the folder list of the weapon's third-person graphs.

| | Khvostov | Hammerhead | The Last Word |
| --- | --- | --- | --- |
| Frames of the reload (first person) | 105 (105) | 169 (180) | 127 (127) |
| Clip of the gun parts | charging handle | cover, belt, charging handle | cylinder |
| `gun` | `stance` | `source` | `source` |
| Largest move and turn of the gun | 11.0 units, 50 degrees | 13.2 units, 33 degrees | 27.4 units, 68 degrees |
| Left hand against the gun: result against source | 0.0000 units | 0.0000 units | 0.0000 units |
| Largest change of a bone length | 0.0004 units | 0.028 units | 0.0004 units |
| Largest move of a collarbone for an arm that is too short | 0 | 0.08 units | 0 |
| Frames with the right hand on the grip | 105 of 105 | 138 of 169 | 127 of 127 |

What is proved by game tests in the cell `QASmoke`
(`validation/NAME/game_test_third_person.mp4`, `third_person_reload_game.jpg`, and
`third_person_source_result.png`, which has the source above the result as lines):

* The game starts `WPNReload` and `WPNAssemblyPose` of each weapon in its third-person
  graph, with 6 reloads in each test, and the reload fills the gun: 27 to 30 rounds for the
  Khvostov, 57 to 60 for Hammerhead, 5 to 8 for The Last Word. Each test has 0 failed ops.
* On the Khvostov the gun tilts up, and the left hand leaves the handguard, goes to the hip,
  comes back to the magazine and pulls the charging handle. The right hand holds the grip.
* On Hammerhead the gun comes down to the chest, the top cover opens, and the left hand goes
  to the hip and back, puts the belt in and closes the cover. The cover, the belt and the
  charging handle move as in the gun clip of Destiny.
* On The Last Word the gun goes up with the muzzle up and comes down, and the left hand goes
  to the cylinder, which swings out and in.
* After a burst the left hand is on the handguard of the gun, or on the grip for The Last
  Word.
* The first-person clips of the three weapons have the same bytes as before.

What is not correct or not done:

* Only the reload is converted. Destiny has more third-person body clips for a weapon, such
  as `ready`, `fire_1` and the sprint (`states.json` has the list). Fallout 4 has its own
  clips of the grip for these.
* The legs and the pelvis do not move. They do not move in the source, and the vanilla
  reload moves the pelvis up to 5 units.
* In third person the magazine of the Khvostov and the box of Hammerhead stay in the gun,
  because the gun clips of Destiny do not move them. The hand goes to the hip and comes back
  with nothing.
* The hand data of a Destiny third-person clip is less exact than that of a first-person
  clip. In the frames where the charging handle of the Khvostov moves, the left hand is 16
  to 27 units from its place in the first-person reload. I did not measure its distance to
  the handle.
* The rule for the right hand is a choice, the vanilla rule, not the source.
* Power armor has its own third-person reload, the vanilla clip. It is not converted.
* The clip is for every actor with the weapon, non-player characters too. The vanilla game
  has a second reload file for them, with the events `CullBone.WeaponMagazine`.
* The crouch variant of the Destiny reload is not used, because Fallout 4 has one reload
  file.
* No game test has the player moving, such as a reload while walking, and none goes frame by
  frame at the normal game speed. The pictures are from a reload at one fifth of the speed,
  and the video has one reload at the normal speed for each camera place.

### The reload of a shotgun, and a gun with no clip of its parts

The two guns of Tex Mechanica needed more rules.

```sh
D=data/destiny/port
./port destiny third $D/extract/the_chaperone/manifest.json \
    --state reload_enter --state 6C41757C=reload_loop --state chamber_1 \
    --additive reload_enter --additive 6C41757C --additive chamber_1
./port destiny third $D/extract/the_huckleberry/manifest.json
```

The Chaperone is a shotgun, and a shotgun has no state `reload_1` of its own. As in first
person, its reload is three states. `reload_enter` is the leaf `shotgun`, the clip
`80C0C54D`, 17 frames. The state `6C41757C` is one shell, the clip `80C0C54C`, 24 frames.
`chamber_1` is the leaf of The Chaperone, `80C0C804`, 38 frames, with the gun clip
`80C0EF28`, in which the gun turns once around and the lever opens.

* These three clips are additive. They have offsets only, and the game adds them to the pose
  the body has at that time. The first starts with no offset, the second starts and ends
  with the offsets of the end of the first, and the last ends with no offset.
  `tools/d2third.py` adds the offsets to one pose, the first frame of a rifle's reload (the
  leaf `rifle` of `reload_1`, the clip `80BB277E`). It uses the rule of
  `destiny/extract/d2x/anim.py` for each control of the rig: rotation = base x offset and
  translation = base + offset. In that pose the left hand is 3 cm from its place in the
  first-person hold pose of The Chaperone. The test of `destiny/extract/d2x/anim.py` for an
  additive clip does not find the last clip, because its mean offset is large. So the
  program also takes a clip whose first or last frame has no offset, and `--additive` says
  so for a state.
* `[third.compose]` makes one source for each count of shells, as `[compose]` does in first
  person, with 77, 100, 123, 146, 169 and 192 frames. The last pose of one clip is the first
  pose of the next. The difference is 0.0 cm, and 3.5 cm at the start of `chamber_1`.
  `[third.piece_events]` has the events.
* The clips need more frames at the end. The game's third-person graph, `WeaponBehavior`,
  has three triggers on the clip node of a reload, relative to the end of the clip:
  `reloadEndSlave` 0.533 s, `reloadEnd` 0.5 s and one more event 0.467 s before the end. So
  the game ends a third-person reload 15 frames before the end of the clip unless the clip's
  own event comes first. For the four other guns it does, by 3 to 11 frames. For The
  Chaperone it did not, and a game test showed the reload ending at frame 22 of the 38
  frames of `chamber_1`. `[third.hold_end]` adds the last pose on 16 more frames, and then
  the clip's event ends the reload, at 2.44 s for one shell, as the clip has it.
* The reload plays on two clip nodes. The same graph has a state machine for the gun parts,
  `WeaponSlave_StateMachine`. Its reload state and the body's reload state,
  `RifleReloadState`, share one clip node in the vanilla graph. For a reload clip with a new
  name, esx makes a new clip node for the state of the body only. So the game plays that
  clip and, at the same time, `WPNReload` on the node of the gun parts, and the events of
  both clips fire. A game test of the reload with one shell showed the sounds of the second
  and of the third shell of `WPNReload`. So each count of shells has a clip with a new name,
  `WPNReload1` to `WPNReload6`, and `silent` of `[third]` leaves `WPNReload` with no sound
  event. It has only `reloadComplete`, `initiateStart` and `reloadEnd`, for a reload that no
  rule of the behavior source selects.
* The two third-person views, the body and the body in power armor, have one graph, and esx
  builds a clip with a new name only when the two views have a file with that name. The
  tools make no clip for the skeleton of the power armor. So `[third.power_armor]` makes
  each one a copy of the vanilla reload of the combat shotgun in power armor. The copies are
  in `rig/third_power_armor/`, which `tools/make_rig.py` makes from your game files.

The reload of The Huckleberry is the leaf `rifle` / `smg` / `2214C237` of `reload_1`, the
clip `80C0C973`, 91 frames, as in first person. The gun entity of The Huckleberry has no
clip, so the file of `tools/d2third.py` has the gun with its parts at rest. `[third.parts]`
gives the gun parts, the barrel housing and the magazine, their motion from the first-person
reload, relative to the gun, frame by frame. That is a choice. The Destiny files do not say
that the parts move in third person.

The result in the game, for `mod/TexMechanica` in the test cell `QASmoke`, on a headless
test copy of the game:

* `check/game_reloads.py` did one reload of The Chaperone for each count of rounds from 0 to
  5, in each view. That is 12 reloads, 0 failed. Each one played the clip of its count, from
  `WPNReload6` for an empty gun to `WPNReload1` for 5 rounds. Each ended at the time of its
  clip's event, 7.23 s to 2.75 s in first person and 6.28 s to 2.45 s in third person. Those
  are the values of `validation/the_chaperone/game_test_reloads.txt`, and the events of the
  first-person clips are at 7.2333 s and 2.7333 s. Each filled the gun to 6 rounds, started
  one shell sound for each shell, and started the two sounds of the lever once.
* `check/game_third.py` ran 94 ops for The Chaperone, 88 for The Huckleberry and 73 for The
  Last Word, each with 0 failed ops. The reload filled the gun in each test: 3 to 6, 27 to
  30, and 5 or 6 to 8 rounds. The files are `validation/NAME/game_test_third_person.mp4` and
  `third_person_reload_game.jpg`, with 14 and 12 pictures of a reload at one fifth of the
  speed, from three sides.
* On The Chaperone the gun turns up, and the left hand goes down and comes back to the
  loading port once for each shell. Then the right hand turns the gun once around with the
  arm to the front, and the left hand comes back to the gun.
* On The Huckleberry the gun turns up, the barrel housing goes to the front, the magazine
  comes out, turns and comes back, and the left hand goes over the top of the gun.

What is not correct or not done, more than for the other guns:

* The lever of The Chaperone in a third-person reload with 1 to 5 shells. I think it does
  not open in the turn of the gun, because the node of the gun parts plays `WPNReload`, with
  6 shells, which has the motion of the lever at another time. I did not make a picture that
  shows the lever in that frame.
* The shell of The Chaperone does not show in third person, because the gun clips of Destiny
  do not move it there.
* In the turn of the gun the right arm of The Chaperone is up to 2.85 units too short for
  the place of the gun, and the collarbone moves by that length.
* The reload of a body in power armor is the vanilla clip, with the sounds of the combat
  shotgun. I did not test it. I think its sounds play twice in a reload with a new name,
  because the two clip nodes have the same events there.

## The templates

A template is a vanilla weapon. It gives the weapon bones with their rest places, the sound
names of the events, the pose of the body bones, the grip point, and the clips whose weapon
motion a set file can take.

* `templates/revolver44.toml` is the vanilla .44 revolver, `Animations/44Pistol`. Its values
  come from the vanilla clips and from `Weapons/44/44.nif`. `WeaponMagazine` is the crane,
  which turns 100 degrees in the vanilla reload. Its children are the cylinder, the ejector,
  the moon clip, the cases and the rounds. `WeaponExtra1` is the hammer.
* `templates/combatrifle.toml` is the vanilla combat rifle. It has the clips of the combat
  shotgun in `Animations/CombatShotgun` and one clip of its own in
  `Animations/CombatShotgun/CombatRifle`, so `game_clips` lists the two folders. Its values
  come from the vanilla clips and from `Weapons/CombatShotgun/CombatRifle.nif`.
  `WeaponMagazine` is the magazine, and `WeaponBolt` is the bolt with the charging handle,
  which goes 3.67 units to the rear in each shot. The reload events have the sound name of
  the combat shotgun, `reload_sound`, as the vanilla reload has. `synth_bones` names the
  bones that a clip with vanilla weapon motion moves on the gun as the vanilla clip does.
  Here that is the bolt.
* `templates/combatrifle_parts.toml` is `combatrifle`, by `base = "combatrifle"`, with the
  bones `WeaponExtra2` and `WeaponExtra3` added, for a gun with many moving parts. A
  template with `base` has every value of that template plus the values of its own file.

A template also names its third-person clips. `third_game_clips` is the folder of the game
in `Meshes/Actors/Character/Animations/Weapon`, for example `CombatShotgun/Player`.
`third_clips` is the folder in `rig/`. `third_ready` is the clip whose first frame is the
stance. `tools/make_rig.py` writes these clips and `rig/third/skeleton.hkx`, the skeleton of
the character. It has 95 bones: the 94 bones of the first-person skeleton, with the same
rest places for the body, and `CamTarget`.

`third_power_armor_game_clips` and `third_power_armor_clips` name the template's
third-person clips for a body in power armor, in
`Meshes/Actors/PowerArmor/Animations/Weapons` and in the folder in `rig/`. Only
`[third.power_armor]` of a set file uses them.

`./port destiny measure-template data/destiny/port/rig/NAME CLIP ...` prints the values for
a new template file from the vanilla clips: the rest place of each weapon bone, the bones
that each clip moves, and the grip point.
`./port destiny points data/destiny/port/work/NAME/parts.json` prints the points of a gun
that a set file needs: the muzzle, the eye point of a clip in the sights, and a map of the
sight with its window.

A reload gets its events from the motion of the parts. A template with the kind `magazine`
gets `ReloadMagOut` and `ReloadMagIn` from the magazine, `reloadComplete` 2 frames after the
magazine is in, and `ReloadBoltOpen` and `ReloadBoltClose` from the bolt. A template with no
magazine, the revolver, gets the events of the crane, the rounds and the hammer.

## Checks

The check programs make the videos and the numbers of `validation/`. They read the HKX
files, not the poses before them.

```sh
D=data/destiny/port
./port destiny check validate FILE.glb --set destiny/port/sets/the_last_word.toml --out $D/validation/the_last_word
./port destiny check validate FILE.glb --set destiny/port/sets/khvostov_7g_02.toml --out $D/validation/khvostov_7g_02 --left-hand
```

`--clips FOLDER` names the folder with the HKX clips, default `out/NAME`. `--work FOLDER`
names the converter's work folder, default `work/NAME`.

`--left-hand` is for a two-handed gun. It also makes `NAME_left_hand.mp4`, the left hand
from the side of its thumb and from its palm. `--resume` keeps the files of every clip that
has its `NAME.txt` and makes only `summary.txt` again. For a clip with the move of
`[sight]`, the videos show the source as it is, so the result is higher. The numbers compare
the result with the source after the same move, from `work/NAME/fo4/moves.json`.

Each clip of the file gets `NAME_first_person.mp4` (the first-person camera, source at the
left, result at the right), `NAME_gun.mp4` (the grip from the two sides of the gun) and
`NAME.txt` (the numbers). Each clip with vanilla weapon motion gets `NAME_first_person.mp4`
with the result only. `summary.txt` has one line per clip. The single programs:

```sh
W=data/destiny/port/work/NAME       # the work folder of the weapon
O=data/destiny/port/out/NAME        # the folder with its clips (or the animation folder of the mod project)
./port destiny check render --glb FILE.glb --clip CLIP --poses $O/WPNReload.hkx \
    --parts $W/parts.json --out DIR --template TEMPLATE --frames all --views fp,r_thumb,r_back,l_thumb,l_palm,gun_left
./port destiny check sheet DIR CLIP VIEW "0 12 24" OUT.jpg        # the source above the result
./port destiny check video DIR CLIP OUT.mp4 VIEW [VIEW2] [RATE]   # the source at the left, the result at the right
./port destiny check strip VIDEO.mp4 OUT.jpg [COUNT] [WIDTH]      # frames of a video at equal steps, in one picture
./port destiny check contact --glb FILE.glb --bake $W/bake/CLIP.npz \
    --poses $O/WPNReload.hkx --parts $W/parts.json --frames all --quiet --out contact.json
./port destiny check contact-table contact.json                   # hand vertices inside the gun, source and result
./port destiny check fingers $O/WPNReload.hkx --bake $W/bake/CLIP.npz \
    --vanilla data/destiny/port/rig/combatrifle                         # joint ranges against the vanilla clips
./port destiny check gun FILE.glb CLIP $W/parts.json $O/WPNReload.hkx   # the gun, vertex by vertex
./port destiny check touch --glb FILE.glb --bake $W/bake/CLIP.npz \
    --poses $O/WPNIdleReady.hkx --parts $W/parts.json --frames 0        # how near each hand is to the gun
./port destiny check touch-table FILE.glb --set SET.toml --clips DIR --out data/destiny/port/validation/NAME/hand_distance.txt
```

`--template` of `render` and `--vanilla` of `fingers` default to the revolver, `revolver44`
and `data/destiny/port/rig/revolver44`. Give them the template of the set file and the
folder with its vanilla clips. That folder is `data/destiny/port/rig/combatrifle` for
`combatrifle` and for `combatrifle_parts`. `check/validate.py` sets both itself.

`render`, `contact` and `touch` run in Blender. `./port destiny check render ...` is
`sh destiny/port/check/bl.sh destiny/port/check/render.py -- ...`. There are more picture
programs, for the pictures of `render` and for a video: `look-sheet` (one frame from more
views), `frame-sheet` (each frame of one view), `hand-sheet` (one hand before and after a
change, with two game pictures) and `video-sheet` (frames of a video with the time of each
one).

`check/contact.py` counts the hand vertices that are inside the gun. A hand that is 1 cm
away from the gun has none, so that check does not show a hand that does not touch.
`check/touch.py` does. For each hand it prints the distance from the nearest vertex to the
surface of the gun and the percent of vertices nearer than 0.5 cm and nearer than 1.5 cm,
for the Destiny hand of the source and for the Fallout 4 hand of the result.
`check/touch_table.py` runs it for every clip of a set file. In the hold pose of the five
guns, a Fallout 4 hand that holds the gun has 5 to 42 percent of its vertices nearer than
0.5 cm. Do this check for every new gun. If the source has 0 percent in the hold pose, the
gun needs a pose clip, as "The left hand on the gun" describes.

The game test records the game. "The game test" has the result.

```sh
esx probe status                                                    # the probe has one session at a time: look first
esx --data "/path/Fallout 4/Data" probe start --mod data/mods/TheLastWord/build/release --cell QASmoke \
    --label NAME --proton "/path/Proton" --format json             # gives the session ID
./port destiny game record --session ID --weapon TheLastWord --capacity 8 --out DIR
esx probe stop --session ID                                         # only the ID that your start command printed
```

The test of the third-person clips makes pictures of a slow reload from three sides and,
with `--record`, a video.

```sh
D=data/destiny/port
./port destiny game session Khvostov LABEL       # builds the mod, starts a session, prints its ID
./port destiny game third --session ID --weapon Khvostov --capacity 30 --record --out DIR
./port destiny check third-sheet $D/extract/khvostov_7g_02/third_person/reload.npz \
    $D/work/khvostov_7g_02/third/poses/WPNReload.npz OUT.png     # the source above the result, as lines
```

`./port destiny game session NAME LABEL`, which is `check/third_session.sh`, takes the name
of a mod. It builds the mod with `./port mod build NAME --update-lock` and starts the
session with `data/mods/NAME/build/release`. It keeps the session ID in
`data/destiny/port/work/probe_session.txt`, with its label in `probe_session.txt.label`.
When you run it again with the same label, it stops the session of that file and no other.
If the file has a session with a different label, the program stops nothing and exits with
code 1, because a second user may have started that session. `--take-over` stops it, but ask
the user first. If the probe has a session that this program did not start, it does not
start one, and its exit code is 1.

`--cell ID` gives the cell where the game starts, default `QASmoke`. `--world` gives no
cell. The game then starts in the cell of the test world of the test folder, which needs
`esx probe install --world FILE` and an esx version of 2026-10-06 or later. `--no-build`
starts the session with the release that is there, to test a release with the bytes that
were tested before. `docs/porting/game-test.md` has the rules of a game test.

The test of a weapon with one reload clip for each count of rounds, The Chaperone, does one
reload for each count in the two views, and gives the clip, the time, the rounds and the
sounds of each one.

```sh
./port destiny game reloads --session ID --weapon TheChaperone --capacity 6 --out DIR
```

More game test programs:

* `./port destiny game sight` makes pictures at the hip and in the sights.
* `./port destiny game trace` gives the clips and the events of one reload, from the trace
  of the probe.
* `./port destiny game shots` makes pictures of the gun in a slow third-person reload.
* `./port destiny game all` runs every test of every weapon of a mod in one session. Give it
  `--session ID`, because with none it takes the ID of the shared session file. `--dry-run`
  prints the commands.
* `./port destiny game results` copies the results of a weapon into its validation folder
  and prints the numbers.

`check/validate.py --no-video` makes only the numbers, `NAME.txt` and `summary.txt`. The
videos of a clip need about 10 minutes.

For an automatic weapon, use `--weapon Khvostov --capacity 30 --auto`. Each group of shots
is then a burst with the action `ActionFireAuto`. Two minutes after the start of a session
the game turns the camera about the player, because it has no input. A recording must end
before that time or start after it, since an op that sets the view ends that camera.

`esx probe start` runs a test copy of the game in a headless gamescope, with no window and
no change in the `Data` folder of the installed game. `check/game_record.py` records the
picture of that gamescope (PipeWire node `gamescope`, GStreamer, 1280 x 720, 60 frames per
second) while it sends the steps of the test to the probe. It writes `record.mp4`,
`steps.json` with each step, its time and its answer, and `trace.json` with each clip and
event of the graph. It sends no keyboard or mouse input.

The source in a picture is the file as Blender reads it, with its own skin and clip, so it
does not come from the bake of these tools. A set file with `[gun]` or `[compose]` is the
exception, as for The Huckleberry and The Chaperone. The file does not have such a clip, so
the source has the pose of `tools/d2bake.py` with those rules, and `check/gun.py` compares
with the same pose. For these two guns the checks prove the retarget, not the rules. The
result is the vanilla Fallout 4 arm meshes and the shapes of the parts file on the Fallout 4
weapon bones. The two pictures of a frame have the same camera. The mesh of the mod has the
same shapes at the same places. Each vertex of the built mesh is at most 0.008 units from
its place in the parts file.

## What is proved

For The Last Word, 24 clips. `validation/the_last_word/summary.txt` has the numbers of each
clip, and `NAME.txt` has the tables.

* Two complete runs give the same bytes for all 24 clips. The single clip form, `--clip`,
  gives the same bytes as the set form.
* In every clip the gun is where the source gun is. Each of the 5998 vertices is at most
  0.009 units away on all frames of all clips. Each wrist is at most 0.003 units from the
  source wrist. The camera bone is at the source camera.
* Every joint between two finger bones is a hinge, with no turn to the side and no twist,
  and no joint bends to the back of the finger. The 25 vanilla clips that the reader can
  read are the same.
* In every clip the Fallout 4 hands are in the gun less than the Destiny hands. Percent of
  hand vertices inside the gun, result against source: WPNIdleReady 4.9 against 8.1;
  WPNIdleSighted 5.0 against 10.4; WPNFireSingleReady 4.7 against 8.4; WPNFireSingleSighted
  5.3 against 9.9; WPNEquip 2.2 against 3.3; WPNUnEquip 5.0 against 8.1; WPNReload 5.7
  against 8.2; WPNSprint 5.1 against 10.5.
* The mesh of the mod has each shape at its place of the parts file, to 0.008 units, and
  each weapon node at its rest place of the template.
* `esx build` of `mod/TheLastWord` passes with 0 issues and 0 warnings, and the weapon,
  scene and render checks of esx have no finding. See `mod/TheLastWord/README.md`.
* The videos of `validation/the_last_word/` show the source beside the result for all frames
  of the 8 Destiny clips, and the result of the 8 clips with vanilla weapon motion.
* The mod loads in the game, and the game plays the clips. The next section has the test.

For the Khvostov 7G-02, 27 clips, in `validation/khvostov_7g_02/summary.txt` and `NAME.txt`:

* Two complete runs give the same bytes for all 27 clips. After the tools changed for this
  weapon, the 24 clips of The Last Word have the same bytes as before.
* In every clip the gun is where the source gun is. Each of the 11141 vertices is at most
  0.012 units away on all frames of the 7 Destiny clips. Each wrist is at most 0.003 units
  from the source wrist. The camera bone is at the source camera. For the clip in the sights
  the source has the move of `[sight]` in this comparison.
* Every joint between two finger bones is a hinge, and no joint bends to the back of the
  finger.
* The Fallout 4 hands are in the gun about as much as the Destiny hands. Percent of hand
  vertices inside the gun, result against source: WPNIdleReady 9.4 against 9.0;
  WPNIdleReadyA 9.2 against 9.8; WPNIdleReadyB 9.0 against 8.7; WPNIdleSighted 9.4 against
  9.1; WPNEquip 9.2 against 9.2; WPNUnEquip 8.9 against 8.1; WPNReload 8.0 against 8.3. For
  this gun the result is not better than the source, as it is for The Last Word. The left
  palm is 4.4 units deep in the handguard, against 4.9 in the source. The Destiny hand holds
  the handguard that deep, and the wrist is where the source wrist is.
* The mesh of the mod has each weapon node at its rest place of the template, each shape
  below the node of its bone, and the center of the bounds of each shape at its place of the
  parts file, to 0.01 units.
* `esx build` of `mod/Khvostov` passes with 0 issues and 0 warnings, and the weapon, scene
  and render checks of esx have no finding. See `mod/Khvostov/README.md`.
* The videos of `validation/khvostov_7g_02/` show the source beside the result for all
  frames of the 7 Destiny clips, for the camera, the grip and the left hand, and the result
  of the 16 clips with vanilla weapon motion.
* The mod loads in the game, and the game plays the clips. See "The game test of the
  Khvostov".

For Hammerhead, 27 clips, in `validation/hammerhead/summary.txt` and `NAME.txt`:

* Two complete runs give the same bytes for all 27 clips. After the tools changed for this
  weapon, the 24 clips of The Last Word and the 27 clips of the Khvostov have the same bytes
  as before.
* In every clip the gun is where the source gun is. Each of the 22683 vertices, on its 12
  moving parts and the body, is at most 0.015 units away on all frames of the 9 Destiny
  clips. Each wrist is at most 0.003 units from the source wrist. The camera bone is at the
  source camera. For the two clips in the sights the source has the move of `[sight]` in
  this comparison.
* Every joint between two finger bones is a hinge, and no joint bends to the back of the
  finger.
* The Fallout 4 hands are in the gun more than the Destiny hands. Percent of hand vertices
  inside the gun, result against source: WPNIdleReady 11.4 against 8.9; WPNIdleReadyA 10.8
  against 9.0; WPNIdleReadyB 10.8 against 8.4; WPNIdleSighted 11.4 against 8.9;
  WPNFireSingleReady 11.5 against 8.9; WPNFireSingleSighted 11.5 against 8.9; WPNEquip 11.4
  against 9.0; WPNUnEquip 10.0 against 9.5; WPNReload 9.0 against 7.7. This is worse than
  for the other two weapons. The bones that go deeper than the source, in every clip, are
  the second and third bones of the right thumb and the last bone of the right index finger.
  In the hold pose the second bone of the right thumb is 3.0 units deep in the gun, against
  1.3 in the source. The thumb is in the receiver above the grip, and you cannot see it from
  the left side of the gun. The collision step moves a finger 1.15 units at most. The right
  hand is below the view in first person, so the game test does not show this.
* The mesh of the mod builds from the parts file with 40 shapes, and `esx build` of
  `mod/Hammerhead` passes with 0 issues and 0 warnings. The weapon, scene and render checks
  of esx have no finding. See `mod/Hammerhead/README.md`.
* The videos of `validation/hammerhead/` show the source beside the result for all frames of
  the 9 Destiny clips, for the camera, the grip and the left hand, and the result of the 3
  automatic fire clips and of the 9 clips with vanilla weapon motion.
* The mod loads in the game, and the game plays the clips. See "The game test of
  Hammerhead".

For The Chaperone and The Huckleberry, 30 and 27 first-person clips and 8 and 2 third-person
clips. `validation/the_chaperone/` and `validation/the_huckleberry/` have `summary.txt`,
`NAME.txt` and `hand_distance.txt`.

* A second complete run gives the same bytes as the files of `mod/TexMechanica` for all 67
  clips. A second thread changed `d2fo4.py`, `tools/blender/d2retarget.py` and
  `tools/blender/d2solver.py` for another weapon after the clips of the mod were made. Its
  new rules are off for these sets. The second run was after those changes, with the tools
  of 2026-10-06, 19:08 local time.
* In every clip the gun is where the source gun is, with each vertex at most 0.012 units
  away. The source here is the clip after the rules of the set file, `[gun]`, `[compose]`
  and `[hand_pose]`.
* No joint between two finger bones bends to the back of the finger.
* The left hand is on the gun in the hold pose. 5.2 percent of its vertices are nearer than
  0.5 cm to The Chaperone and 20.9 percent to The Huckleberry, against 0.0 and 12.4 percent
  before the pose clip. In every clip the left Fallout 4 hand has at least as many such
  vertices as the left Destiny hand, as the mean of the frames in `hand_distance.txt`. The
  right hand on The Chaperone has 32 percent, and the Destiny hand has 35 percent.
* In the shot of The Chaperone at the hip the right hand has no vertex nearer than 0.5 cm to
  the gun in frames 12 to 21, in the source and in the result. The gun turns in the hand
  there, as the clip of Destiny has it.
* `esx build` of `mod/TexMechanica` passes with 0 issues and 0 warnings.
  `mod/TexMechanica/README.md` has the other checks of esx.
* The mod loads in the game, and the game plays the clips. See "The game test of the Tex
  Mechanica mod".

## The game test

`validation/the_last_word/game_test.mp4`, 85 s, is a recording of Fallout 4 with the mod in
the test cell `QASmoke`. `game_test.log` and `game_test_steps.json` have each step with its
time, `game_test_frames.jpg` has 9 frames, `game_test_view.jpg` has the game beside the
Blender check pictures, and `game_test_put_away.jpg` has the put-away before and after its
correction. The video time is the log time plus 2 s.

| Time in the video | Step |
| --- | --- |
| 4 s | Draw, with the spin of the gun. Then the idle. |
| 9 s, 11 s, 12 s | Three shots from the hip. The left hand fans the hammer. |
| 13 s to 17 s | Reload. The ammunition count goes from 5 to 8. |
| 19 s to 24 s | The sights, and two shots in the sights. |
| 26 s to 29 s | Gun down, then gun ready. |
| 31 s to 33 s | The sprint pose (the event of the graph, with no motion of the player). |
| 35 s, 38 s | Put away, then draw. |
| 45 s to 62 s | Reload and one shot at one quarter of the game speed. |
| 69 s to 83 s | Third person: a shot, a reload, the camera at the side of the weapon. |

What the test proves:

* The game finds the weapon `TheLastWord`, with the name "The Last Word" and capacity 8,
  loads its model with its textures, and starts its graphs `TLWGunBehavior` and
  `TLWPistol_GunWrappingBehavior`.
* The game played 13 of the 24 clips: `WPNEquipFast`, `WPNIdleReady`, `WPNIdleReadyA`,
  `WPNFireSingleReady`, `WPNFireSingleReadyA`, `WPNFireSingleSighted`, `WPNIdleSighted`,
  `WPNIdleSightedWobble`, `WPNReload`, `WPNIdleGunDown`, `WPNSprint`, `WPNUnEquip` and
  `WPNRunForwardReady`, which the graph blends into the draw. The vanilla additive clips of
  the graph, the sway of the idle and the jiggle after a shot, play on top of them.
* The events work. Each shot fires and uses one round, `reloadComplete` fills the cylinder,
  and `reloadEnd` ends the reload state.
* The gun and the right hand are at the same place on the screen as in the Blender check
  pictures. In `game_test_view.jpg` the rear sight of the idle is 10 pixels or less away in
  a picture of 960 x 540. In the sights, the rear sight and the front sight are at the
  center of the screen, and the game shows the gun a little larger because of its zoom in
  the sights.
* The hands stay on the gun in every clip, and the cylinder, the crane and the rounds move
  with the hands in the reload.
* For the put-away, see `[hold_end]` above. Before the correction the game removed the gun
  one frame before the hand moved, which the vanilla .44 in the same session did not do.
  After the correction the gun goes down with the hand, as `game_test_put_away.jpg` shows.

What the test shows, and is not a fault of the clips:

* The camera kicks at each shot. The clips do not turn the camera bone in a shot, 0.03
  degrees at most. The kick is the recoil of the weapon record, which is a copy of the
  vanilla .44, and the vanilla .44 does the same in the same session.
* A moving object leaves a row of copies behind it for some frames: the globe of the test
  cell at each shot, the gun in the reload and in the draw. Vanilla objects show it too, so
  it is the anti-aliasing of the game in the test session, not the mesh.
* The Pip-Boy on the left arm is in the view in the shot and in the reload, because the
  Destiny clips bring the left forearm far into the view.
* The top of the picture has a black and yellow area. It is there before the weapon is in
  the hand. It is the sky of the test cell in the headless session.
* The graph starts the blend from the draw clip to the idle 0.5 s before the end of the draw
  clip, at its trigger `00NextClip`, as for every vanilla weapon. The gun is ready 0.57 s
  after the start of the draw, and the last 0.5 s of the Destiny clip, where the gun comes
  back from the right, plays at a decreasing weight.

## The game test of the Khvostov

`validation/khvostov_7g_02/game_test.mp4`, 81 s, is a recording of Fallout 4 with the mod
`mod/Khvostov` in the test cell `QASmoke`. `game_test.log` and `game_test_steps.json` have
each step, `game_test_frames.jpg` has 9 frames, and `game_test_view.jpg` has the game beside
the Blender check pictures. The video time is the log time plus 2 s.

`validation/khvostov_7g_02/game_test_red_dot.mp4`, 81 s, is the same test with the sight
part and with the materials from the dyes work. The gun is a dark worn metal, and the glass
of the sight has its two red marks and its reticle, a dot with four arcs, which is at the
center of the screen in the sights, from 19 s to 24 s. `game_test_red_dot.log`,
`game_test_red_dot_steps.json` and `game_test_red_dot_frames.jpg`, with 16 frames, are
beside it, and `red_dot_game.jpg` has the sight 6 times larger. The test ran 40 ops, 0
failed. Each step is within 0.2 s of the first recording, and the same first-person clips
started. In this recording the gun is 0.11 units lower in the sights, because the aim point
is now the reticle.

| Time in the video | Step |
| --- | --- |
| 4 s | Draw. Then the idle. |
| 9 s, 12 s | Two automatic bursts from the hip (16 rounds). |
| 14 s to 17 s | Reload. The ammunition count goes from 14 to 30. |
| 19 s to 24 s | The sights, and a burst in the sights. |
| 26 s to 28 s | Gun down, then gun ready. |
| 30 s to 33 s | The sprint pose (the event of the graph, with no motion of the player). |
| 35 s, 37 s | Put away, then draw. |
| 41 s to 60 s | Reload and a burst at one quarter of the game speed. |
| 64 s to 79 s | Third person: a burst, a reload, the camera at the side of the weapon. |

What the test proves:

* The game finds the weapon `Khvostov`, with the name "Khvostov 7G-02", capacity 30 and the
  keyword of an automatic weapon, loads its model with its textures, and starts its graph
  `KHVGunBehavior`.
* The game played 14 of the 27 clips: `WPNEquipFast`, `WPNIdleReady`, `WPNIdleReadyA`,
  `WPNIdleReadyB`, `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNFireAutoSighted`,
  `WPNIdleSighted`, `WPNIdleSightedWobble`, `WPNReload`, `WPNIdleGunDown`, `WPNSprint`,
  `WPNUnEquip` and `WPNRunForwardReady`, which the graph blends into the draw.
* The events work. The weapon fires automatically while the trigger is down, 10 rounds in a
  burst of 1.0 s. `reloadComplete` fills the magazine, and `reloadEnd` ends the reload
  state.
* The gun and the hands are at the same place on the screen as in the Blender check
  pictures, in `game_test_view.jpg`. In the sights, the window of the sight is at the center
  of the screen.
* In the put-away the gun goes down with the hands. The game removes it 15 ticks, 0.125 s,
  after the start of the clip, which is after the 4 frames of the motion.
* In third person the hands of the vanilla combat rifle clips hold the grip and the
  handguard of this gun.

What the game checks found, and the corrections:

* The first check found the sight below the center of the screen in the sights. The cause
  and the correction are in "The Khvostov 7G-02", at `[sight]`.
* The build stopped with `like AnimsCombatRifle`, because that keyword has no rules for
  power armor. The behavior source is `like AnimsCombatShotgun`, and the item file removes
  the keyword `AnimsCombatRifle` from the weapon.
* The first recordings were not usable. One session was idle for more than two minutes
  before the recording, and the game was in its camera that turns about the player. The
  recording of the report is from a new session.

What the test shows, and is not a fault of the clips:

* The camera kicks at each shot. That is the recoil of the weapon record, which is a copy of
  the vanilla combat rifle with its automatic receiver.
* A moving object leaves a row of copies behind it for some frames, as in the test of The
  Last Word.
* The sight has no reticle, and the gun is light gray in the light of the test cell. The
  recording is from before the work on the dyes and on the reticle, and
  `game_test_red_dot.mp4` shows the two.
* The Pip-Boy on the left arm is in the view, because the left hand holds the handguard.

## The game test of Hammerhead

`validation/hammerhead/game_test.mp4`, 92 s, is a recording of Fallout 4 with the mod
`mod/Hammerhead` in the test cell `QASmoke`, with the same files beside it as for the
Khvostov. The video time is the log time plus 2 s.

`validation/hammerhead/game_test_default_shader.mp4`, 92 s, is the same test, recorded again
after the work on the dyes. The gun has the default shader of Destiny (black paint, red
metal and steel). Its steps have the same times, in `game_test_default_shader.log` and
`game_test_default_shader_steps.json`, with 16 frames in
`game_test_default_shader_frames.jpg`. The test ran 40 ops, 0 failed, and the same
first-person clips started as in the first recording.

`validation/hammerhead/game_test_red_dot.mp4`, 92 s, is the same test with the sight part.
The glass of the sight has its red graphics, and the red dot of the reticle is at the center
of the screen in the sights, from 21 s to 26 s, and on the glass from the hip. Its files are
`game_test_red_dot.log`, `game_test_red_dot_steps.json`, 16 frames in
`game_test_red_dot_frames.jpg`, and `red_dot_game.jpg` with the sight 6 times larger. The
test ran 40 ops, 0 failed. Each step is within 0.2 s of the recording before, and the same
first-person clips started. In this recording the gun is 0.15 units higher in the sights
than in the two recordings before, because the aim point is now the reticle.

| Time in the video | Step |
| --- | --- |
| 4 s | Draw. Then the idle. |
| 9 s, 12 s | Two automatic bursts from the hip (16 rounds). |
| 14 s to 19 s | Reload. The ammunition count goes from 44 to 60. |
| 21 s to 26 s | The sights, and a burst in the sights. |
| 28 s to 30 s | Gun down, then gun ready. |
| 32 s to 35 s | The sprint pose (the event of the graph, with no motion of the player). |
| 37 s, 39 s | Put away, then draw. |
| 43 s to 71 s | Reload and a burst at one quarter of the game speed. |
| 74 s to 89 s | Third person: a burst, a reload, the camera at the side of the weapon. |

What the test proves:

* The game finds the weapon `Hammerhead`, capacity 60, loads its model with its textures,
  and starts its graph `HMHGunBehavior`.
* The game played 14 of the 27 clips: `WPNEquipFast`, `WPNIdleReady`, `WPNIdleReadyA`,
  `WPNIdleReadyC`, `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNFireAutoSighted`,
  `WPNIdleSighted`, `WPNIdleSightedWobble`, `WPNReload`, `WPNIdleGunDown`, `WPNSprint`,
  `WPNUnEquip` and `WPNRunForwardReady`, which the graph blends into the draw.
* The events work. The weapon fires automatically while the trigger is down, 16 rounds in
  the two bursts of the recording, 1.2 s and 0.45 s long. `reloadComplete` fills the box,
  and `reloadEnd` ends the reload state.
* The 12 parts move in the game. In the reload the cover opens, the box goes away and a box
  comes in, the hand puts the belt in, the cover closes, and the right hand pulls the
  charging handle.
* The gun and the hands are at the same place on the screen as in the Blender check
  pictures, in `game_test_view.jpg`. In the sights, the window of the sight is at the center
  of the screen.
* In the put-away the gun goes down with the hands. The game removes it 15 ticks, 0.125 s,
  after the start of the clip.
* In third person the hands of the vanilla combat rifle clips hold the grip and the gun in
  front of the box. In the third-person idle every part is at its place, the belt too.

What the test shows, and is not a fault of the clips, is the same as for the Khvostov: the
camera kick of the weapon record and the row of copies behind a moving object. The first
recording also has a sight with no reticle and a light gray gun, and the two later
recordings show the work on the dyes and on the reticle. The Pip-Boy on the left arm is
large in the view in the reload, because the Destiny clip moves the left forearm across the
view.

## The game test of the Tex Mechanica mod

`mod/TexMechanica` has three weapons in one plugin. Each test below is from one session of
the game with the release that `validation/tex_mechanica/release_tested.sha` names. That
file has the hashes of the three files of `build/release`, the same before and after the
tests. The steps of a test are those of the Khvostov test.

| File | Weapon | Result |
| --- | --- | --- |
| `validation/the_chaperone/game_test.mp4` (88 s), `.log`, `_steps.json` | The Chaperone | 44 ops, 0 failed. Three shots (6 to 3 rounds), then a reload with 3 shells (`WPNReload3`) to 6 rounds. |
| `validation/the_huckleberry/game_test.mp4` (78 s), `.log`, `_steps.json` | The Huckleberry | 40 ops, 0 failed. Two bursts (30 to 14 rounds), then the reload to 30 rounds. |
| `validation/tex_mechanica/game_test_the_last_word.mp4` (82 s), `_steps.json` | The Last Word | 44 ops, 0 failed. Three shots (8 to 5 rounds), then the reload to 8 rounds. |
| `validation/NAME/game_test_third_person.mp4` (122 s and 109 s) | The Chaperone, The Huckleberry | "The third-person clips" has the result. |
| `validation/the_chaperone/game_test_reloads.txt` | The Chaperone | The 12 reloads, one for each count of rounds in each view. |
| `validation/NAME/red_dot_game.jpg` | The Chaperone, The Huckleberry | The sight in the sights and at the hip. |
| `validation/NAME/left_hand_before_after.jpg` | The Chaperone, The Huckleberry | The left hand at the hip before and after the pose clip: the game, and check pictures of the hand from two sides. |

| Time in the video of The Chaperone | Step |
| --- | --- |
| 0 s to 3 s | The idle camera of the game (the test started 2.5 minutes after the start of the session; the first op of the test ends that camera). The draw is at 2 s. Then the idle. |
| 7 s, 8 s, 10 s | Three shots from the hip. |
| 11 s to 15 s | Reload with 3 shells. The ammunition count goes from 3 to 6. |
| 17 s to 23 s | The sights, and the shots in the sights with the motion of the lever. |
| 25 s to 27 s | Gun down, then gun ready. |
| 29 s to 32 s | The sprint pose (the event of the graph, with no motion of the player). |
| 34 s, 36 s | Put away, then draw. |
| 40 s to 66 s | Reload with 3 shells and a shot at one quarter of the game speed. |
| 68 s to 83 s | Third person: a shot, a reload, the camera at the side of the weapon. |

What the tests prove:

* The game finds the three weapons, `TheLastWord`, `TheChaperone` and `TheHuckleberry`,
  loads the model of each one with its textures, and starts its graph, `TXLGunBehavior`,
  `TXCGunBehavior` or `TXHGunBehavior`.
* For The Chaperone, the game played these clips in the recording: `WPNEquipFast`,
  `WPNIdleReady`, `WPNIdleReadyA`, the three shot clips at the hip, `WPNFireSingleReady`,
  `A` and `B`, `WPNReload3`, `WPNIdleSighted`, `WPNIdleSightedWobble`,
  `WPNFireSingleSighted`, `WPNIdleGunDown`, `WPNSprint`, `WPNUnEquip` and
  `WPNRunForwardReady`. The graph selects one of the three shot clips for each shot. In the
  test of the reloads the game played `WPNReload1` to `WPNReload6`. One shot takes one
  round.
* For The Huckleberry, the game played `WPNEquipFast`, `WPNIdleReady`, `WPNIdleReadyA`,
  `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNFireAutoSighted`, `WPNReload`,
  `WPNIdleSighted`, `WPNIdleGunDown`, `WPNSprint`, `WPNUnEquip` and `WPNRunForwardReady`,
  and in an earlier run also `WPNIdleSightedWobble`. The weapon fires automatically while
  the trigger is down, 16 rounds in the two bursts.
* The gun of The Huckleberry is in the right hand in every clip, so the rule of `[gun]` is
  correct for the place of the gun.
* The left hand is on each of the two new guns at the hip, as
  `validation/NAME/left_hand_before_after.jpg` shows. The thumb of the left hand is on the
  left side of The Chaperone, and the left hand holds the magazine of The Huckleberry.
  Before the pose clip the left hand of The Chaperone was open at the left of the gun, with
  a space between the two. "The left hand on the gun" has the numbers.
* In the sights, the dot of the reticle is at the center of the screen for the two new guns,
  at (639, 359) of 1280 x 720 for each one, where the center is (640, 360). The glass of The
  Chaperone has its two red rings between the horns of the rear sight. The glass of The
  Huckleberry has its border and its four marks.

What the tests show, and is not a fault of the clips:

* In every recording the game goes into the sights about 2.1 s after the action
  `ActionSighted` of the test, for each of the three weapons. That includes The Last Word,
  whose clips did not change. The rounds of the two shot actions in the sights come late.
  The Chaperone has 5 rounds at the end of the sights and 4 after that. I did not find the
  cause.
* Two minutes after the start of a session the game turned the camera about the player,
  because it had no input. One recording of The Huckleberry had that camera in it, and I
  made it again in a session that was older than two minutes. The camera did not come again
  in that session.
* In one run of the test of The Huckleberry on an earlier build, one op of 40 failed. The
  game did not keep the ammunition count that the test set at its start. The runs after that
  had no failed op. In one session on the last release, each of the three first-person tests
  had one such failed op. The reserve count stayed above the count of the test, and the
  program for the sight pictures had run before and had set a reserve of 200. After these
  tests the same op kept the counts in that session, 10 times of 10. I did not find the
  cause. The results here are from the next session, where the tests ran before the sight
  pictures, and no op failed.
* `check/third_session.sh` keeps the session ID in one file, `work/probe_session.txt`, and
  the probe has one session at a time. Two threads that use this program at the same time
  stop each other's session. That happened once. A second thread started its session 34 s
  after the last test here was complete, and my stop command then stopped the session of
  that thread. Check `esx probe status` before you start or stop a session.
* The build of esx gave a plugin file with other bytes once, in the first build after a
  change of the behavior source, with the same count of records and the same two archives.
  Every build after that gave the same bytes. Every result here is from the tests on that
  last release.

## What is not proved

* For The Chaperone and The Huckleberry, the same as for the Khvostov: no walk, run or jump
  clip in the game. `WPNEquip` and the idle variants `B`, `C` and `D` did not play. The four
  single shot clips of The Huckleberry did not play, because the weapon is automatic.
* For The Huckleberry, no picture of Destiny shows that the reload is correct. The clip of
  the hands and the clip of the gun parts have the same frame count, and the barrel housing
  moves in the frames in which the left hand is away from the gun. The path of the magazine,
  out of the gun, a turn, and back into the gun with no hand on it, is what the clip of the
  parts has.
* The values of the two new weapons, damage, capacity and time between two shots, are
  choices. The tools do not read the values of Destiny.
* The source-against-result videos of the two new guns cover one reload of each gun,
  `WPNReload1_*.mp4` and `WPNReload_*.mp4`, and two idle clips only. The numbers in
  `summary.txt` are for every clip.
* For Hammerhead, the same as for the Khvostov: no walk, run or jump clip in the game, and
  no single shot clip in the recording.
* For the Khvostov, the same: no walk, run or jump clip in the game. The weapon is
  automatic, so the four single shot clips did not play in the recording. `WPNEquip` and
  `WPNIdleReadyC` and `D` did not play. They have the same data as clips that played.
* The game test had no move input, so the game did not play the walk, run and jump clips:
  `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunLeftReady`, `WPNRunRightReady`,
  `WPNRunGunDown` and `WPNJumpImpactLand`. `WPNEquip`, `WPNFireSingleReadyB` and
  `WPNIdleReadyB` to `D` did not play in the test. They have the same data as the clips that
  played.
* The game test is one recording at 1280 x 720 in a test cell. Nobody played the game with a
  keyboard and a mouse, and the sound was not recorded.
* The look of the materials in any light other than that of the test cell.
* The clips with vanilla weapon motion have no source to compare with. I looked at their
  first-person videos. The hands stay on the gun, and no arm part comes into the view.
* The bone `Camera Control` has the values of the vanilla clips. What the game does with
  that bone is an assumption from those values, a wider view in the sprint and a narrower
  view in the sights.

## Limits

* The reload of The Chaperone with 6 shells is 7.2 s long, because the clips have the speed
  of the files of Destiny: 16 frames, 27 frames for each shell, 48 frames. The document of
  esx, `docs/BEHAVIOR.md`, says that a `speed` line in the `reload` block of the behavior
  source makes every reload faster. No mod has such a line, and it was not tested.
* The shot of The Chaperone at the hip has no motion of the lever, because the file has none
  there.
* The glass of The Huckleberry has no tint and no mirror picture, and the two curved lines
  of its texture show only a little. Its colors are half of the values of Destiny in the
  sights, set by `glass_scale`, because the game makes a glow around a color above 1.
* The glass of the two new guns always shows, at the hip too, with the colors that Destiny
  has in the sights.
* The pose of the left hand on the two new guns is a pose clip of each gun that the
  measurements selected, as "The left hand on the gun" describes. No file says that Destiny
  uses this clip with these states. The left hand of The Chaperone touches the gun with its
  thumb and its fingers, with 5 percent of its vertices nearer than 0.5 cm in the hold pose,
  and its palm does not. That is the pose of the file. A frame in which the left wrist is
  between 3 and 8 cm from its place in the hold pose gets a part of the offsets.
* There are three templates, `revolver44`, `combatrifle` and `combatrifle_parts`, and five
  weapons. The kinds of the Destiny weapon bones, in `tools/d2rig.py` and in `[roles]` of a
  set file, are those of a hand cannon and of a rifle with a magazine. A gun with other
  parts gets its bones in `[bones]` of its set file, as Hammerhead does, and the reload
  events then need a magazine or a bolt, or `[events]`.
* A gun can have 13 moving parts at most, because the Fallout 4 skeleton has 13 weapon
  bones. Hammerhead uses 12.
* The Khvostov has no Destiny clip for its shots and no motion in its Destiny sprint loop,
  so these clips have the motion of the vanilla combat rifle. In the sights the gun is 2.69
  units higher than in the Destiny clip, because of `[sight]`.
* In the reload of the Khvostov a finger bone of the left hand can turn up to 31 degrees
  more in one frame than the source bone. That is the second bone of the middle finger at
  frame 64, where the hand pulls the charging handle and the source bone turns 30 degrees.
  The source fingers turn up to 107 degrees in one frame in this clip. I looked at frames 62
  to 66 from two sides, and no finger has a wrong shape.
* `rig/d2_hands.json` is for the masculine hand mesh of the file, `body_hands`.
* The events use the sound names of the vanilla .44 revolver.
* A clip with vanilla weapon motion moves the arms as one body with the gun. That is correct
  for a small motion such as walk, run, jump or gun down. It is not correct for a large turn
  of the gun. The melee clip was wrong, and it is not in the set.
* Some finger bones go deeper into the gun than the same bone of the source. `summary.txt`
  lists them under "deeper than the source": `WPNIdleReady` right Finger31;
  `WPNFireSingleReady` left Finger41; `WPNFireSingleSighted` left Finger41, left Finger42,
  left Finger43; `WPNEquip` right Finger31; `WPNUnEquip` right Finger31; `WPNReload` right
  Finger23, left Finger13. `NAME.txt` has the depth of each bone. In the hold pose the first
  bone of the right middle finger is 0.46 units deep in the grip below the trigger guard,
  against 0.18 in the source. The next bone of that finger is 0.66 units deep, against 0.69.
  The other values are in frames where a hand goes fast to or from the grip, and the source
  hand goes through the grip there too.
* The collision step can turn a finger bone by up to 10 degrees in one frame when the source
  finger goes through a gun part, as in the regrip of the reload and the fan of the hammer.
* The check pictures do not draw the part of the sleeve at the shoulder, because its skin
  bone is not a bone of the animation.

## The folders

"This area in the monorepo" says where each short name of this table is. In short, the
sources and `rig/d2_hands.json` are in `destiny/port/`, in git. `extract/`, `out/`, `work/`,
`validation/` and the rest of `rig/` are in `data/destiny/port/`, not in git. `mod/NAME/` is
`data/mods/NAME/`.

| Folder | Content |
| --- | --- |
| `d2fo4.py` | The command (`./port destiny convert`). |
| `port.toml`, `regress.toml` | The commands of `./port destiny`, and the table of the regression (`./port destiny regress`). |
| `docs/porting/` (in the root of the repository) | The procedure for a new weapon (`destiny.md`), the sign and the rule of each known problem (`troubleshooting.md`), and the lessons of the ports (`lessons.md`). |
| `sets/` | One file per weapon, with its clip set and the data of its model. |
| `tools/` | The programs. `tools/blender/` has the programs that run in Blender. |
| `templates/` | One file for each template weapon. |
| `rig/` | `d2_hands.json`, and the clips of each template (game files, made by `tools/make_rig.py`). |
| `check/` | The check programs. |
| `extract/khvostov_7g_02/`, `extract/hammerhead/` | The extraction of the Khvostov and of Hammerhead, from `./port destiny extract --out`: the first-person files, the weapon file, the textures, `manifest.json`, and `states.json` of `tools/d2states.py`. `notes/`, which is `destiny/port/notes/`, has programs that analyze the game data, and `extract/notes/` has their outputs. Two print the weapon tags, `third_clip_index.py` lists each clip tag of the game (name hash, frames, bones), and `third_graph_dump.py` writes each state and leaf of the third-person graph. |
| `out/the_last_word/`, `out/khvostov_7g_02/`, `out/hammerhead/` | The results: 24, 27 and 27 HKX clips. |
| `extract/the_chaperone/`, `extract/the_huckleberry/` | The extraction of the two guns, with `states.json`, `dyes.json`, `sight.json`, `third_person/`, and `posed/` (the clips with the pose clip of the gun on the left hand, `tools/d2pose.py`). |
| `mod/TexMechanica/` | The esx project with three weapons: The Last Word, The Chaperone and The Huckleberry. Its `README.md` has the content and the commands. |
| `validation/the_chaperone/`, `validation/the_huckleberry/` | The numbers of each clip (`summary.txt`, `NAME.txt`), the videos of one reload and of two idle clips, and the game tests (`game_test.mp4`, `game_test_third_person.mp4`, `game_test_reloads.txt`, `red_dot_game.jpg`, `third_person_reload_game.jpg`, `third_person_source_result.png`), the distance of each hand to the gun in each clip (`hand_distance.txt`), and the left hand before and after the pose clip (`left_hand_before_after.jpg`). |
| `validation/tex_mechanica/` | The test of The Last Word in the mod with three weapons, and `release_tested.sha`. |
| `rig/third_power_armor/` | The vanilla third-person clips of each template for a body in power armor (game files, made by `tools/make_rig.py`). |
| `mod/TheLastWord/`, `mod/Khvostov/`, `mod/Hammerhead/` | The esx project of each weapon. `build/release/` has the plugin and the two archives. |
| `work/the_last_word/`, `work/khvostov_7g_02/`, `work/hammerhead/` | The work files of the last run: `parts.json`, the bake, the poses, the reports, the check pictures, the game recordings. For the Khvostov and for Hammerhead the pictures of the validation videos are not kept, and `check/validate.py` makes them again. |
| `validation/materials_before_after.jpg` | The three guns in the game before and after the dyes and the new material conversion. `validation/hammerhead/shaders_game.jpg` has the four looks of Hammerhead in the game. |
| `validation/hammerhead/red_dot_game.jpg`, `game_test_red_dot.*` | The sight of Hammerhead in the game with its glass and its reticle, and the game test with the sight part. |
| `validation/khvostov_7g_02/red_dot_game.jpg`, `game_test_red_dot.*` | The same two for the Khvostov. |
| `extract/NAME/third_person/` | The third-person reload of each gun (`tools/d2third.py`): `reload.npz`, `states.json`, and `raw/` with the tags that the decoder reads. |
| `validation/NAME/game_test_third_person.mp4`, `third_person_reload_game.jpg`, `third_person_source_result.png`, `game_test_third_person_steps.json` | The game test of the third-person reload of each weapon, 12 pictures of it, and the source above the result as lines. |
| `rig/third/` | The skeleton of the character and the vanilla third-person clips of each template (game files, made by `tools/make_rig.py`). |
| `extract/hammerhead/sight.json`, `extract/hammerhead/sight/`, and the same in `extract/khvostov_7g_02/` | The glass of the sight and the reticle of each gun (`tools/d2reticle.py`): the meshes, the values of each material, and its two shaders. |
| `validation/khvostov_7g_02/`, `validation/hammerhead/` | The videos and the numbers of the 27 clips of each weapon, and the game test (`game_test.mp4`, `game_test.log`, `game_test_steps.json`, `game_test_frames.jpg`, `game_test_view.jpg`). |
| `validation/the_last_word/` | The videos and the numbers of the 24 clips, and the game test (`game_test.mp4`, `game_test.log`, `game_test_steps.json`, `game_test_frames.jpg`, `game_test_view.jpg`, `game_test_put_away.jpg`). |
| `marathon/` | The extraction tools for the game Marathon (the weapon M77): its own programs (`marathon/extract/`), result and `README.md`. `data/marathon/extract/out/m77_omnipositor/` has the first-person file that `d2fo4.py` reads. |
| `mod/M77/`, `marathon/port/sets/m77_omnipositor.toml`, `out/m77_omnipositor/`, `work/m77_omnipositor/`, `validation/m77/` | The M77 of Marathon: the esx project, the set file, the 27 HKX clips, the work files, and the numbers, the pictures and the game test. |
| `validation/the_last_word_reload/` | The first validation of the reload (pictures of the two hands). It was made before the 48-bit rotations and the last finger rule, so its numbers are older. |
