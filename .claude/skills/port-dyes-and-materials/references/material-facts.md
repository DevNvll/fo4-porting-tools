# Facts about the dyes and the materials

From [destiny/port/README.md](../../../../destiny/port/README.md), "The dyes and the shaders
of Destiny", and from the notes of the first work. The reading of the dye data is the reading
of the first work: the public tool Charm has the order of another game build with 21 vectors.

## The data of Destiny 2

* A texture set of a gun is three files: albedo, normal and gstack.
* The gstack texture: red is the occlusion, green is the smoothness, blue is the alpha test
  and the emission, and alpha has two uses. An alpha of 40 to 255 is a pixel with a dye, and
  the value is the wear mask. An alpha of 0 to 32 is a pixel with the color of the albedo,
  and the value is the metal value.
* A gun has three dyes (the channels Weapon1, Weapon2, Weapon3). Each dye has a primary and a
  secondary material: a tint, a metal value, a smoothness range, the same three for the worn
  surface, and two detail textures.
* Each mesh part has one of six slots: the primary or the secondary material of one of the
  three dyes. The model tool prints the percent of pixels of each slot.
* A dye tag has 27 vectors. The tools use the vectors 0 to 2 (the transforms of the detail
  textures), 9 to 12 (the primary material), 13 to 16 (the secondary), 17 to 20 (the worn
  primary) and 21 to 24 (the worn secondary). The vectors 3 to 8, 25 and 26 are not used.

| Gun | Pixels with a dye | Default dyes |
| --- | --- | --- |
| The Last Word | 0 percent | The colors are in the albedo texture. Its dyes are locked. |
| Khvostov 7G-02 | Less than 0.1 percent | The colors are in the albedo texture. |
| Hammerhead | 93 percent of the body and of the belt, 50 percent of the sight | Black paint and steel; dark gray; red metal and silver metal |
| The Huckleberry | 0 percent | |

## The gear shader

The formula is that of the public shader `DeltaDesigns/sbox_destiny_2_gear_shader` (a copy of
the shader of the game for a different engine). `a` is the alpha of the gstack texture.

* remap(v, r) = clamp(v x r.y + r.x, r.z, r.z + r.w)
* Metal with no dye = saturate(a x 7.96875)
* Wear mask = saturate(a x 1.186 - 0.186)
* Color = lerp(worn tint, tint, remap(wear mask, wear remap))
* Base = color x saturate(albedo x 4) + saturate(albedo - 0.25)
* Smoothness = the remap of gstack green x 0.86
* Detail texture coordinates = (uv x 5) x transform.xy + transform.zw

## The conversion to a Fallout 4 material

Fallout 4 has a diffuse texture, one specular value and a gloss value for each pixel, and no
metal value.

* Diffuse = sRGB(base x ((1 - occlusion) + occlusion x ao))
* F0 = lerp(0.04, base, metal)
* Specular = 0.9 x sqrt(luminance(F0)) x (0.5 + 0.5 x smoothness) x (0.6 + 0.4 x ao)
* Gloss = smoothness
* The `_d` texture is the base color, `_n` is the normal map, and `_s` has the specular
  value in red and the smoothness in green.
* `specular` (default 0.9) and `occlusion` (default 0.5) of `[model]` are the two weights.

The first version gave each metal pixel a specular value of 0.7 to 0.9. A dark metal was
light gray in the game: the reflection of the environment was too bright. The median
specular value of the body texture is now 0.12 for Hammerhead and 0.13 for the Khvostov.

## The shaders in a mod

* `mods/Hammerhead` has the default look and three shaders of Destiny: Golden Trace, Calus's
  Selected and Monochromatic. Each one is a receiver part
  (`from = "mod_CombatRifle_Receiver_Automatic1"`) with its own model file.
* Two part tables with one attach point are alternative parts. The player changes the part
  at the weapons workbench.
* The reading of the dye values fits known shaders of the game: Golden Trace has a gold
  metal (tint 0.97, 0.58, 0.10, metal 1) on black, and Monochromatic has only grays.
* For The Last Word and the Khvostov the plugin and the main archive of the release had the
  same bytes before and after the work on the materials. Only the texture archive changed.

## What is not correct or not done

* The meaning of each of the 27 vectors is a reading of the values. 8 vectors have no
  meaning in the tools.
* The detail textures have the place of the public shader (5 times the texture coordinates).
  The game has a second set of texture coordinates for them, which the extraction does not
  have.
* Not done: emission, iridescence, fuzz and transmission. The three shaders of
  `mods/Hammerhead` have an iridescence value (33, 35 or 25) on a part of their materials.
* A smoothness range with a negative size gives a smoothness of 0, as in the public shader.
  It is not known if the game does the same.
* Fallout 4 has a white specular color, so the reflection of a colored metal has no color.
* No reference picture of Destiny is here.
* The shader parts were tested with the probe, not at the weapons workbench.

## The materials of Marathon

| Rule | Content |
| --- | --- |
| `palette` | One texture: an atlas of flat colors. The texture coordinates of a part point at a color. No normal map, no metal. |
| `detail` | 6 textures. Color = texture 0 x the color of a region x a detail value. The file has the color of the region 0 only (0.216). The game calculates the six others when it runs. |
| `constant` | No texture: one color of the constants. |

A shader of Marathon is DXIL, not the bytecode of Direct3D 11. The command
`./port marathon notes dxil MATERIAL` prints it as LLVM text (it needs the program
`llvm-dis`). The render targets are those of Destiny 2: 0 the color, 1 the normal (its
length has the smoothness), 2 the metal value and the occlusion.
