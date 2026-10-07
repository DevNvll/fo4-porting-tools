# The port of a Destiny 2 weapon to Fallout 4: the process, and what five ports showed

`README.md` is the reference of the tools: each program, each key of a set file, each check
and each result. This file is the procedure for the next weapon, and the lessons of the five
ports. It gives the order of the work, the signs of each known problem, and the facts about
the two games that were not known before the work. For a value, `README.md` and the set
files are the source.

Each command of this file runs in the root of the repository. `README.md`, "This area in the
monorepo", says where each short name of this file is: `d2fo4.py`, `sets/`, `tools/`, `check/`
and `templates/` are in `destiny/port/`; `extract/`, `work/`, `out/`, `rig/` and `validation/`
are in `data/destiny/port/` (not in git); `mod/NAME` is the esx project `data/mods/NAME`, and
its hand-written files are in `mods/NAME`.

## The five ports

| Weapon | Kind | Template | Vanilla record | What was new in this port |
| --- | --- | --- | --- | --- |
| The Last Word | hand cannon | `revolver44` | `44` | The mapping of the two rigs, the finger rules, the gun parts, the clip format |
| Khvostov 7G-02 | auto rifle | `combatrifle` | `CombatRifle`, automatic receiver | The clip of each state from the graph, a state with no clip, the move of the sight |
| Hammerhead | machine gun | `combatrifle_parts` | `CombatRifle`, automatic receiver | 12 moving parts, automatic fire from one shot, the dyes and the shaders, a glass on a moving part |
| The Chaperone | shotgun with a lever | `combatrifle` | `CombatShotgun` | A reload from three states, one reload clip for each count of rounds, additive third-person clips |
| The Huckleberry | submachine gun | `combatrifle` | `CombatRifle`, automatic receiver | Clips of another rig, part motion in a second clip, a glass with bright colors |

The sight glass with its reticle (Hammerhead, the Khvostov) and the third-person reload (the
first three guns) came after the first-person ports of these guns. `mod/TheLastWord`,
`mod/Khvostov` and `mod/Hammerhead` have one weapon each. `mod/TexMechanica` has The Last
Word, The Chaperone and The Huckleberry in one plugin.

## The process

Do the steps in this order. Each step has a result that you can examine before the next one.

### 1. Prepare (one time)

```sh
cp config.example.toml data/config.toml      # then give blender, esx, fo4_data, proton and destiny_game in it
./port destiny setup                         # the environment of d2x, for the extraction
./port fnv make-rig --nvcs /path/to/NVCS/Skeleton.nif    # the rig folder of fnv: the Fallout 4 skeleton
./port fnv make-rig --arm-meshes             # the arm meshes of Fallout 4, for the check programs
./port destiny make-rig                      # the vanilla clips of the templates, into data/destiny/port/rig/
./port doctor                                # each setting and each necessary file: there or missing
```

The environment variables `BLENDER`, `ESX_BIN`, `FO4_DATA` and `PROTON_DIR` replace the values
of `data/config.toml`.

The tools read the files of `destiny/extract/d2x`, of `fnv/` and of the game. They
change none of them. Each result goes below `data/`.

### 2. Extract the weapon

```sh
E=data/destiny/port/extract/the_chaperone
./port destiny find "Chaperone"                    # the name and the hash of the item
./port destiny extract "The Chaperone" --arms "Ancient Apocalypse Grips" --out data/destiny/port/extract
./port destiny states $E/manifest.json -o $E/states.json
./port destiny dyes "The Chaperone" -o $E/dyes.json
./port destiny reticle "The Chaperone" -o $E/sight.json
./port destiny third $E/manifest.json              # prints the third-person states
```

`states.json` has the clip of each game state (idle, ready, put_away, fire, iron_sight_idle,
iron_sight_fire, the reload states, the sprint states). It is the list of candidates for the
set file. A state whose name is not a known word has only its hash (the three reload states
of a shotgun).

### 3. Examine the data before you write the set file

The two last ports needed much time for facts that this step shows in minutes. Examine
these points:

1. **The gun is in the hand.** For each clip that you will use, the gun bone (`b_handle`)
   must be on the grip bone (`b_r_grip`). Run this in the root of the repository
   (`python3 FILE.py NAME`):

   ```python
   import json, sys
   import numpy as np
   sys.dont_write_bytecode = True
   sys.path.insert(0, 'destiny/port/tools')
   from glb import Glb
   from d2bake import Rig
   name = sys.argv[1]
   folder = 'data/destiny/port/extract/%s/' % name
   first = json.load(open(folder + 'manifest.json'))['first_person'][0]
   rig = Rig(Glb(folder + first['file']))
   i = rig.index
   print(len(first['bones']), 'bones in the rig')
   for record in first['clips']:
       if record.get('additive') or record['name'] not in rig.clip_names():
           continue
       world, _ = rig.bake(record['name'])
       gap = np.linalg.norm(world[:, i['b_handle'], :3, 3] - world[:, i['b_r_grip'], :3, 3], axis=1).max()
       print('%-20s %3d frames, %d nodes, the gun is %.3f m from the grip bone' % (record['name'], record['frames'], record['nodes'], gap))
   ```

2. **The parts.** For each weapon bone: the count of its vertices, the box of its vertices, and
   its motion in each clip
   (`python3 destiny/port/tools/d2bake.py FILE.glb --clip CLIP -o data/destiny/port/work/NAME/probe`
   writes the matrices). A bone with no vertex needs no Fallout 4 bone.
3. **The clips that move the parts.** A part can move in the clip of the hands, in an
   additive clip with the same frame count, or in a clip of the gun entity (`weapon_clips`
   of the manifest).
4. **The poses at the two ends of each clip.** Compare the last frame of each clip with the
   first frame of the idle. A clip that does not start or end in the hold pose is a part of
   a sequence.
5. **Pictures.**
   `./port destiny video FILE.glb --clip CLIP --columns 8 --width 640 --out data/destiny/port/work/NAME/probe/sheet.png`
   draws frames of a clip of the file. Read the motion from the pictures, not from the names of
   the bones.
6. **The left hand is on the gun.**
   `./port destiny pose data/destiny/port/extract/NAME/manifest.json --measure --hold CLIP:0`
   prints the distance of each Destiny hand to the gun in the hold pose. A hand that holds
   the gun has many vertices nearer than 0.5 cm. If the left hand has none, the clip is a
   clip of the weapon class and the gun needs a pose clip: `--list` prints the candidates
   (the short additive clips with offsets of the left hand), and `--measure --pose TAG`
   measures one. `README.md`, "The left hand on the gun", has the commands.

### 4. Select the template and the vanilla record

The template (`templates/NAME.toml`) gives the weapon bones, the sounds and the pose of the
body. The vanilla record gives the behavior graph, the ammunition and the third-person clips of
the grip. A long gun uses `combatrifle`: the combat rifle and the combat shotgun have the same
graphs and clips (`AnimsCombatShotgun`). `combatrifle` has 11 weapon bones; a gun that needs
more uses `combatrifle_parts` (13 bones, all that the skeleton has).
`esx item new weapon RECORD --standalone --all-parts -o FILE` prints the values and the parts of
a vanilla weapon, and `esx record show Fallout4.esm RECORD` prints each field.

### 5. Write the set file, in two passes

First pass: `template`, `hold`, `sighted`, `[roles]` or `[bones]`, `[clips]`, `[synth]`,
`[static]`, `[hold_end]`, `[events]`. Copy `sets/khvostov_7g_02.toml` and change it. Then:

```sh
W=data/destiny/port/work/NAME
./port destiny convert FILE.glb --set destiny/port/sets/NAME.toml bake parts
./port destiny convert FILE.glb --set destiny/port/sets/NAME.toml retarget hkx install
./port destiny points $W/parts.json --poses $W/fo4/poses/SIGHTED_CLIP.npz
```

Examine the output:

* `[parts]`: each shape is on the Fallout 4 bone that you expect, and the box of the gun has
  the size of the gun (The Chaperone is 48.6 units long, which is 69 cm).
* `[retarget]`: `wrist` and `weapon` are 0.00 units.
* `[hkx]`: `pos err` is below 0.02 units, and each reload has the events that you expect.
* Pictures of the source beside the result:

  ```sh
  D=data/destiny/port
  ./port destiny check render --glb FILE.glb --clip CLIP --poses $D/out/NAME/WPNReload.hkx \
      --parts $D/work/NAME/parts.json --out DIR --template combatrifle --frames 0,10,20,30 --views fp --kinds src,fo4
  ```

Second pass: `[sight]`, `[model]`, `[model.sight]`, `[third]`. `tools/d2points.py` prints the
muzzle, the eye point and a map of the sight.

### 6. The model and the sight

```sh
./port destiny model FILE.glb --set destiny/port/sets/NAME.toml --mod NAME      # writes into data/mods/NAME
```

For a sight with a glass, read the pixel shader of each glass material
(`./port destiny shader-text data/destiny/port/extract/NAME/sight/TAG_ps.dxbc`) and write the
rule into the set file as a comment. Look at each channel of the plate textures. The program
prints the place of the reticle in weapon space: put it into `point` of `[sight]`, then run the
steps `retarget hkx install` again.

### 7. The third-person reload

```sh
D=data/destiny/port
./port destiny convert FILE.glb --set destiny/port/sets/NAME.toml third \
    --third-output data/mods/NAME/behavior/NAME/animations/third_person
./port destiny check third-sheet $D/extract/NAME/third_person/reload.npz $D/work/NAME/third/poses/WPNReload.npz OUT.png
```

Read the line `[third]` of the output: the shoulder shift (a large value: use `gun = "source"`),
and the count of frames with the right hand on the grip.

### 8. The mod project

A project has `esx.toml`, one item file for each weapon (`items/`), and one behavior source
for each weapon (`behavior/NAME/NAME.bhv`, with its own prefix). Copy the files of
`mods/TexMechanica` and change them. These hand-written files are in `mods/NAME` (in git).
`./port mod build NAME` copies them into the project `data/mods/NAME`, where the convert
commands wrote the clips and the model, and runs `esx build` there (`mods/README.md`).

```sh
./port mod build NAME --update-lock
esx --data "/path/Fallout 4/Data" plugin check-weapons data/mods/NAME/build/release/NAME.esp
esx --data "/path/Fallout 4/Data" scene weapon data/mods/NAME/build/release/NAME.esp WEAPON
esx --data "/path/Fallout 4/Data" render weapon data/mods/NAME/build/release/NAME.esp WEAPON --sheet -o data/mods/NAME/docs/WEAPON.png
```

### 9. The game tests

```sh
esx probe status                                               # the probe has one session at a time: look first
./port destiny game session NAME LABEL                         # builds, starts a session, prints its ID
./port destiny game record --session ID --weapon WEAPON --capacity N [--auto] --out DIR
./port destiny game third --session ID --weapon WEAPON --capacity N --record --out DIR
./port destiny game reloads --session ID --weapon WEAPON --capacity N --out DIR     # one clip for each count
esx probe stop --session ID                                    # only the ID that your start command printed
```

Look at each recording before you use it (frames at equal steps). Write down the hashes of
the release before the tests, and compare them after the last change of any file.

### 10. The numbers, the videos and the documents

```sh
V=data/destiny/port/validation/NAME
./port destiny check validate FILE.glb --set destiny/port/sets/NAME.toml --out $V --clips CLIPS --no-video
./port destiny check validate FILE.glb --set destiny/port/sets/NAME.toml --out $V --clips CLIPS --left-hand --only WPNReload
```

Then write the section of the weapon in `README.md` and the `README.md` of the mod
(`mods/NAME/README.md`): what
the mod has, the choices, what is proved, what is not proved, the limits. Add the weapon to
`destiny/port/regress.toml` with the clip folders of the mod as its baseline: then
`./port destiny regress` finds each later change of its clips.

## Which rule for which sign

| Sign | Cause | Rule |
| --- | --- | --- |
| The hands hold no gun; the gun bone is at the origin of the world | The clip is a clip of another rig | `[gun] rest = true` |
| A part does not move in the clip of the hands | Its motion is in a second clip | `[gun.parts]`, with the additive clip that has the same frame count |
| The left hand does not touch the gun (0 percent of its vertices are nearer than 0.5 cm, `check/touch.py`), in the source also | The clip of the hands is a clip of the weapon class | `tools/d2pose.py` with a pose clip of the gun, and `[hand_pose]` |
| The reload is three states, and one of them plays one time for each round | A shotgun | `[compose]`, `[piece_events]`, and one line `when ammo == N play CLIP` for each count in the behavior source |
| A state has no clip for this weapon (no shot clip) | The graph has no entry for the tags of the weapon | `[synth]`: the weapon motion of the vanilla clip on the Destiny hold pose |
| The sprint loop is one pose | The file has no motion in that clip | `[synth]` with `pose = "sprint"` and the vanilla sprint as the reference |
| In the sights the eye is not on the sight | Destiny aligns the sight when the game runs | `[sight]`: `point` and `clips` |
| The gun is out of the hand before the hand moves in the put-away | The graph removes the gun 0.233 s before the end of the clip | `[hold_end] WPNUnEquip = 8` |
| A part is at a wrong place in a vanilla clip (a belt that is a straight line) | The bind pose of the file is not the hold pose | `part_rest = "hold"` |
| A weapon bone has a hash, not a name | The name is not in the word list | `[roles]` (a kind of the template) or `[bones]` (a Fallout 4 bone) |
| Third person: the left arm is too short | Destiny holds the gun at another place than the vanilla stance | `gun = "source"` in `[third]` |
| Third person: "the clip has offsets only" | An additive clip | `tools/d2third.py --additive STATE`, with `--base` |
| Third person: the gun parts do not move | The gun entity has no clip for the state | `[third.parts]`, with the first-person clip |
| Third person: the reload ends before its motion ends | The graph sends `reloadEnd` 0.5 s before the end of the clip | `[third.hold_end]` |
| Third person: sounds of another reload clip play | The graph plays `WPNReload` on a second clip node | A clip with a new name for each count, and `silent = ["WPNReload"]` |
| The build stops: no folder of `power_armor_third_person` has the clip | The two third-person views have one graph | `[third.power_armor]` |
| A haze on the sight glass, or a glow around the reticle | A color above 1 in an effect material | A smaller `glass_scale`; a small reticle |

## What the ports showed

### The data of Destiny

* **The graph, not the clip list, says which clip a weapon uses.** A first-person file has 91
  to 133 clips, and most of them are clips of other weapons of the class. `tools/d2states.py`
  reads the graph with the tags of the weapon. The weapon tag is the content group of the
  gun (the Khvostov) or the tag of its class (Hammerhead), and the row of the pattern entity
  says which one.
* **A clip with another node count than the rig is a clip of another rig.** In the files of
  The Chaperone, the Khvostov and Hammerhead, each full-pose clip with the node count of the
  rig has the gun on the grip bone (32, 66 and 23 clips), and no clip with another node
  count has it (32, 13 and 30 clips). The state clips of these three guns have the node
  count of the rig. The Huckleberry is the exception: its rig has 76 bones, its state clips
  have 77 nodes, and only 2 of its 59 full-pose clips have the gun on the grip. The cause in
  the decoder is not known. The gun bone has no offset from `b_r_grip` in each correct clip,
  so the rule `rest` is safe.
* **A bone name is not a part name.** `b_pump` of The Chaperone is a lever. Its vertices are
  a thin loop below the receiver, and it turns 99 degrees. `bone_D7A79DD5` of The Huckleberry
  moves in the clip of the shot and has no vertex. Count the vertices and look at a picture.
* **A part that the game hides is at a far place.** The shell of The Chaperone is behind the
  camera, or 1.4 m away, when Destiny does not show it. A blend between two clips must not
  move such a bone (`cut`).
* **Additive clips.** The extraction shows an additive clip on the first frame of one
  full-pose clip, which can be a clip of another gun. Only the motion against its own first
  frame is data. Put that motion on the rest place of the bone.
* **A clip of the class does not hold each gun of the class.** The left hand of The
  Chaperone is 0.9 cm from the gun in each clip of the shotgun class. The file of each gun
  has short additive clips (2 or 3 frames, offsets only) that no state of the graph names.
  Some of them have one pose of the left hand and its fingers, and with the correct one the
  hand is on the gun. For The Huckleberry the pose clip is the difference between the idle
  of the class and a clip of this gun with one pose. Two candidates of The Chaperone have
  the same offsets with opposite signs, so measure each candidate: the name does not say
  which one is correct.
* **Two clips are a pair when the same frames move.** In the reload of The Huckleberry the
  housing of the barrel moves from frame 3 to frame 61 in the clip of the parts, and the
  left hand is away from the gun from frame 3 to frame 61 in the clip of the hands. That is
  the evidence that the two clips are one reload. No file says it.
* **The reload of a shotgun is three states**: `reload_enter`, one state for one shell
  (`6C41757C`, its name is not known), and `chamber_1`. The last pose of the shell clip is
  not its first pose: the hand is out of the view at the two ends.
* **A state can have no part motion.** The shot of The Chaperone at the hip has no motion
  of the lever in the first-person file; the shot in the sights has it.
* **State names are FNV-1 hashes of words.** Found: `reload_1` (`EB22859A`), `reload_enter`
  (`12CFA0E5`), `chamber_1` (`FACB2E5D`), `sprint_ready` (`DB28BEA1`). Hash a list of
  candidate words to find a name.
* **Third person.** The clips are in the player body entity (72 bones, one graph with 332
  states), not in the extraction of the gun. The dimension 3 of a state is the weapon tags
  and the dimension 1 is the stance; the stance `811C9DC5` (the hash of an empty word) is
  for each stance. The clips move the upper body only. The gun entity has its own graph
  with the same state names, and that graph gives the clip of the gun parts. A pairing by
  the frame count gave the same clips for three guns. For The Chaperone it gave a clip that
  is in no state of the graph of the gun.
* **Third-person clips of a shotgun are additive.** The test of the extraction for an
  additive clip does not find each of them. A clip whose first or last frame has no offset
  is additive.
* **The colors of a gun are not in its textures.** The dyes and the gear shader give them
  (`tools/d2dyes.py`, `tools/d2shade.py`). The Last Word and The Huckleberry have 0 percent
  of pixels with a dye; Hammerhead has 93 percent.
* **A sight glass is in two more render stages** (`transparent`, `reticle`), which the
  extraction does not have. The materials are small programs: the pixel shader gives the
  rule, and an expression program calculates colors from inputs that the files do not name.
  You must select one state of the inputs, and that is a choice.

### The two rigs and the clips

* The true scale is correct: 1 m is 69.99125 units, and the arms and the hands of the two
  rigs have the same size to 6 percent. The fingers do not, and they need the finger rules.
* The camera bone of Destiny (`b_utility`) goes on the Fallout 4 camera bone. Then the
  picture of the game is the picture of Destiny, and a check picture can compare the two.
* A first-person clip of Destiny has useful poses of the arms and of the gun only. Each
  other bone takes the pose of the template.
* The clip format matters: with 40-bit rotations the muzzle moved 0.03 to 0.09 units from
  frame to frame, more than the motion of an idle. The vanilla clips have 48 bits.
* A clip with vanilla weapon motion is correct for a small motion (walk, run, jump, gun
  down, sprint). It is wrong for a large turn of the gun: the melee clip is not converted.
* The Fallout 4 skeleton has 13 weapon bones. Hammerhead uses 12.
* When a tool changes, bake the clips of each earlier gun again and compare. The largest
  difference must be 0.0. `./port destiny regress` makes the HKX clips of each weapon again
  and compares their bytes with the clips of each mod.

### The graphs of Fallout 4

* **First person.** The graph asks for clips by name, and a clip that the mod does not have
  is the vanilla clip. `WPNIdleSightedWobble` must be the sighted idle of the weapon. The
  put-away state removes the gun 0.233 s before the end of its clip. The combat rifle has
  two animation keywords, and `AnimsCombatRifle` must go away. The vanilla .44 has the flag
  `Bolt Action`, which plays a hammer clip after each shot.
* **Third person has few clips of a weapon**: the reload, a hold pose (`WPNAssemblyPose`) and
  two clips of the gun parts. Each other clip is a clip of the grip.
* **The left hand in third person is on the bone `WeaponIKTargetL`.** The game puts the hand
  there with IK in each clip. `WPNAssemblyPose` gives its place for each clip of the grip.
  With the bone at its rest place the hand goes to the grip of the gun.
* **The third-person graph ends a reload 0.5 s before the end of the clip.** The clip node
  has three triggers relative to the end of the clip (`reloadEndSlave`, `reloadEnd`, and one
  more). When the event of the clip comes first, it ends the reload. A clip that moves until
  its last frames needs 16 more frames.
* **The third-person graph has a second player for the gun parts**
  (`WeaponSlave_StateMachine`). In the vanilla graph its reload state and the reload state of
  the body have one clip node. esx makes a new node for a clip with a new name in the state
  of the body only, so the game also plays `WPNReload`, with its events.
* **In the first-person view the events come from the first-person clip only.** The
  third-person reload of The Chaperone is 1 s shorter, and the reload still ends at the
  event of the first-person clip.
* **One reload clip for each count of rounds works** with the lines `when ammo == N play CLIP`
  of an esx behavior source, in the two views. Each line needs the clip in each view that
  has the same graph (the body and the body in power armor).
* To learn such facts: `esx behavior explain reload --like KEYWORD`,
  `esx hkx events FILE --event NAME` and `esx hkx show FILE --selector 'object(N)'` on the built
  graph, and the trace of the probe (`anim.trace`) for the clips and the events that the game
  started.

### The model and the sight

* A Fallout 4 material has no metal value. A specular value from the reflectance of the
  surface gives a dark metal; a high specular value for each metal pixel gives a light gray
  gun.
* esx makes no new effect shader. The glass and the reticle are a second part of the weapon
  with a vanilla mesh as the template, and the gun has the connect point `P-Scope` on the
  bone that carries the glass.
* A template shape keeps 16-bit vertex values. Put the place of the shape at the center of
  its new geometry.
* The reticle has the size of an angle, not of its quad. The vertex shader gives the
  distance from the camera. The quad of the file as a part of the gun was 5 times too large.
* A color above 1 makes a glow in Fallout 4. A small dot can have it. A border of 3.0
  around a glass made a haze on all of the glass.
* The glass and the reticle show at each time in Fallout 4. In Destiny the reticle shows
  only in the sights, and it is on the aim axis, not on the glass.
* `esx render` does not draw an effect material. Only a game test shows a glass.

### esx and the game test

* `esx probe start` needs `--mod PROJECT/build/release` and `--proton`. With the project
  folder the game loads no plugin.
* The probe has one connection. An op with the error detail `retryable` can be sent again.
* The probe has one session at a time for the whole computer, and `check/third_session.sh`
  (`./port destiny game session`) keeps its ID in one file
  (`data/destiny/port/work/probe_session.txt`). Two threads that test in the game at the same
  time stop the session of each other. Examine `esx probe status` before you start or stop a
  session, and stop the ID that your start command printed.
* About two minutes after the start of a session the game turns the camera about the
  player. A recording must end before that time or start after it.
* In the test the game goes into the sights about 2.1 s after `ActionSighted`, for each
  weapon. The cause is not known.
* One build gave a plugin file with other bytes than the builds after it (the first build
  after a change of a behavior source). Do the last tests after the last build, and compare
  the hashes of the release before and after.
* An item file can set a field that it has no key for:
  `set = { 'FNAM\# Projectiles' = 1, 'DNAM\Attack Delay' = 0.857 }`.
* The videos of `check/validate.py` need about 10 minutes for each clip. Make the numbers of
  each clip first (`--no-video`).

### The method

* Measure, then decide. Each rule in a set file has the measurement that gave it as a
  comment.
* A check that compares with the source proves the retarget. It does not prove a rule that
  changes the source (`[gun]`, `[compose]`). Only a picture of Destiny, or the game, proves
  such a rule.
* A check against the source does not find a fault that the source has. The left hand of
  The Chaperone was 1.0 cm from the gun in the result and 0.9 cm in the source: each check
  passed, and the user saw the fault in the game. Measure the property that you want (the
  hand touches the gun), not only the difference to the source.
* A check that counts the vertices inside the gun does not show a hand that is away from
  the gun. `check/touch.py` measures the distance.
* A game test that passes is not a correct clip. The test of the third-person reload passed
  with a reload that ended 12 frames early and with sounds of another clip. The trace of the
  events showed the two faults.
* Write what is a choice (the damage, the capacity, the state of a glass), and what is not
  tested, in the documents of the mod.
* Stop a program by its process ID. A stop by a text of the command line also stops the
  shell that has that text.

## Faults that we made, and how each one showed

| Fault | How it showed | Correction |
| --- | --- | --- |
| The reticle had the size of its quad | The user saw a reticle that was too large | The size from the distance of the vertex shader |
| Bright values on the glass | A red haze (Hammerhead), a green haze (The Huckleberry) in the game | The values of Destiny with a small reticle; `glass_scale` |
| The session started with the project folder | `item.give`: no form has this editor ID | `--mod PROJECT/build/release` |
| `WeaponIKTargetL` at its rest place | In the game the left hand went to the grip | The bone has the matrix of the left hand |
| The right hand of the third-person source | Open fingers on the grip | The grip of the first-person hold pose, while the hand is on the grip |
| The gun on the vanilla stance | The left arm was up to 8 units too short | `gun = "source"` |
| The events of the third-person clip from the median of each part | Wrong times for a gun with a belt | The bolt, or `align` |
| The first tag list of `tools/d2third.py` | The reload of a rifle for a revolver; the clip of the class for The Huckleberry; no clip of The Chaperone | The tag list of the first-person clips, in the order of the tag tree; the stance for each stance |
| The clip of the gun parts by its frame count | For the shell state of The Chaperone: a clip that is in no state of the graph of the gun | The graph of the gun entity |
| No frames after the motion of a third-person reload | The time to `reloadEnd` was 0.4 s shorter than the clip | `[third.hold_end]` |
| Sounds in the default reload clip | Three shell sounds in a reload with one shell | `silent`, and a clip for each count |
| A recording 2 minutes after the start of the session | The camera turned about the player in the video | A session that is older than 2 minutes |
| Tests before the last build | The hash of the plugin was not that of the tested file | All tests again on the last release |
| A stop command with the session ID of the state file | It stopped the session of a second thread, which had started its session with the same program | `esx probe status` first; the ID that the start command printed |
| The clips of the weapon class for the left hand, with no pose clip of the gun | The user saw in the game that the left hand did not touch the gun | `tools/d2pose.py`, `[hand_pose]`, and `check/touch.py` for each new gun |
| The game pictures at the hip were made for the sight | The left hand was in those pictures, and we did not examine it | Examine each hand in the game picture of the hold pose |

## Open points

* The lever of The Chaperone in a third-person reload with 1 to 5 shells: no picture shows
  if it opens.
* A body in power armor: no game test. The third-person reload there is the vanilla clip.
* The walk, run and jump clips in the game: the tests have no move input.
* The reload of The Huckleberry against a picture of Destiny.
* Why the extraction has the gun bone at the origin in a clip of another rig.
* Why the test goes into the sights 2.1 s after the action.
* Which states of Destiny use the pose clips of a gun, and with which weight. The other
  short additive clips of a gun (ramps with 2 keys, which look like the kick of a shot) are
  not used.
* The melee clip, the other third-person clips of Destiny (`ready`, `fire_1`), the clips of
  a non-player character.
* Emission, iridescence and the mirror picture of a glass.
* The weapons workbench, and the mods in the installed game.
