---
name: extract-game-weapon
description: Gives the procedure to extract a weapon of Destiny 2 (d2x) or of Marathon (m2x) from the game packages as glTF files with a manifest (model, textures, rigs, clips), to check the files, to find the clip of a game state from the animation graph, and to show a clip as a frame sheet or a video. Use when the user asks to "extract the model and animations" of a weapon, asks "which clip is the reload", "send a video or a sheet" of a clip, asks what a picture of a clip shows, when a port needs the files of a new weapon, or when "./port destiny find" or "./port marathon find" has no row for a name.
---

# Extract a weapon of Destiny 2 or of Marathon

The tools read the packages of the game and write glTF files below `data/`. They do not
change the game folder. Do not start Destiny 2 or Marathon: Marathon has an anti-cheat
program (BattlEye).

## When to use it, and when not

* Use it when the result is the files of the game: a model, clips, pictures, a video.
* For a complete port to Fallout 4: `port-destiny-weapon` or `port-marathon-weapon`. They
  call this skill for their first step.
* For data that the extraction does not read (a new table, a new game build): `decode-game-data`.

## Before the start

Run `./port doctor destiny` or `./port doctor marathon`. Each check must be `ok`. If not:
`set-up-workspace`. The tools were made for one build of each game. A later build can have
other class numbers.

## A weapon of Destiny 2

### 1. Find the item

```sh
./port destiny find "TEXT"
```

Each row has the item hash, the pattern entity and the name. Take the row that has a pattern
entity. A row with no pattern entity is not a weapon (a catalyst, for example).

Gate: one row for the weapon. With no row the exit code is 1: the weapon is not in this game
build (23 August 2020). Hawkmoon is not. Tell the user, and do not take another weapon.

### 2. Extract

```sh
./port destiny extract "ITEM" --arms "Ancient Apocalypse Grips"
./port destiny extract "ITEM" --arms "Ancient Apocalypse Grips" --out data/destiny/port/extract
```

The first form writes into `data/destiny/extract/out/NAME/`. The second form is for a port.
`--arms` adds an armor item (the forearms) to the first-person rig. The hands come from the
player body. An extraction needs 30 seconds, and about 2 minutes the first time.

The folder has `NAME_weapon.glb`, `NAME_first_person.glb` (each first-person clip of the
weapon type, with names `fp_ORDER_TAG`), `NAME_first_person_set.glb` (the clips of the states
of this weapon, with the names of the states), `textures/`, `raw/` and `manifest.json`.

### 3. Check the files

```sh
./port destiny check-glb data/destiny/extract/out/NAME/NAME_weapon.glb --clips 3
./port destiny check-glb data/destiny/extract/out/NAME/NAME_first_person_set.glb --view fp --sheet
```

Gate: the command prints `NO PROBLEMS`. If not, it lists the problems (one armature, each
vertex has weights, finite keys, keys for each bone) and has the exit code 1.

### 4. Find the clip of a state

Do not guess the clip of a state from the bones that move or from a picture. The first
report of the first work named three reload clips from a contact sheet. Two of them were
reloads of other hand cannons. Read the animation graph:

```sh
./port destiny states data/destiny/port/extract/NAME/manifest.json -o data/destiny/port/extract/NAME/states.json
```

`states` of `manifest.json` has the same kind of table, but it does not have each main state
for each weapon (The Chaperone has no `ready`, `fire` or reload there). For each state give
the clip, the count of frames and the weapon tag of the choice.

### 5. Show a clip

```sh
./port destiny video FILE_first_person_set.glb --clip reload --clip "iron_sight_idle=ADS" --out NEW_NAME.png
```

`.png` gives a frame sheet and `.mp4` gives a video (it needs `ffmpeg`). `--clip NAME@N`
plays a clip N times.

Gate: you opened the picture, and you can say what it shows: the clip, the frames, the
camera. The weapon is in the right hand. No part floats. The hands are not at the rest pose.
In `iron_sight_idle` the sight is in the middle of each frame. A clip with `_add` in its name
is additive: it has offsets only, and the picture shows it on the first frame of a base clip.

## A weapon of Marathon

```sh
./port marathon find "TEXT"
./port marathon extract "ITEM" --art "BASE ITEM" --hands data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
./port marathon render data/marathon/extract/out/NAME/NAME_weapon.glb data/marathon/extract/work/NAME.png --views side,quarter
./port marathon regress
```

1. `find` prints `entity ...` or `no entity of its own` for each item. An item with no entity
   is a variant: give its base item with `--art` (the description of the item names it:
   `M77 Omnipositor` is a "Modified M77 Assault Rifle").
2. `--hands` puts the hand mesh of a first-person file of Destiny 2 on the rig. It is not a
   mesh of Marathon. It is there for pictures only.
3. Read the last lines of the output of `extract`: the count of pieces with a place, the
   clips with an error, and "the rest places of the gun parts differ by". A value that is not
   0.000000 says that the arm rig does not have the bones of this weapon: its first-person
   file is not correct (`V75 SCAR`).
4. `render` makes pictures of a file. For a first-person clip: `--action fp_NNN_TAG --frame N`.
5. `states.json` beside the `.glb` file has the clip of each state.

Gate: `./port marathon regress` prints `same` for each stored weapon, and you looked at the
pictures of the weapon file and of some frames of first-person clips.

## Stop and ask the user

* When the weapon is not in the game build.
* When more than one item has the name. `--all` of `./port destiny extract` takes each one.

## Common faults

| Sign | Cause | What to do |
| --- | --- | --- |
| "what is this": the gun is far from the hand in a picture | A bone with no keys kept the pose of the clip before. It was a fault of the export, not of the game data. | It is corrected in the tool. `check-glb` reports "bones without keys". In a Blender program, reset the pose before each clip. |
| The user sees the old picture after the correction | The chat shows a cached copy of a file with the same name | A new file name for each picture that is made again |
| The gun is too far to the right in a first-person picture | The camera was at the head bone | The camera is the bone `b_utility`: its place is the eye point and its +Z axis is the view direction |
| A clip looks like no state of the weapon | The full file has the clips of each weapon that shares the rig | Use the set file, or `states.json` |
| A preview camera points in a wrong direction | The camera setup | Look at each picture before you send it |
| Frames at wrong times in Blender | The scene rate | Set the scene to 30 frames for each second before the import |

## What to report

* The item hash. The weapon bones (each `bone_HASH` with no name). The count of rigs, bones
  and clips.
* The clip of each main state, with its frames and its weapon tag. Each state with no name
  that matters. The pictures.
* What is not proved: the weapon tag rule is proved by pictures on The Last Word only.
* When a second agent starts from the files: make a frozen copy, write each fact with its
  proof, and send a correction with its effects when a fact was wrong.

## More

* [destiny/extract/README.md](../../../destiny/extract/README.md): the reference of `d2x`.
* [marathon/extract/README.md](../../../marathon/extract/README.md): the reference of `m2x`.
* [docs/getting-started.md](../../../docs/getting-started.md),
  [docs/reference/commands.md](../../../docs/reference/commands.md).
