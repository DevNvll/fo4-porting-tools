# The port of a Destiny 2 weapon to Fallout 4

This is the procedure for the next Destiny 2 weapon: the order of the work, the gate of each
step, and what five ports showed about the two games.

* [destiny/port/README.md](../../destiny/port/README.md) is the reference of the tools. It
  has every key of a set file, every step of the converter, every check, and a section for
  each ported weapon. When you need a value, that file and the set files in
  `destiny/port/sets/` are the source.
* [destiny/extract/README.md](../../destiny/extract/README.md) covers the extraction tool.
* [troubleshooting.md](troubleshooting.md) lists the signs of each known problem.
* [overview.md](overview.md) has the rules for each source.

Run every command from the repository root. The source files are in `destiny/port/`:
`d2fo4.py`, `sets/`, `tools/`, `check/` and `templates/`. Results go below
`data/destiny/port/`, into `extract/`, `work/`, `out/`, `rig/` and `validation/`, which git
ignores. The esx project of a mod is `data/mods/NAME`. Its hand-written files live in
`mods/NAME`.

## The five ports

| Weapon | Kind | Template | Vanilla record | What was new in this port |
| --- | --- | --- | --- | --- |
| The Last Word | hand cannon | `revolver44` | `44` | Mapping the two rigs, the finger rules, the gun parts, the clip format |
| Khvostov 7G-02 | auto rifle | `combatrifle` | `CombatRifle`, automatic receiver | Each state's clip from the graph, a state with no clip, moving the sight |
| Hammerhead | machine gun | `combatrifle_parts` | `CombatRifle`, automatic receiver | 12 moving parts, automatic fire from one shot, dyes and shaders, a glass on a moving part |
| The Chaperone | shotgun with a lever | `combatrifle` | `CombatShotgun` | A reload from three states, one reload clip per count of rounds, additive third-person clips |
| The Huckleberry | submachine gun | `combatrifle` | `CombatRifle`, automatic receiver | Clips of a different rig, part motion in a second clip, a glass with bright colors |

The sight glass and reticle of Hammerhead and the Khvostov, and the third-person reload of
the first three guns, came after the first-person ports of those guns. The mods
`TheLastWord`, `Khvostov` and `Hammerhead` hold one weapon each. `TexMechanica` puts The
Last Word, The Chaperone and The Huckleberry in one plugin.

A weapon of a kind in this table needs a set file, an item file and a behavior source. A new
kind, such as a bolt action, a bow or a sword, needs programming. The second weapon in the
table needed new code in eight places. No command writes a first set file from the state
table.

## The procedure

Do the steps in order. Each one leaves a result you can examine before you start the next.
The times come from the chat, where an AI agent worked without a pause.

### 1. Prepare (one time)

```sh
cp -n config.example.toml data/config.toml   # only when the file is not there; then give blender, esx, fo4_data, proton and destiny_game in it
./port destiny setup                         # the environment of d2x, for the extraction
./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif    # the Fallout 4 skeleton
./port fnv make-rig --arm-meshes             # the arm meshes of Fallout 4, for the check programs
./port destiny make-rig                      # the vanilla clips of the templates, into data/destiny/port/rig/
./port doctor destiny                        # each setting and each necessary file: there or missing
```

The environment variables `BLENDER`, `ESX_BIN`, `FO4_DATA` and `PROTON_DIR` override the
values in `data/config.toml`. The tools only read the game and never change its files. If
`data/config.toml` already exists, edit it instead of copying the example over it.
[getting-started.md](../getting-started.md) says what each command makes and where to get
esx.

**Gate.** `./port doctor destiny` prints `Result: each setting and each check is ok.`

### 2. Extract the weapon

```sh
E=data/destiny/port/extract/the_chaperone
./port destiny find "Chaperone"                    # the name and the hash of the item
./port destiny extract "The Chaperone" --arms "Ancient Apocalypse Grips" --out data/destiny/port/extract
./port destiny states $E/manifest.json -o $E/states.json
./port destiny dyes "The Chaperone" -o $E/dyes.json
./port destiny reticle "The Chaperone" -o $E/sight.json
./port destiny third $E/manifest.json              # prints the third-person states, writes $E/third_person/
```

`states.json` gives the clip of each game state: idle, ready, put_away, fire,
iron_sight_idle, iron_sight_fire, the reload states and the sprint states. These are your
candidates for the set file. A state whose name is not a known word shows only its hash, as
the three reload states of a shotgun do.

The extraction can write more than one first-person file. The gun's row in the pattern
entity then names the rig entity of the gun. The Khvostov has three files and one of them is
correct, see [destiny/port/README.md](../../destiny/port/README.md#the-khvostov-7g-02).
`./port destiny notes weapon-tags $E/manifest.json` prints the rows.

Two of these commands can stop without a fault. `./port destiny reticle` stops with "has no
part in the stages transparent and reticle" when the gun has no glass.
`./port destiny third` stops with "the graph has no state reload for this weapon" for a
shotgun, because its reload is three states. The reference of the tools covers that under
"The reload of a shotgun".

**Time.** `find` takes 5 s. `extract` takes 30 s, or 2 minutes 10 seconds the first time,
when it searches for the player body entity. The Khvostov took 3 minutes from the request to
the complete extraction.

**Gate.** `manifest.json` and the first-person `.glb` file exist. `states.json` has a clip
for `idle`, `ready`, `put_away` and `iron_sight_idle`, and for the reload or its three
states. If a state has no clip, as `fire` of the Khvostov, note that the clip must come from
`[synth]`.

### 3. Examine the data before you write the set file

The last two ports spent a long time on facts that this step shows in minutes. In the chat
it took 20 minutes for two guns, before it was a written procedure. Check these points:

1. The gun must be in the hand. In every clip you plan to use, the gun bone `b_handle` must
   sit on the grip bone `b_r_grip`:

   ```sh
   ./port destiny check gun-on-grip data/destiny/port/extract/NAME/manifest.json
   ./port destiny check gun-on-grip data/destiny/port/extract/NAME/manifest.json --clip CLIP --clip CLIP2
   ```

   The first form prints one line per full-pose clip with its frames, node count and
   distance, then counts the clips with the gun on the grip bone for each node count. With
   `--clip` it checks only those clips and exits with 1 if one of them has the gun more than
   0.001 m from the grip bone. For The Huckleberry the last lines are
   `2 of 59 full-pose clips have the gun on the grip bone`, `clips with 76 nodes: 2 of 37`
   and `clips with 77 nodes: 0 of 22`. That run, on 2026-10-06, took less than one second.

2. Look at the parts. For each weapon bone you want its vertex count, the box of its
   vertices and its motion in each clip.
   `python3 destiny/port/tools/d2bake.py FILE.glb --clip CLIP -o data/destiny/port/work/NAME/probe`
   writes the matrices. A bone with no vertex needs no Fallout 4 bone. The `parts` step of
   the converter prints one `[parts]` line per shape, with its bone and vertex count. Before
   you have a set file, the converter takes single clips instead, with `--clip CLIP=NAME`,
   `--template`, `--hold`, and `--work` for a scratch work folder:

   ```sh
   ./port destiny convert FILE.glb --clip IDLE_CLIP=WPNIdleReady --template combatrifle \
       --hold IDLE_CLIP:0 --work data/destiny/port/work/NAME/probe parts
   ```

   This form comes from the program text in `destiny/port/d2fo4.py`. Nobody ran it for this
   document.
3. Find the clips that move the parts. A part can move in the clip of the hands, in an
   additive clip with the same frame count, or in a clip of the gun entity, listed under
   `weapon_clips` in the manifest.
4. Check the poses at both ends of each clip. Compare the last frame of each clip with the
   first frame of the idle. A clip that does not start or end in the hold pose is one part
   of a sequence.
5. Make pictures.
   `./port destiny video FILE.glb --clip CLIP --columns 8 --width 640 --out data/destiny/port/work/NAME/probe/sheet.png`
   draws frames of one clip of the file. Read the motion from the pictures, not from the
   bone names.
6. Check that the left hand is on the gun.
   `./port destiny pose data/destiny/port/extract/NAME/manifest.json --measure --hold CLIP:0`
   prints how far each Destiny hand is from the gun in the hold pose. A hand that holds the
   gun has many vertices nearer than 0.5 cm. If the left hand has none, the clip belongs to
   the weapon class and the gun needs a pose clip. `--list` prints the candidates, which are
   the short additive clips with offsets of the left hand, and `--measure --pose TAG`
   measures one. [destiny/port/README.md](../../destiny/port/README.md#the-left-hand-on-the-gun)
   has the commands. "0 percent" was the sign for The Chaperone only. The Huckleberry had
   12.4 percent and was still wrong, with its left wrist 2.5 cm from where a clip of this
   gun puts it. So compare the hold pose with a clip of the gun itself, if the file has one.

**Gate.** For each clip you know three things: that the gun is 0.000 m from the grip bone or
that you need `[gun] rest = true`, which clip moves each part, and whether the clip starts
and ends in the hold pose. And in the hold pose the left hand has vertices nearer than
0.5 cm to the gun, or you have a pose clip.

### 4. Select the template and the vanilla record

The template, `destiny/port/templates/NAME.toml`, gives the weapon bones, the sounds and the
pose of the body. The vanilla record gives the behavior graph, the ammunition and the
third-person clips of the grip. A long gun uses `combatrifle`, because the combat rifle and
the combat shotgun share their graphs and clips under `AnimsCombatShotgun`. `combatrifle`
has 11 weapon bones. A gun that needs more uses `combatrifle_parts`, which has 13 bones,
all that the skeleton has.

```sh
esx item new weapon RECORD --standalone --all-parts -o FILE      # the values and the parts of a vanilla weapon
esx record show Fallout4.esm RECORD                               # each field
./port destiny measure-template data/destiny/port/rig/NAME CLIP ...   # only for a new template file
```

**Time.** None if the template exists. The combat rifle template took 6 minutes, including
the extraction of its clips.

**Gate.** The template has a Fallout 4 bone for every moving part that has vertices. The
limit is 13 weapon bones.

### 5. Write the set file, in two passes

The first pass covers `template`, `hold`, `sighted`, `[roles]` or `[bones]`, `[clips]`,
`[synth]`, `[static]`, `[hold_end]` and `[events]`. Add `[gun]`, `[hand_pose]`, `[auto]`,
`[compose]` and `part_rest` when the data from step 3 needs them. Start from a copy of
`destiny/port/sets/khvostov_7g_02.toml`.
[destiny/port/README.md](../../destiny/port/README.md#the-keys-of-a-set-file) explains each
key, and "The Fallout 4 clip of each state" below has the clip names. Then run:

```sh
W=data/destiny/port/work/NAME
./port destiny convert FILE.glb --set destiny/port/sets/NAME.toml bake parts
./port destiny convert FILE.glb --set destiny/port/sets/NAME.toml retarget hkx install
./port destiny points $W/parts.json --poses $W/fo4/poses/SIGHTED_CLIP.npz
```

Check the output:

* In `[parts]`, each shape is on the Fallout 4 bone you expect and the box of the gun has
  the size of the gun. The Chaperone is 48.6 units long, which is 69 cm.
* In `[retarget]`, `wrist` and `weapon` are 0.00 units.
* In `[hkx]`, `pos err` is below 0.02 units and each reload has the events you expect.
* Check the finger joints of each clip before you look at any picture:
  `./port destiny check fingers data/destiny/port/out/NAME/WPNReload.hkx --bake $W/bake/CLIP.npz --vanilla data/destiny/port/rig/combatrifle`.
  `--vanilla` is the folder with the vanilla clips of the template. It defaults to the
  folder of `revolver44`, and both rifle templates use the folder `combatrifle`. In the M77
  port this check found a finger turn of 170 degrees at once, after the user had already
  seen it in a picture.
* Render the source beside the result:

  ```sh
  D=data/destiny/port
  ./port destiny check render --glb FILE.glb --clip CLIP --poses $D/out/NAME/WPNReload.hkx \
      --parts $D/work/NAME/parts.json --out DIR --template combatrifle --frames 0,10,20,30 --views fp --kinds src,fo4
  ```

* Look at the hold pose from more than the first-person camera. Give the idle clip, its HKX
  file, frame 0 and the views `fp,gun_left,gun_right,l_thumb,l_palm,r_thumb,r_back`. In the
  chat, the first check of each gun was the hold pose from the camera and from both sides of
  the gun.

The second pass adds `[sight]`, `[model]`, `[model.sight]` and `[third]`.
`./port destiny points` prints the muzzle, the eye point and a map of the sight.

Every name the Fallout 4 graph asks for needs a clip. For a name the mod lacks, the game
plays the vanilla clip with the hands of the vanilla gun: `WPNIdleReadyA` to `D`,
`WPNIdleSightedWobble`, `WPNEquipFast`, `WPNFireSingleReadyA` and `B`.

**Time.** 3 seconds for one clip. About one minute for the first-person steps of the two
sets of The Chaperone and The Huckleberry.

**Gate.** The four values above are in range. The pictures show the hands on the gun. Each
rule in the set file carries the measurement behind it as a comment, and the word "choice"
where it is one.

### 6. The model, the materials and the sight

```sh
./port destiny model FILE.glb --set destiny/port/sets/NAME.toml --mod NAME      # writes into data/mods/NAME
```

The program reads `data/destiny/port/work/NAME/parts.json`, so do step 5 first.

* The `[model]` line of each texture set prints the percent of pixels with a dye. At 0
  percent a dye changes nothing, as for The Last Word and The Huckleberry. At a large value,
  such as the 93 percent of Hammerhead, the gun needs `dyes = "dyes.json"` in `[model]`.
  [destiny/port/README.md](../../destiny/port/README.md#the-dyes-and-the-shaders-of-destiny)
  covers the shader parts.
* If the sight has a glass, read the pixel shader of each glass material with
  `./port destiny shader-text data/destiny/port/extract/NAME/sight/TAG_ps.dxbc` and write
  its rule into the set file as a comment. Look at each channel of the plate textures. The
  state of a glass's inputs is a choice, so write that down too.
  [destiny/port/README.md](../../destiny/port/README.md#the-glass-of-the-sight-and-the-reticle)
  describes the two sights that are done.
* The program prints the place of the reticle in weapon space. That is the aim point. Put
  it into `point` of `[sight]`, then run the steps `retarget hkx install` again.

**Time.** 14 minutes for the complete sight of the Khvostov, including the game test and the
documents. The first sight, on Hammerhead, took 52 minutes.

**Gate.** The line `[model] sight: the aim point of [sight] is ...` reports 0.02 units or
less from the center of the reticle and does not have the text
`THE CLIPS IN THE SIGHTS DO NOT AIM THROUGH THE RETICLE`. After you change `point`, only the
clips in the sights have new bytes. That was 5 of 27 for both the Khvostov and Hammerhead.

### 7. The third-person reload

Fallout 4 has few third-person clips that belong to a weapon: the reload, a hold pose called
`WPNAssemblyPose`, and two clips of the gun parts. Every other third-person clip belongs to
the grip. Tell the user this before you start.

```sh
D=data/destiny/port
./port destiny convert FILE.glb --set destiny/port/sets/NAME.toml third \
    --third-output data/mods/NAME/behavior/NAME/animations/third_person
./port destiny check third-sheet $D/extract/NAME/third_person/reload.npz $D/work/NAME/third/poses/WPNReload.npz OUT.png
```

Compare the frame count of the third-person reload with the first-person reload. A very
different count can mean the reload of a different weapon class. In the `[third]` line of
the output, read `shoulder shift` and the count of frames with the right hand on the grip.
A large shoulder shift needs `gun = "source"`.
[destiny/port/README.md](../../destiny/port/README.md#the-third-person-clips) has each rule,
and
[the part for a shotgun](../../destiny/port/README.md#the-reload-of-a-shotgun-and-a-gun-with-no-clip-of-its-parts)
covers `[third.compose]`, `[third.hold_end]`, `silent` and `[third.power_armor]`.

**Time.** 80 minutes for the first three guns, including the new tools. Nobody timed one
gun with the finished tools.

**Gate.** In the `[third]` line, `left hand to gun` is 0.0000 units. The shoulder shift is
small, 0.00 to 0.08 units for four of the five ports, or the set file has `gun = "source"`.
The Chaperone is the exception. It has `shoulder shift 2.85` and `bone length 0.9111`
without a `gun` key, a limit that its game test passed with. The first-person clips kept
their bytes. The `third` step uses results of the first-person steps, so changing the
first-person clips changes the third-person clips too.

### 8. The mod project, the build and the byte checks

A project has `esx.toml`, one item file per weapon in `items/`, and one behavior source per
weapon, `behavior/NAME/NAME.bhv`, with its own prefix. Start from a copy of the files in
`mods/TexMechanica`. These hand-written files live in `mods/NAME`, in git.
`./port mod build NAME` copies them into the project `data/mods/NAME`, where the convert
commands wrote the clips and the model, and runs `esx build` there. See
[mods/README.md](../../mods/README.md).

```sh
./port mod build NAME --update-lock
esx --data "/path/to/Fallout 4/Data" plugin check-weapons data/mods/NAME/build/release/NAME.esp
esx --data "/path/to/Fallout 4/Data" scene weapon data/mods/NAME/build/release/NAME.esp WEAPON
esx --data "/path/to/Fallout 4/Data" render weapon data/mods/NAME/build/release/NAME.esp WEAPON --sheet -o data/mods/NAME/docs/WEAPON.png
```

What the ports found out about the records:

* A long gun needs `weapon NAME like AnimsCombatShotgun` in the behavior source and
  `remove_keywords = ["AnimsCombatRifle"]` in the item file. With `like AnimsCombatRifle`
  the build stops, because that keyword has no rules for power armor.
* A copy of the vanilla .44 needs `flags = { "Bolt Action" = false }`, or a hammer clip
  plays after each shot.
* `reload_seconds` in the item file is the time of the `reloadEnd` event in `WPNReload`, not
  the length of the clip. That is frame 102 of 127 for The Last Word, 3.4 s, and frame 217
  of 226 for The Chaperone, 7.2333 s.
* For one reload clip per count of rounds, write one line `when ammo == N play CLIP` per
  count in the behavior source.
* An item file can set a field it has no key for, with
  `set = { 'FNAM\# Projectiles' = 1, 'DNAM\Attack Delay' = 0.857 }`.
* The damage, the capacity and the time between two shots are choices. The tools do not
  read Destiny's values. Say so in the item file and in the document of the mod.
* The clips play at the speed of the Destiny files, and no key of a set file changes that.
  For a faster or slower reload, the esx document `docs/BEHAVIOR.md` has a line `speed 1.5`,
  or `speed reloadSpeedMult * 1.5`, for the `reload` block of a behavior source. No mod in
  this repository has such a line, and nobody tested it here. Do not change
  `reload_seconds` for this.

The byte checks:

```sh
./port destiny convert FILE.glb --set destiny/port/sets/NAME.toml -o data/destiny/port/work/NAME/second_run
# then compare each .hkx file of second_run with the clips of the mod project (cmp)
./port destiny regress                       # each earlier weapon, after a change of a tool
```

`./port mod build` prints the sha256 of each release file. `./port baseline check` compares
every stored result in `data/`, the baseline clips and the release of each mod, with
`baselines.sha256`. That shows a baseline that a command replaced. For a new mod it reports
the new files as "not in the list".

**Time.** 2 minutes for the build and the three checks of the Khvostov, including one
keyword correction.

**Gate.** The build reports 0 issues and 0 warnings. `check-weapons` reports 0 findings.
`scene weapon` reports 0 findings, or 2 notes for the two effect materials of a sight. The
second run gives the same bytes. `./port destiny regress` prints 0 clips that differ, or you
can name each clip that changed and say why. `./port baseline check` prints `0 different`.

### 9. The numbers of each clip and the hands, before the game

```sh
V=data/destiny/port/validation/NAME
./port destiny check validate FILE.glb --set destiny/port/sets/NAME.toml --out $V --clips CLIPS --no-video
./port destiny check touch-table FILE.glb --set destiny/port/sets/NAME.toml --clips CLIPS --out $V/hand_distance.txt
./port destiny check validate FILE.glb --set destiny/port/sets/NAME.toml --out $V --clips CLIPS --left-hand --only WPNReload
```

The first port of The Chaperone ran the game test before this step, and the user then found
in a game picture that the left hand did not touch the gun.

Add the weapon to `destiny/port/regress.toml` now, with the clip folders of the mod as its
baseline. From then on `./port destiny regress` finds every later change to its clips.

The videos of one clip take about 10 minutes. So make the numbers of each clip first with
`--no-video`, then the hand distance, then the videos of the clips that someone has to
watch, which are one reload and the idle. [checks.md](checks.md) says how to read the
numbers. Look at each hand in pictures of the hold pose and of the reload, from more than
the first-person camera, as in step 5.

**Gate.** `summary.txt` has one line per clip. No finger joint bends back. The largest
distance of a gun vertex from the source is at most about 0.015 units. The five ports have
0.009 to 0.015 as their largest value. `hand_distance.txt` shows each hand on the gun in the
hold pose, where the lowest value of the five ports is 5 percent of the vertices nearer
than 0.5 cm. A value above 0 does not prove where the hand is, as The Huckleberry showed in
step 3.

### 10. The game tests

Do this step only if the user asked for a game test or allowed one.
[game-test.md](game-test.md) has the rules and explains how to read a trace.

```sh
esx probe status                                               # the probe has one session at a time: look first
./port destiny game session NAME LABEL                         # builds, starts a session, prints its ID
./port destiny game record --session ID --weapon WEAPON --capacity N [--auto] --out DIR
./port destiny game third --session ID --weapon WEAPON --capacity N --record --out DIR
./port destiny game reloads --session ID --weapon WEAPON --capacity N --out DIR     # one clip for each count
./port destiny game sight --session ID --weapon WEAPON --capacity N --out DIR        # pictures: the hip and the sights
esx probe stop --session ID                                    # only the ID that your start command printed
```

`./port destiny game all --session ID ...` runs the tests in this order, for every weapon of
a mod, in one session. Always pass `--session ID`. Without `--session` the command takes the
ID from the session file, and all users share that one file. If the session file holds a
session with a different label, `./port destiny game session` leaves that session running
and exits with 1. `--take-over` stops that session, so ask the user first. For a release
that already passed a game test, pass `--no-build`. The session then has the bytes on
record.

Look at each recording before you use it, with `./port destiny check strip VIDEO OUT.jpg`.
In the pictures at the hip, look at each hand, the gun and the sight, even if you took the
picture for the sight. A check with pictures before the first recording finds a fault
early. Do it in a session of its own. In one session the program for the sight pictures ran
first, and every first-person test after it had one failed `ammo.set` op.

**Time.** A session starts in 20 seconds. A first-person recording is 78 to 92 seconds long,
and a third-person recording 109 to 122 seconds. Nine tests in one session took about 17
minutes.

**Gate.** 0 failed ops. You looked at frames of each recording. The trace has the clips and
the events you expect. The release has the same sha256 before and after the tests, which
`--mod NAME --tested FILE` of `game all` compares. `esx probe status` shows no session and
no game process.

### 11. The documents

Write the weapon's section in `destiny/port/README.md` and the `README.md` of the mod,
`mods/NAME/README.md`. Cover what the mod has, the choices, what is proved, what is not
proved, and the limits. The weapon is already in `destiny/port/regress.toml` from step 9.
For a new sign, add a row to [troubleshooting.md](troubleshooting.md). When the user accepts
the port, run `./port baseline update`, which records the new clips and the new release in
`baselines.sha256`. Commit that file with the port.

**Gate.** Every statement in the documents names its command or its file.
`./port baseline check` prints `0 different` and reports no file that the list does not
have.

## The Fallout 4 clip of each state

| State of Destiny | Fallout 4 clip |
| --- | --- |
| `idle`, the first clip | `WPNIdleReady` |
| `idle`, the second and the third clip | `WPNIdleReadyA` to `D` |
| `iron_sight_idle` | `WPNIdleSighted`, `WPNIdleSightedWobble` |
| `fire` | `WPNFireSingleReady`, `A`, `B`, and with `[auto]` `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack` |
| `iron_sight_fire` | `WPNFireSingleSighted`, and with `[auto]` `WPNFireAutoSighted` |
| `ready` | `WPNEquip`, `WPNEquipFast` |
| `put_away` | `WPNUnEquip`, with `[hold_end]` |
| `reload_empty`, `reload_full`, `reload_special` | `WPNReload` |
| `reload_enter`, `6C41757C`, `chamber_1` (a shotgun) | `WPNReload1` to `WPNReloadN` and `WPNReload`, with `[compose]` |
| `sprint_loop` | `WPNSprint`, or `[synth]` when the clip is one pose |
| `sprint_enter`, `sprint_exit` | No clip. The Fallout 4 graph blends. |
| No state | `[synth]`: `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNJumpImpactLand`. `[static]`: `WPNIdleGunDown`. |

The melee, grenade and mine clips stay vanilla. So do the additive clips of the graph:
jiggle, pitch, turn and jump.

## Facts about the data of Destiny 2

* The graph says which clip a weapon uses. The clip list does not. A first-person file has
  91 to 133 clips, and most of them belong to other weapons of the class.
  `./port destiny states` reads the graph with the tags of the weapon. The weapon tag is
  the content group of the gun, as for the Khvostov, or the tag of its class, as for
  Hammerhead. The row of the pattern entity says which one.
* A clip whose node count differs from the rig's is a clip of a different rig. In the files
  of The Chaperone, the Khvostov and Hammerhead, every full-pose clip with the node count of
  the rig has the gun on the grip bone (32, 66 and 23 clips), and no clip with a different
  node count has it (32, 13 and 30 clips). The state clips of these three guns have the node
  count of the rig. The Huckleberry is the exception. Its rig has 76 bones, its state clips
  have 77 nodes, and only 2 of its 59 full-pose clips have the gun on the grip. The cause in
  the decoder is not known. In every correct clip the gun bone has no offset from
  `b_r_grip`, so the rule `rest` is safe. Measure the gap for each clip as in step 3,
  because the node count alone does not find the fault.
* A bone name is not a part name. `b_pump` of The Chaperone is a lever. Its vertices are a
  thin loop below the receiver, and it turns 99 degrees. `bone_D7A79DD5` of The Huckleberry
  moves in the clip of the shot and has no vertex. Count the vertices and look at a picture.
* A part that the game hides sits far away. When Destiny does not show the shell of The
  Chaperone, the shell is behind the camera or 1.4 m away. A blend between two clips must
  not move such a bone, so name it in `cut`.
* The extraction shows an additive clip on the first frame of one full-pose clip, and that
  can be a clip of a different gun. Only the motion against the additive clip's own first
  frame is data. Put that motion on the rest place of the bone. `[gun.parts]` does this
  with translation = rest + source(f) - source(0) and rotation = rest x inverse(source(0))
  x source(f).
* A clip of the class does not hold every gun of the class. The left hand of The Chaperone
  is 0.9 cm from the gun in every clip of the shotgun class. The file of each gun has short
  additive clips, 2 or 3 frames of offsets only, that no state of the graph names. Some of
  them have one pose of the left hand and its fingers, and the correct one puts the hand on
  the gun. For The Huckleberry the pose clip is the difference between the idle of the class
  and a clip of this gun with one pose. Two candidates of The Chaperone have the same
  offsets with opposite signs, and the name does not say which one is correct, so measure
  each candidate.
* Two clips are a pair when the same frames move. In the reload of The Huckleberry, the
  housing of the barrel moves from frame 3 to frame 61 in the clip of the parts, and the
  left hand is off the gun from frame 3 to frame 61 in the clip of the hands. That is the
  evidence that the two clips are one reload. No file says so.
* The reload of a shotgun is three states: `reload_enter`, one state for one shell, and
  `chamber_1`. The shell state is `6C41757C`, and its name is not known. The shell clip does
  not end in the pose it starts in. The hand is out of the view at both ends.
* A state can have no part motion. In the first-person file, the shot of The Chaperone at
  the hip does not move the lever. The shot in the sights does.
* The state `idle` has three clips, with the thresholds 0.962, 0.981 and 1.0. The agent
  read them as the limits of a random choice, 96, 2 and 2 percent. The game data does not
  say what the numbers are.
* State names are FNV-1 hashes of words. Found so far: `reload_1` is `EB22859A`,
  `reload_enter` is `12CFA0E5`, `chamber_1` is `FACB2E5D` and `sprint_ready` is `DB28BEA1`.
  To find a name, hash a list of candidate words.
* The third-person clips are in the player body entity, which has 72 bones and one graph
  with 332 states. They are not in the extraction of the gun. Dimension 3 of a state is the
  weapon tags and dimension 1 is the stance. The stance `811C9DC5`, the hash of an empty
  word, stands for every stance. The clips move the upper body only. The gun entity has its
  own graph with the same state names, and that graph gives the clip of the gun parts.
  Pairing by frame count gave the same clips for three guns. For The Chaperone it gave a
  clip that is in no state of the gun's graph.
* Third-person clips of a shotgun are additive, and the extraction's test for an additive
  clip does not find all of them. A clip whose first or last frame has no offset is
  additive.
* The colors of a gun are not in its textures. The dyes and the gear shader give them. See
  `./port destiny dyes` and `destiny/port/tools/d2shade.py`. The Last Word and The
  Huckleberry have 0 percent of pixels with a dye. Hammerhead has 93 percent.
* A sight glass is in two more render stages, `transparent` and `reticle`, which the
  extraction does not have. Its materials are small programs. The pixel shader gives the
  rule, and an expression program calculates colors from inputs that the files do not name.
  You have to pick one state of the inputs, and that is a choice.

## Facts about the two rigs and the clips

| Fact | Value |
| --- | --- |
| The file of Destiny | glTF, +Y up, +Z forward, +X to the left of the player, meters, 30 frames per second, FK only |
| Fallout 4 | +Z up, +Y forward, +X to the right, game units |
| The scale | 1 m is 69.99125 units, the true scale. 1 unit is 1.43 cm. |
| The size of the two rigs | The upper arm and the forearm agree to 6 percent, the palm to 5 percent. The first bone of the ring finger is 22 percent longer in Destiny. The Fallout 4 palm is 0.8 units wider. |
| The camera bone of Destiny | `b_utility`, at (0, 1.66, 0). It moves up to 4 cm in the reload of The Last Word (2.9 units). |
| The gun bone | `b_handle`, a child of `b_r_grip`. In each correct clip it is on `b_r_grip` with no offset. |
| The bones of each rig | The Last Word 80, the Khvostov 76, Hammerhead 87, The Chaperone 77, The Huckleberry 76 |
| The Fallout 4 skeletons | First person 94 bones. Third person 95, the same 94 and `CamTarget`. 13 weapon bones. |

* The arms and hands of the two rigs are close in size. The fingers are not, so they need
  the finger rules.
* Destiny's camera bone, `b_utility`, goes on the Fallout 4 camera bone. The game then
  shows the picture that Destiny shows, and a check picture can compare the two.
* A first-person clip of Destiny has useful poses only for the arms and the gun. Every
  other bone takes the pose of the template.
* The bind pose of the file is not a hold pose, because the weapon is not in the hand
  there. Use frames of a clip.
* The clip format matters. With 40-bit rotations the muzzle moved 0.03 to 0.09 units from
  frame to frame, more than the motion of an idle. The vanilla clips have 48 bits.
* A clip with vanilla weapon motion is correct for a small motion: walk, run, jump, gun
  down, sprint. It is wrong for a large turn of the gun, so the melee clip is not converted.
* Hammerhead uses 12 of the 13 weapon bones of the Fallout 4 skeleton.
* When a tool changes, make the clips of every earlier gun again and compare. The largest
  difference must be 0.0. `./port destiny regress` does this.

## Facts about the graphs of Fallout 4

* The first-person graph asks for clips by name, and for a clip the mod lacks it plays the
  vanilla clip. `WPNIdleSightedWobble` must be the sighted idle of the weapon. The put-away
  state removes the gun 0.233 s before its clip ends. The combat rifle has two animation
  keywords, and `AnimsCombatRifle` must go. The vanilla .44 has the flag `Bolt Action`,
  which plays a hammer clip after each shot.
* In the draw, the graph starts the blend from the draw clip to the idle 0.5 s before the
  draw clip ends. The gun is ready 0.57 s after the start.
* The first-person graph of a gun has no hand IK, so the game does not correct a hand that
  is off the gun.
* Third person has few clips that belong to a weapon: the reload, the hold pose
  `WPNAssemblyPose` and two clips of the gun parts. Every other clip belongs to the grip.
* In third person the left hand is on the bone `WeaponIKTargetL`. The game puts the hand
  there with IK in every clip. `WPNAssemblyPose` gives the hand's place for each clip of the
  grip. With the bone at its rest place, the hand goes to the grip of the gun.
* The third-person graph ends a reload 0.5 s before the clip ends. The clip node has three
  triggers timed from the end of the clip: `reloadEndSlave` at 0.533 s, `reloadEnd` at
  0.5 s, and one more at 0.467 s. If the event of the clip comes first, it ends the reload.
  A clip that moves until its last frames needs 16 more frames.
* The third-person graph has a second player for the gun parts,
  `WeaponSlave_StateMachine`. In the vanilla graph its reload state and the reload state of
  the body share one clip node. For a clip with a new name, esx makes a new node in the
  state of the body only, so the game also plays `WPNReload`, with its events.
* In the first-person view the events come from the first-person clip only. The
  third-person reload of The Chaperone is 1 s shorter, and the reload still ends at the
  event of the first-person clip.
* One reload clip per count of rounds works in both views, with the lines
  `when ammo == N play CLIP` of an esx behavior source. Each line needs its clip in every
  view that has the same graph, which means the body and the body in power armor.
* `weaponFire` is at frame 0 of each shot clip. `reloadComplete` fills the gun, and
  `reloadEnd` ends the reload state. For a gun with a magazine, the reload events come from
  the motion of the parts: `ReloadMagOut` and `ReloadMagIn` from the magazine,
  `reloadComplete` 2 frames after the magazine is in, and `ReloadBoltOpen` and
  `ReloadBoltClose` from the bolt. A composed clip takes its events from `[piece_events]`
  and `[events]` only.
* To learn facts like these, run `esx behavior explain reload --like KEYWORD`,
  `esx hkx events FILE --event NAME` and `esx hkx show FILE --selector 'object(N)'` on the
  built graph. `./port destiny game trace` gives the probe's trace of the clips and events
  that the game started.

## Facts about the model and the sight

* A Fallout 4 material has no metal value. A specular value from the reflectance of the
  surface gives a dark metal. A high specular value for each metal pixel gives a light gray
  gun.
* esx makes no new effect shader. The glass and the reticle are a second part of the weapon
  with a vanilla mesh as the template, and the gun has the connect point `P-Scope` on the
  bone that carries the glass.
* A template shape keeps 16-bit vertex values. Put the place of the shape at the center of
  its new geometry.
* The reticle has the size of an angle, not the size of its quad. The vertex shader gives
  the distance from the camera: 2.25 m for Hammerhead (0.44 degrees), 1.1 m for the Khvostov
  (0.91 degrees), 3.35 m for The Chaperone and 2.65 m for The Huckleberry. Used as a part of
  the gun, the quad of the file was 5 times too large.
* A color above 1 makes a glow in Fallout 4. A small dot can have it. A border of 3.0
  around a glass put a haze on the whole glass.
* In Fallout 4 the glass and the reticle show all the time. In Destiny the reticle shows
  only in the sights, and it is on the aim axis, not on the glass.
* `esx render` does not draw an effect material. Only a game test shows a glass.
* The eye point of a clip in the sights is at z 11.55 of weapon space for each rifle, 9.61
  for The Chaperone and 10.34 for The Huckleberry. Destiny aligns the sight of each gun when
  the game runs, so `[sight]` moves every clip in the sights: 2.69 units up for the
  Khvostov, 3.40 down for Hammerhead, 0.76 up for The Chaperone and 0.75 up for The
  Huckleberry.

## What is proved

[destiny/port/README.md](../../destiny/port/README.md#what-is-proved) has the proof of each
weapon, and [checks.md](checks.md) has the numbers. In short:

* On 2026-10-06, after the tools moved into this repository, `./port destiny regress` made
  the clips of the five guns and of the M77 again: 162 first-person clips, 16 third-person
  clips and 6 clips of the power armor, 0 differ.
* `./port baseline check` on 2026-10-06 covered 602 stored files, the baseline clips and
  the releases, with 0 different from `baselines.sha256`.
* All five weapons passed their game tests with 0 failed ops in the chat of 2026-10-06,
  before the move. The `TexMechanica` release in `data/mods/` has the sha256 values of the
  tested release, which are in
  `data/destiny/port/validation/tex_mechanica/release_tested.sha`.

## What is not proved

* `./port destiny check gun-on-grip` from step 3 ran on 2026-10-06 for The Huckleberry and
  for two clips of The Chaperone. It did not run for the other weapons for this document.
  The form of the `parts` step without a set file, also in step 3, was not run.
* The game test commands of step 10. [game-test.md](game-test.md) says what ran in this
  repository, under "The state of the game test programs".
* The `speed` line of a behavior source in step 8 comes from the document of esx. No build
  and no game test in this repository used it.
* Whether the lever of The Chaperone opens in a third-person reload with 1 to 5 shells. No
  picture shows it.
* A body in power armor. It had no game test, and its third-person reload is the vanilla
  clip.
* The walk, run and jump clips in the game. The tests have no move input.
* The reload of The Huckleberry against a picture of Destiny.
* Why the extraction has the gun bone at the origin in a clip of a different rig.
* Why the test goes into the sights 2.1 s after the action.
* Which states of Destiny use the pose clips of a gun, and with which weight. The other
  short additive clips of a gun are not used. They are ramps with 2 keys that look like the
  kick of a shot.
* The melee clip, the other third-person clips of Destiny (`ready`, `fire_1`, the sprint),
  the crouch variant, the clips of a non-player character.
* Emission, iridescence, fuzz, transmission, and the mirror picture of a glass.
* Any look against a picture of Destiny: the materials, the colors of a glass, the size and
  the color of a reticle. There was no reference picture.
* The meaning of the three thresholds of the state `idle`, and of each of the 27 vectors of
  a dye.
* The sound. No test recorded it.
* The weapons workbench, and the mods in the installed game.
* Only one build of Destiny 2 is tested, `86657.20.08.23.1800.d2_rc`.
* The hand measurements in `destiny/port/rig/d2_hands.json` are for the masculine hand mesh.
