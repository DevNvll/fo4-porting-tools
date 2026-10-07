---
name: port-fnv-animations
description: Gives the procedure to convert the first-person animations of a Fallout New Vegas weapon mod (.kf files and a .nif model) to Fallout 4 clips (HKX) with the tools of fnv/, and to put them into an esx mod project with a game test when the user asks for a mod. Use when the user gives a New Vegas weapon mod or a Nexus archive and says "port this", "I just want the animations to work on fo4", asks for the reload or the clips of a New Vegas gun in Fallout 4, asks about WPNReloadEmpty or a partial reload, or changes the mods PPK or FAMAS.
---

# Port the animations of a New Vegas weapon

One command converts the first-person animations of an extracted New Vegas weapon mod to
the clips of a Fallout 4 gun. The tools make only the clips. They do not make the model, the
textures, the sounds, the records or the behavior graph.

## When to use it, and when not

* Use it for a New Vegas mod with first-person `.kf` files and a `.nif` model.
* Decide the scope with the user first. The first answer to "port this" is the animations.
  Do not make a mod project, attachments or textures unless the user asks. Ask only what the
  tools cannot find.
* The clips fit only the gun of the source mod.
* A weapon that is not a magazine gun (a revolver, a bolt action, a shotgun with single
  shells) needs a new template. That is not done. Tell the user.

## Before the start

1. `./port doctor fnv`. The exit code must be 0. The rig folder `data/fnv/rig` has files of
   the game and of the NVCS skeleton mod. This command makes it one time:

   ```sh
   ./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif
   ```
2. Extract the archive of the mod yourself, into `data/fnv/fixtures/NAME`. The tools do not
   read an archive.
3. Read the readme of the mod for its permissions. Say in the report what it permits.

## Steps

### 1. Check the input

```sh
./port fnv inspect /path/to/MODEL.nif        # the nodes and the shapes
./port fnv inspect /path/to/ANIMATION.kf     # the tracks and the text keys
```

The `.kf` files are in a folder such as `meshes/characters/_male/`,
`meshes/characters/_1stperson/` or `meshes/AnimGroupOverride/NAME/_1stPerson/`.

Gate: the mod has first-person `.kf` files and a model. With no animation file, stop and
tell the user: such a mod uses the vanilla animations of New Vegas. A 3ds Max scene is not an
input of these tools.

### 2. Convert

```sh
./port fnv convert data/fnv/fixtures/NAME --name NAME
```

The tool selects the model (the fewest shapes, then the shortest name), the animation folder
(the folder `_1stperson` with the most `.kf` files), and the template (`pistol10mm` when a
`.kf` name starts with the grip code `1hp`, else `smg`). The clips go to `data/fnv/out/NAME`.

Gate: read what the command prints. Each clip has the source that you expect. Each reload
has its events (`ReloadMagOut`, `ReloadMagIn`, `reloadComplete`, `reloadEnd`) at frames that
fit the motion. Write down the time of `reloadEnd`: it is `reload_seconds` of an item file.

### 3. Correct a value that the tools assume

```sh
./port fnv convert CONFIG show      # the complete data: the values of the file and each default
./port fnv convert CONFIG plan      # the source of each clip and the events of each reload
```

The command of step 2 writes `conversion.toml` into the work folder `data/fnv/work/NAME`.
Write a small file of your own with only the values that are wrong (a clip, a part, the
trigger, an event). [references/fnv-facts.md](references/fnv-facts.md) has the keys.

### 4. Look at the hands

This area has no program that shows the result. The regression compares bytes. It does not
look at the hands. Each hand fault of the first work was found by the user in a picture,
while the game test passed. So before you say that the clips are correct:

* Read the numbers of the retarget step: the wrist error is 0, the arm length error is below
  0.0001, and `max_shoulder_adjustment` is small in each clip where the gun is in the view.
* Look at the clips in the game (step 6) or in an animation tool. Look at each hand in a
  close view, and compare the place of each thumb with the source.
* No finger joint bends to the back of the finger. Only the last thumb joint can, 17 degrees.

Gate: you looked at pictures of each hand in the reload and in the hold pose, or the report
says under "What is not proved" that nobody looked.

### 5. Add the weapon to the regression

`./port fnv regress` converts each folder of `data/fnv/fixtures/` again and compares each
clip with `data/fnv/out/NAME`. Gate: each line is `same`.

### 6. The mod project (only when the user asks for a mod)

`mods/PPK` and `mods/FAMAS` are the models: `conversion.toml` (the name, the template, and
`output = "behavior/NAME/animations/first_person"`), `esx.toml`, `items/`, the behavior
source and `tests/`. The extracted mod is the folder `source` in `data/mods/NAME/`.

```sh
./port mod sync NAME
./port fnv convert data/mods/NAME/conversion.toml
./port mod build NAME --update-lock
```

* The game plays `WPNReloadEmpty` only when the behavior source has the line
  `when empty play WPNReloadEmpty` (see `mods/PPK/behavior/ppk/ppk.bhv`).
* The tools make no model. `out/fo4mesh/parts.json` of the work folder has each shape of
  the gun in the space of its weapon bone: a model must have its shapes at these places. The
  models and the textures of `PPK` and `FAMAS` came from the tools at the tag
  `before-animation-only`.
* The game test is a test plan of esx. Only with the permission of the user:
  `game-test-port` ("A test plan of a New Vegas mod"). Look at each screenshot of the report.

Gate: the build has 0 warnings, and the sha256 of each release file is written down.

## Stop and ask the user

* When the mod has no animation file. "if theres no animation, don'tport it".
* Before you make a mod project that the user did not ask for.
* Before the game starts.
* Before a change of a finger rule: it changes the clips of each weapon at one time, and
  `destiny/port` uses the same solver (`change-shared-tool`).

## Common faults

| Sign | Cause | What to do |
| --- | --- | --- |
| The fingers are in the gun, or open, or a part comes through the palm | Faults of the first versions of the solver | They are corrected in the tool. If one comes back: `fix-hand-pose`. |
| A straight finger with lumps, or a thumb beside its place | The two finger rules are off | `[fingers] min_bend = 0.3`, `skin_center = true` (the defaults) |
| The game does not play the reload of the empty gun | No state for it in the vanilla graph | The line in the behavior source |
| Each clip is different after a run of some steps | The step `parts` did not run | Run each step. Only `install` copies the clips to the output folder. |
| A shorter clip list, with no error | The rig folder has no clip of the template | `./port fnv make-rig` |
| The weapon does not draw in the test game | A fault of the template weapon (the vanilla Deliverer does not draw there) | Test the vanilla template weapon alone first |

## What to report

The count of clips, which clips come from the source and which have the weapon motion of
the template, the source clips that got no clip (a sneak copy, a jam, an empty-gun pose, a
last shot), the time of `reloadEnd`, the permissions of the source mod, and what is not
proved: no command of this repository proves that the clips are correct in the game.

## More

* [references/fnv-facts.md](references/fnv-facts.md): the names, the keys, the events, the
  rules of the solver, the limits.
* [fnv/README.md](../../../fnv/README.md): the reference of this area.
* [docs/porting/fnv.md](../../../docs/porting/fnv.md),
  [mods/README.md](../../../mods/README.md).
