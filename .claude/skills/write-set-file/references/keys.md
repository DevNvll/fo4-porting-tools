# The keys of a set file: the sign, the rule, an example

[destiny/port/README.md](../../../../destiny/port/README.md), "The keys of a set file", is the
reference of each key. This file adds the sign that asks for each key and a line from a set
file of this repository. A key that is "off by default" changes no clip of a weapon that does
not have it.

## The poses and the bones

| Key | Use it when | Example (set file) |
| --- | --- | --- |
| `template` | Always. | `template = "combatrifle"` |
| `hold` | Always. The hold pose gives the place of the gun in Fallout 4 weapon space, and it is the pose `ready` of `[synth]`. Use the first frame of the idle. | `hold = "fp_001_80BC5F49:0"` (Khvostov) |
| `sighted` | The weapon has a clip in the sights. It is the pose `sighted` of `[synth]`. | `sighted = "fp_015_80BC5F3D:0"` |
| `[poses]` | A clip of `[synth]` needs one more pose. | `sprint = "fp_008_80BC5F50:0"` |
| `[roles]` | A weapon bone has a hash for a name, or a name that the tools do not know, and the template has a bone for its kind (`bolt`, `magazine`). | `bone_68719972 = "bolt"` (the charging handle of the Khvostov), `b_pump = "bolt"` (the lever of The Chaperone) |
| `[bones]` | A weapon bone needs a Fallout 4 bone directly. The template must have that bone. | `bone_8E40D42D = "WeaponExtra1"` (The Chaperone) |
| `part_rest = "hold"` | A part is at a wrong place in a vanilla clip, because the bind pose of the file is not the hold pose (the belt of Hammerhead is a straight line there). | `part_rest = "hold"` (Hammerhead) |

The known bone names with a kind: `b_magazine` is `magazine`, `b_bolt` and
`b_charging_handle` are `bolt`, `b_safety` is `safety`. Count the vertices of a bone before
you give it a Fallout 4 bone: `b_safety` and `b_trigger` of The Last Word have none.

## The clips

| Key | Use it when | Example |
| --- | --- | --- |
| `[clips]` | Fallout 4 clip = clip of the file, or a clip of `[compose]`. Give a clip to each name of the graph. | `WPNIdleSightedWobble = "fp_015_80BC5F3D"` |
| `[synth]` | A state has no clip for this weapon, or the game has a clip that Destiny does not have (walk, run, jump). The clip has the weapon motion of the vanilla clip on a pose of the file. | `WPNRunForwardReady = "ready"`, `WPNWalkForwardSighted = "sighted"`, `WPNSprint = { pose = "sprint", reference = "wpnsprint" }` |
| `[static]` | The reader cannot read the vanilla clip (each vanilla idle has the lossless format). | `WPNIdleGunDown = { pose = "ready", vanilla = "wpnrungundown", frame = 0, frames = 30 }` |
| `[auto]` | The weapon is automatic and the file has one clip for one shot. The clip gets the length and the events of the vanilla automatic clip (67 frames, 20 shots). | `WPNFireAutoReadyForward = "fp_049_80BC1189"` (The Huckleberry) |
| `[hold_end]` | The game removes the gun 0.233 s before the end of the put-away clip, and the clip is shorter than that. | `WPNUnEquip = 8` for a clip of 4 or 5 frames. `WPNUnEquip = 3` for the clip of 12 frames of the M77. |
| `[events]` | A clip needs an event that the tools do not find, or the tools find one at a wrong frame. `{sound}` is the sound name of the template. | `WPNEquip = [[0, "SoundPlay.{sound}EquipUp"]]`, `WPNReload = [[31, "SoundPlay.WPNShotgunCombatReloadMagIn"]]` (The Huckleberry) |
| `[sight]` | In the sights the eye is not on the sight. | `point = [0.0, 8.61, 8.86]`, `clips = ["fp_015_80BC5F3D"]` |

Do not put the melee clip into `[synth]`. A clip with vanilla weapon motion moves the arms as
one body with the gun. That is correct for a small motion. For a large turn of the gun the
shoulders go through the view.

## The gun bones of a clip

| Key | Use it when | Example |
| --- | --- | --- |
| `[gun] rest = true` | The gun bone is not on the grip bone in the clips of the hands (`./port destiny check gun-on-grip`). Off by default. | The Huckleberry: 57 of its 59 full-pose clips |
| `[gun.parts]` | The parts do not move in the clip of the hands. `CLIP = "CLIP2"`: the parts of CLIP move as they do in CLIP2, against the first frame of CLIP2, on their rest place. | `fp_105_80EF5694 = "fp_103_80EF5692_add"` (The Huckleberry), `fp_088_80A5E82E = "weapon_000_80A5E484"` (the M77) |
| `[compose.NAME]`, `[piece_events]` | The reload is more than one state. | The skill `port-staged-reload` |

A check that compares with the source does not prove `[gun]`, `[gun.parts]`, `[compose]` or
`[hand_pose]`. The check compares with the pose after the rule. Only a picture of the source
game, or the game test, proves such a rule. Write it under "What is not proved".

## The hands

| Key | Use it when | Example |
| --- | --- | --- |
| `[hand_pose] folder = "posed"` | The left hand does not touch the gun in the source also. | The Chaperone, The Huckleberry (`fix-hand-pose`) |
| `knuckles = "align"` | The hand bone of the rig is at another place in the hand than that of Destiny: the knuckles of the Fallout 4 hand are far from the source knuckles (1.42 units for Marathon, 0.50 for Destiny). Off by default. | The M77 |
| `closed_fingers = true` | A finger that is a hook or a fist points to the wrist or is straight. Off by default. | The M77 |

## The model, the sight, the third-person clips

| Key | Skill |
| --- | --- |
| `[model]`: `name`, `muzzle`, `[model.materials]`, `dyes`, `[model.shaders]`, `specular`, `occlusion` | `port-dyes-and-materials` |
| `[model.materials]`: `TAG = "Name"` | TAG is the material of a shape of the file: the tag of its texture set (`plate_set` of each mesh in `manifest.json`, and the start of the file names in `textures/`). Name is the name of the Fallout 4 material and of its textures (`Barrel.bgsm`, `Barrel_d.dds`). A material with no line has its tag as its name. Example: `80EF39D0 = "Barrel"` (The Chaperone). |
| `[model.sight]`, `[[model.sight.glass]]`, `[model.sight.reticle]`, `glass_scale` | `port-sight-and-reticle` |
| `[third]` and its tables | `port-third-person-clips` |

`muzzle` is the place of the node `ProjectileNode` in Fallout 4 weapon space: the bore at the
front of the barrel. `./port destiny points WORK/parts.json` prints the front of the gun.

## The form of a comment

The comment above a rule has the measurement, and the word "choice" where it is one. From
`destiny/port/sets/the_chaperone.toml`, above `[hand_pose]`:

```toml
# The pose of the left hand on this gun (tools/d2pose.py). The idle and most other clips are
# clips of the shotgun class: in them the left hand is open below the barrel, and no vertex
# of the hand of Destiny is nearer than 0.89 cm to this gun. The file has two short pose
# clips of The Chaperone (2 frames, offsets only). 80BBD62D closes the fingers and moves the
# wrist 2.7 cm to the rear and 0.9 cm up: with it the hand is on the cover of the barrel (33
# vertices nearer than 0.5 cm). The other one, 80BBD626, has the same offsets with the
# opposite sign. The extraction does not say which state uses each one: this pose is a
# choice.
[hand_pose]
folder = "posed"
```
