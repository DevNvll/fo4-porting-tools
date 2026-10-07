---
name: port-dyes-and-materials
description: Gives the procedure to give a ported Destiny 2 weapon its colors in Fallout 4 (the dyes of the gun and the gear shader, the conversion to a Fallout 4 material), and to add a shader item of Destiny as a second receiver part, with the tools d2dyes and d2model and the keys dyes and [model.shaders] of a set file. Use when a ported gun has wrong colors in the game (light gray where Destiny is dark, flat gray where Destiny has paint, too bright in daylight), when the user says "make destiny shaders work in the weapons", names a shader such as "Golden Trace", or asks why a Marathon piece is gray.
---

# The dyes, the shaders and the materials

The colors of a Destiny 2 gun are not in its textures. A gun has three dyes, and a shader
item gives it three other dyes. The tools read the dyes from the game packages, do the gear
shader for each pixel, and write Fallout 4 textures.

## When to use it, and when not

* Use it for wrong colors of the gun body, and for a shader of Destiny on a weapon.
* The glass of a sight and the reticle: `port-sight-and-reticle`.
* A shape at a wrong place, or a missing part: `diagnose-port-fault`.

## Before the start

The step `parts` of the converter ran (`data/destiny/port/work/NAME/parts.json` is there),
and the set file has `[model]` with `name`, `muzzle` and `[model.materials]`. The variables
are those of `port-destiny-weapon`: `E`, `G`, `S`. Say how you read a short request: "make
destiny shaders work" was read as two things, the look of the guns and selectable shaders.

## Steps

### 1. Measure which guns the feature applies to

```sh
./port destiny model $G --set $S --mod MOD
```

For each texture set the tool prints one line `[model]` with the percent of metal pixels,
the percent of pixels with a dye, and the mean specular value.

Gate: you know the percent of pixels with a dye. With 0 percent a shader changes nothing:
tell the user, and stop the shader work for that gun. The Last Word and The Huckleberry have
0 percent, the Khvostov less than 0.1 percent, Hammerhead 93 percent of its body.

### 2. Read the default dyes

```sh
./port destiny dyes "ITEM" -o $E/dyes.json
```

Write `dyes = "dyes.json"` in `[model]` of the set file. The file is beside the `.glb` file.

### 3. Read the dyes of a shader item

```sh
./port destiny dyes --list "TEXT"
./port destiny dyes "ITEM" --shader "SHADER NAME" -o $E/dyes_shader_name.json
```

Write one line for each shader in `[model.shaders]`: `GoldenTrace = "dyes_golden_trace.json"`.

### 4. Make the model again

Run the model command of step 1 again. Each shader gets its textures, its materials and its
model file (the name of the weapon + the name of the shader).

Gate: the lines `[model]` of a dark metal have a low specular value. The median specular
value of the body texture is 0.12 for Hammerhead and 0.13 for the Khvostov. A value of 0.7 to
0.9 for each metal pixel gives a light gray gun in the game.

### 5. The item file and the build

Fallout 4 has no dyes. A shader is one more receiver part with the same mesh and its own
textures: see `[part.ReceiverGoldenTrace]` in `mods/Hammerhead/items/10-hammerhead.toml`. Then
`./port mod build MOD --update-lock`.

Gate: the build has 0 warnings. For a gun with no dye, only the texture archive of the
release has other bytes: the plugin and the main archive are the same, and the clips did not
change (`./port destiny regress --only NAME`).

### 6. A game picture of each look

Load `game-test-port`. Use one new session for each shader: a second `item.give` in one
session keeps the first gun, so each part shows the default colors. Do not use
`player.removeitem`: it stopped the game.

Gate: `item.give` with the part gives the part in `mods_attached`. You looked at each picture.
The light of the test cell `QASmoke` gives each dark surface a green tint. The vanilla .44
has the same tint there, so it is not a fault of the material. The test world (`--world`) has
direct daylight: the light parts of two guns were too bright there (a limit, see below).

## A weapon of Marathon

The extraction writes each material as a texture set of Destiny 2, so the model tool reads
it with no change and with no dyes. A `detail` material has seven regions, and the file has
the color of the region 0 only: the game calculates the six others when it runs. So the
muzzle device, the magazine and the sight unit of the M77 are gray. This is a limit, not a
fault of the tools. `./port marathon notes dxil MATERIAL` prints the pixel shader of a material.

## Stop and ask the user

* Before the game starts.
* Before you write a statement such as "as in Destiny": no reference picture of Destiny is here.

## Common faults

| Sign | Cause | Rule |
| --- | --- | --- |
| A dark metal is light gray in the game | A high specular value for each metal pixel, with the reflection of the environment | The specular value from the reflectance (in the tool). `specular` and `occlusion` of `[model]` change the two weights. |
| The light parts of a gun are too bright, with a glow, in direct daylight | Not known. Seen for The Chaperone and The Huckleberry in the test world (`WeapTest`). In the dark cell `QASmoke` the same materials looked correct. | No rule yet: the materials are not corrected for it. Report it as a limit. Do not change `specular` or `occlusion` with no measurement and no game picture of before and after. |
| Flat gray surfaces where Destiny has paint | The colors are in the dyes | `dyes = "dyes.json"` |
| A shader item does not change the gun | The gun has no pixel with a dye, or its dyes are locked (The Last Word) | No rule. Say so. |
| Each shader part shows the default colors in the test | A second `item.give` in one session | One new session for each shader |
| A statement about a shader value is wrong | It was not measured | Measure the built textures before the report. Three statements went away that way: "No dye of these four looks has an iridescence value" was false. |

## What to report

* The percent of pixels with a dye for each texture set, and the dyes of each look.
* The pictures from the game (name the cell and its light), and the files that changed.
* The limits: no emission, iridescence, fuzz or transmission. The size of the detail pattern
  can be different from the game. A colored metal has a reflection with no color. "As in
  Destiny" is from the dye values. The shader parts were tested with the probe, not at the
  weapons workbench.
* The public source of the gear shader formula, and what is your own reading.

## More

* [references/material-facts.md](references/material-facts.md): the data of a dye, the
  formulas, the numbers.
* [destiny/port/README.md](../../../destiny/port/README.md), "The dyes and the shaders of
  Destiny".
* [marathon/extract/README.md](../../../marathon/extract/README.md), "The materials".
* [docs/porting/troubleshooting.md](../../../docs/porting/troubleshooting.md).
