---
name: port-sight-and-reticle
description: Gives the procedure to put the eye on the sight of a ported weapon in Fallout 4, and to make the glass and the reticle of a Destiny 2 sight (a red dot) as a second part of the weapon, with the keys [sight] and [model.sight] of a set file. Use when the sight is below or above the center of the screen in the sights, when the user says "make the red dot work", "the reticle is too big", "its stretched", "the sight has no glass", when there is a haze or a glow on the glass, or when the glass does not move with its cover.
---

# The sight, the glass and the reticle

Destiny 2 and Marathon align the sight of each weapon when the game runs. Fallout 4 has the
sights in the clip. So a clip in the sights needs a move (`[sight]`). A glass and a reticle
are not in the extraction: a second tool reads them, and the model tool makes them a second
part of the weapon (`[model.sight]`).

## When to use it, and when not

* Part 1 (the eye on the sight) is for each weapon with a clip in the sights.
* Part 2 (the glass and the reticle) is for a weapon whose sight has a glass in Destiny 2.
  A weapon with iron sights needs part 1 only (the M77).
* Wrong colors of the gun body: `port-dyes-and-materials`.

## Before the start

The first-person clips convert (`write-set-file`). The variables are those of
`port-destiny-weapon`: `E`, `G`, `S`, `W`. Part 2 needs a game test to prove it:
`esx render` draws no effect material. Ask the user for the permission.

## Part 1: the eye on the sight

1. Print the eye point of the clip in the sights, and a map of the sight:

   ```sh
   ./port destiny points $W/parts.json --poses $W/fo4/poses/SIGHTED_CLIP.npz
   ```

   `--sight TEXT` selects the shapes of the sight by a text in their names.
2. Write `[sight]`: `point` is the aim point in Fallout 4 weapon space, and `clips` are the
   clips of the file in the sights. For a sight with no glass the aim point is the center of
   the window of the housing, or the top of the front post. Write the move as a comment.
3. Run `./port destiny convert $G --set $S retarget hkx install`. The line `[retarget]` of
   each clip in the sights says how far each bone but the camera moves.

Gate: only the clips in the sights changed. Each other clip keeps its bytes
(`./port destiny regress --only NAME` names the clips that differ). In a game picture in the
sights, the aim point is at the center of the picture.

## Part 2: the glass and the reticle

### 1. Read the parts from the game

```sh
./port destiny reticle "ITEM" -o $E/sight.json
```

The output has the meshes of the render stages `transparent` (the glass) and `reticle` (one
quad at the origin), and for each material its two shaders (`$E/sight/TAG_ps.dxbc`,
`TAG_vs.dxbc`), its textures and the values of its constant buffer.

### 2. Read the rule of each material from its shaders

```sh
./port destiny shader-text $E/sight/TAG_ps.dxbc
```

It prints the instructions of one shader. Write the rule of each material as a comment in
the set file, as the set files of this repository do. Look at each channel of the plate
textures ([the rules that the ports found](references/sight-facts.md)).

Gate: for each material you can write "color = ..." and "picture = ..." from the
instructions, and you have the distance of the reticle from the vertex shader (`cb0[11].x`).

### 3. Select one state of the glass

An expression program calculates the colors of a glass from inputs that the files do not
name. Select one state of the inputs. Write in the set file and in the report that the state
is a choice.

### 4. Write `[model.sight]`

Copy the tables of the nearest set file: `file`, `source`, `template`, `template_shapes`,
`glass_scale`, one `[[model.sight.glass]]` for each glass material, and
`[model.sight.reticle]` with `distance` (the meters of the vertex shader), `eye` (the eye
point of part 1), `scale` and `center`. The size of the reticle is an angle, not the size of
its quad.

### 5. Make the model, then put the aim point on the reticle

```sh
./port destiny model $G --set $S --mod MOD
```

Read the lines `[model] sight:`. They have the size of the reticle, the place of its center
in weapon space, and the distance of the aim point of `[sight]` from that center. When the
distance is more than 0.02 units, the tool prints "THE CLIPS IN THE SIGHTS DO NOT AIM THROUGH
THE RETICLE" and the correct `point`. Put that point into `[sight]`, and run
`retarget hkx install` again.

Gate: the model tool prints no such warning. Only the clips in the sights changed.

### 6. The item file and the build

Add the sight part to the item file: a copy of `mod_CombatRifle_Scope_SightsIron`, with the
model `Weapons\NAME\NAMESight.nif` (see `mods/TexMechanica/items/20-thechaperone.toml`). The
model of the gun has the connect point `P-Scope` on the bone that carries the glass, and the
sight has `C-Scope`. Then `./port mod build MOD --update-lock`.

### 7. Test in the game

Load `game-test-port`. Then:

```sh
./port destiny game sight --session ID --weapon EDITORID --capacity N --out DIR
```

Look at each picture, at the hip and in the sights. When the glass is on a part that moves
(the top cover of Hammerhead), take pictures in the reload also.

Gate: in the sights the center of the reticle is less than 1 pixel from (640, 360) of a
picture of 1280 x 720. The glass has no haze and the reticle has no large glow. In the
reload no part of the glass stays at its old place.

## Stop and ask the user

* Before the game starts.
* When a word of the user is not clear. For "its stretched" the agent found no geometric
  stretch, said so, corrected the size, and asked: "If you see a different stretch, tell me where."

## Common faults

| Sign | Cause | Rule |
| --- | --- | --- |
| The reticle is too large | The quad had its mesh size. The vertex shader puts it some meters before the camera. | `distance` and `eye` of `[model.sight.reticle]`. `scale` changes the result. |
| A haze on all of the glass | A color above 1 in an effect material makes a glow in Fallout 4 | A smaller `glass_scale` (0.5 for The Huckleberry, whose border had the value 3.0) |
| A red haze from the reticle | A reticle with a high scale on a large quad | A small reticle |
| The glass stays in its place when its cover opens | The sight part is on the wrong node | `P-Scope` on the bone of the glass (`WeaponOptics1`). For a sight that is rigid on the gun: the node `NAME` + `Receiver`. |
| `esx render` shows no glass | It draws no effect material (the note `SCENE_NOT_DRAWN`) | Only a game test shows a glass |

## What to report

The move of each clip in the sights, the rule of each material with its shader file, the
state of the glass as a choice, the pixel of the reticle in the game picture ("less than 1
pixel", not "0.4 pixels"), the clips that changed, and the limits: the reticle shows at each
time and is fixed to the glass, no reference picture of Destiny is here, and the sight part
was not tested at the weapons workbench.

## More

* [references/sight-facts.md](references/sight-facts.md): the numbers of each gun, the shader
  rules, the blend of Fallout 4, what is not done.
* [destiny/port/README.md](../../../destiny/port/README.md), "The glass of the sight and the reticle".
* [docs/porting/troubleshooting.md](../../../docs/porting/troubleshooting.md),
  [docs/porting/game-test.md](../../../docs/porting/game-test.md).
