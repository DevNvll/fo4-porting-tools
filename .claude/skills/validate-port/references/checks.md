# The checks: what each one proves, and what passed it

From the notes of the three chats and from
[destiny/port/README.md](../../../../destiny/port/README.md), "Checks". The column "Faults
that passed it" is the reason for each gate of the skill.

## The checks of the converter d2fo4

| Check | It proves | It does not prove | Faults that it found | Faults that passed it |
| --- | --- | --- | --- | --- |
| The lines of `./port destiny convert`: `[parts]`, `[retarget]` (`wrist`, `weapon`), `[hkx]` (`pos err`) | Each shape is on a bone. The wrists and the gun of the result are at the source. The HKX file has the poses. | That the source pose is correct. | | The gun at the origin of the world (The Huckleberry): the numbers compare with the same wrong source. |
| `./port destiny check gun` | Each gun vertex of the HKX clip is at its source place. | A rule that changes the source: `[gun]`, `[compose]`, `[hand_pose]`. | The error of 0.15 units with 40-bit rotations. | The reload of The Huckleberry as a pair of two clips. |
| `./port destiny check fingers` | Each joint between two finger bones is a hinge. No joint bends back. The largest turn in one frame against the source. | That a finger is at the correct place on the gun. | A turn of 20 to 38 degrees to the side. A turn of 170 degrees at frame 83 of the reload of the M77. | |
| `./port destiny check contact`, `contact-table` | The percent of hand vertices inside the gun, and the depth of each bone, for the source and for the result. | A hand that is away from the gun: a hand that is 1 cm away has no vertex inside. | The right middle finger 0.93 units deep in the hold pose. The right thumb of Hammerhead 3.0 units deep (source 1.3). | The left hand of The Chaperone 1 cm from the gun. |
| `./port destiny check touch`, `touch-table` | The distance of the nearest vertex of each hand to the gun, and the percent of vertices nearer than 0.5 cm and 1.5 cm, for the source hand and for the Fallout 4 hand. | That the pose is the pose of the source game. A pose clip is a choice. | It showed that the three earlier guns did not have the fault of The Chaperone. | |
| `./port destiny check render` with `sheet`, `look-sheet`, `frame-sheet`, `video`, `strip` | What a person sees: the source beside the result with one camera. | A number. A fault that the source has also. | The shoulders in the melee clip. The hands with no gun in the source of The Huckleberry. | The left hand of The Chaperone: the pictures were equal to the source. |
| `./port destiny check third-sheet` | The source above the result as lines, for a third-person clip. | The hand IK of the game. The fingers. | The arms that were too short in the reload of Hammerhead. | The left hand that the game pulled to the grip, and the open fingers. The game pictures showed the two. |
| `./port destiny regress`, and a second complete run | The same input gives the same bytes. A tool change did not change an earlier weapon. | That a clip is correct. | A change of 3e-5 in two source files made the releases different from the recorded ones. | |
| `./port mod build`, and `plugin check-weapons`, `scene weapon`, `render weapon` of esx | The records, the slots, the meshes, the materials and the textures resolve. | The look in the light of the game. A glass. A clip. | The flag `Bolt Action`, the missing nodes `WeaponOptics1` and `WeaponOptics2`, the power armor rules, the missing clip for power armor. | The light gray guns and the reticle that was too large. The game showed these. |
| The game tests (`./port destiny game ...`) with the trace | The game loads the weapon, starts its graphs and its clips, fires, and fills the gun. The trace gives each clip and each event with its time. | The look of the hands. The walk, run and jump clips. The sound. Power armor. The workbench. | The put-away, the sight below the center, the left hand at the grip, the reload that ended early, the haze. | The hands that did not touch the gun. A reload that ended 12 frames early passed with 0 failed ops until the agent read the trace. |

## The checks of the fnv tool

| Check | Shows | Does not show |
| --- | --- | --- |
| The wrist error and the arm length error of the retarget step | The arm solve | The fingers |
| The HKX step that reads each file again | The file has the poses | That the poses are good |
| A count of skin vertices inside the gun | Skin inside the gun | A finger that is open, straight, or at a wrong place outside the gun |
| A picture sheet at a normal zoom | Large pose faults | A thumb that is 0.7 units off, lumps on a finger |
| `./port fnv regress` | A change of the result | Whether the result is good |
| A close view at a zoom of 300 percent, the source above the result | The faults that the user found | It needs a reader who looks |
| The joint bends against the range of the vanilla clips | Back bends, straight fingers | The place on the gun |
| A game test with `esx probe` | The weapon equips, the graph is active, each clip starts, the events come, the ammunition count changes | The look of the hands, held input, sound |

The game test of the first MP7 build passed 30 of 30 with the fingers in the gun. A broken
collision step made the contact count better (631 against 1184 vertices) while the fingers
pointed away from the grip.

## The numbers of a correct port

| Value | The ported weapons |
| --- | --- |
| A gun vertex against the source | at most 0.009 units (The Last Word), 0.012 (the Khvostov, The Chaperone, The Huckleberry), 0.015 (Hammerhead), 0.0102 (the M77) |
| A wrist against the source wrist | at most 0.003 units |
| `pos err` of an HKX clip that is read again | below 0.02 units |
| Hand vertices inside the gun, result against source | The Last Word 2.2 to 5.7 percent against 3.3 to 10.5. The Khvostov 8.0 to 9.4 against 8.1 to 9.8. Hammerhead 9.0 to 11.5 against 7.7 to 9.5. The M77 6.1 to 10.6 against 8.3 to 24.1. |
| Vertices of the left Fallout 4 hand nearer than 0.5 cm to the gun in the hold pose | The Last Word 10.6 percent, the Khvostov 5.6, Hammerhead 5.1, The Chaperone 5.2, The Huckleberry 20.9 |
| A Fallout 4 hand that holds a gun, nearer than 0.5 cm | 5 to 42 percent |
| The reticle in the sights, in a picture of 1280 x 720 | less than 1 pixel from (640, 360) |
| The built mesh against the parts file | at most 0.008 units |
| A finger joint that bends back | none. The first joint of a thumb of the M77 bends back 3.3 to 4.9 degrees in the reload. |

Zero hand vertices inside the gun is not the target: the source hands are partly in the gun.

## The views of `./port destiny check render`

| View | Shows |
| --- | --- |
| `fp` | The first-person camera. The default. |
| `r_thumb`, `r_back`, `r_front`, `r_under`, `r_palm` | The right hand from five sides |
| `l_thumb`, `l_back`, `l_front`, `l_under`, `l_palm` | The left hand from five sides |
| `gun_left`, `gun_right`, `gun_top`, `gun_back`, `gun_under` | The gun with the hands |

* `--kinds src,fo4` is the default: the source and the result. The pictures have the names
  `CLIP_fFFF_VIEW_src.png` and `CLIP_fFFF_VIEW_fo4.png`.
* `--template` has the default `revolver44`. Give the template of the weapon.
* `./port destiny check fingers` has the default `--vanilla data/destiny/port/rig/revolver44`.
  Give the folder of the template of the weapon.
* The source in a picture is the file as Blender reads it. For a set file with `[gun]` or
  `[compose]` the source has the pose of the bake with those rules.
* The check pictures do not draw the part of the sleeve at the shoulder.
* The camera bone of the source is on the camera bone of Fallout 4. So a check picture from
  `fp` and a game picture show the same view, and you can compare the two.
* `./port destiny check sheet`, `video` and `strip` are shell programs with no help text. Do
  not run them with `--help`. `./port list` has the arguments of each one.

## What a recording shows that is not a fault of a clip

* The camera kicks at each shot. It is the recoil of the weapon record. The vanilla weapon
  does the same in the same session.
* A moving object leaves a row of copies behind it. Vanilla objects show it also.
* The Pip-Boy is in the view, because the clips of Destiny bring the left forearm far into
  the view.
* The top of the picture has a black and yellow area before the weapon is in the hand. It is
  the sky of the test cell `QASmoke`.
* The graph starts the blend from the draw clip to the idle 0.5 s before the end of the draw
  clip, so the last part of the draw plays at a decreasing weight.
* The game goes into the sights about 2.1 s after the action `ActionSighted`, for each weapon.
  The cause is not known.
