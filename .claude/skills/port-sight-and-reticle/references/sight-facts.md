# Facts about the sights of the ported weapons

Each number is from the set files of this repository and from
[destiny/port/README.md](../../../../destiny/port/README.md), "The glass of the sight and the
reticle". Use the numbers as the expected range for a new weapon.

## The move of the clips in the sights

The clip in the sights of Destiny is the clip of each gun of the class. In the clip the eye
is at one place for the class, and the sight of each gun is at another height.

| Gun | Eye in the clip (z, weapon space) | Aim point (z) | Move of each clip in the sights |
| --- | --- | --- | --- |
| Khvostov 7G-02 | 11.55 | 8.86, the center of the reticle | 2.69 units up |
| Hammerhead | 11.55 | 14.95, the center of the reticle | 3.40 units down |
| The Chaperone | 9.61 | 8.85, the center of the two rings | 0.76 units up |
| The Huckleberry | 10.34 | 9.59, between the two marks | 0.75 units up |
| M77 (Marathon) | 11.18 | 7.62, the top of the front post | 3.56 units up |

Before the work on the reticle, the aim point of the Khvostov and of Hammerhead was the center
of the window of the housing (2.80 units up, 3.55 units down). When the aim point changed,
the 5 clips in the sights of each gun changed, and the 22 other clips kept their bytes.

## The render stages of Destiny 2

| Stage | Content | In the extraction |
| --- | --- | --- |
| 0, `opaque` | The gun | yes |
| 7, `transparent` | The glass with its graphics. Each part is on a weapon bone. | no: `./port destiny reticle` |
| 16, `reticle` | One quad at the origin, with the texture of the reticle. Its vertex shader puts it on the aim axis. | no: `./port destiny reticle` |

## The rules of the materials

* The reticle (each gun has this pixel shader, with other values): color = red x `cb0[1]` +
  green x `cb0[2]`, and picture = blue x color + scene x (1 - `cb0[0].x` x blue). In Destiny
  it shows only when one input is 0.99 or more (the gun is in the sights).
* The glass of Hammerhead: color = red x RED + green x GREEN + blue x BLUE of the albedo
  plate, and alpha = the green value of the gstack plate. An expression program calculates
  RED, GREEN and BLUE from six inputs that the files do not name.
* The glass of the Khvostov: color = red x RED + a mirror picture of the scene, and picture =
  color x a + scene x (1 - 0.5 x a), with a = the green value of the gstack plate. RED is
  0.8194 red with no alarm and 3.0 red with the alarm. The mirror picture is not done.
* The glass of The Chaperone: color = red x RED, and picture = color x a + scene x (1 - 0.75
  x a).

## The size of the reticle

The vertex shader puts the quad `cb0[11].x` meters before the camera. The quad of the file
is 1.74 x 1.77 cm. The size on the glass = the size of the quad x (the distance of the glass
from the eye point / the distance of the shader).

| Gun | Distance of the shader | Angle | Size on the glass | In a picture of 1280 x 720 |
| --- | --- | --- | --- | --- |
| Hammerhead | 2.25 m | 0.44 degrees | 0.24 units, at 31.2 units from the eye | The dot is 4 pixels wide |
| Khvostov 7G-02 | 1.1 m | 0.91 degrees | 0.41 units, at 25.9 units from the eye | The reticle is 11 pixels wide |
| The Chaperone | 3.35 m | 0.30 degrees | | |
| The Huckleberry | 2.65 m | | | |

The first version gave the quad its size as a part of the gun: 1.22 units for Hammerhead,
half the width of the glass, 5 times too large. The user wrote: "its stretched. the center
reticle is too big".

The center of the reticle in the game pictures in the sights: (639.6, 359.4) for Hammerhead,
(639.1, 359.6) for the Khvostov, (639, 359) for The Chaperone and The Huckleberry. The center
of the picture is (640, 360).

## What Fallout 4 does with the two shapes

* esx makes no new effect shader, and it keeps the effect shader of a template. The template
  is the vanilla mesh `Meshes/Weapons/CombatShotgun/CombatShotgunReflexSightDot.nif`, with
  the shapes `TubeGlass:0` (it becomes the glass) and `TubeGlass001:0` (the reticle).
* Fallout 4 blends an effect material as texture x scale x a + scene x (1 - a). So the reticle
  texture of Hammerhead has color / 2.5 and a = 0.5 x blue, and its material has the scale 5.
* A color above 1 makes a glow. A small dot can have it. A border with the value 3.0 around
  a glass made a haze on all of the glass.
* A template shape keeps 16-bit vertex values, with a step of 1/64 unit at 20 units from the
  place of the shape. The model tool puts the place of each shape at the center of its new
  geometry.
* The sight part is a copy of `mod_CombatRifle_Scope_SightsIron` in the slot `ap_gun_Scope`.
  The gun has `P-Scope` and the sight has `C-Scope`.
* `glass_scale`: 2.0 for Hammerhead, the Khvostov and The Chaperone, from a game test. 0.5
  for The Huckleberry.

## What is not done, and the limits

* The colors of a glass are those of one state. The choice of the state is not from a file.
* Not done: the moving grid in the glow of the glass, the change of the brightness with the
  time, the red marks on objects behind the glass, the dust layer, the mirror picture.
* In Fallout 4 the reticle shows at each time and is fixed to the glass. In Destiny it shows
  only in the sights, and it is on the aim axis.
* The angle is correct for Fallout 4 only if Destiny draws the gun and the reticle with the
  same projection. No reference picture of Destiny is here.
* Hammerhead and The Chaperone have more transparent parts that are not in the model.
* The sight parts were tested with the probe, not at the weapons workbench of the game.

## The sight of a Marathon weapon

The sight unit of the M77 has two named points, 27.2 cm apart at one height. The first work
read them as the aim point and the eye point. The game test agrees: the top of the front
post is at the center of the picture. The meaning of the two points is a reading, not a fact
of a file. `manifest.json` of the extraction has the points of each piece.
