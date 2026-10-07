# Facts about the third-person clips

From [destiny/port/README.md](../../../../destiny/port/README.md), "The third-person clips",
and from the set files of this repository.

## What Fallout 4 has

* The third-person files of one weapon are `WPNReload`, `WPNAssemblyPose`,
  `WPNFireAutoReadySlave` and `WPNFireSingleReadySlave`, in a folder such as
  `Meshes/Actors/Character/Animations/Weapon/CombatShotgun/Player`.
* The game puts the left hand on the bone `WeaponIKTargetL` with IK, in each clip. Each
  vanilla clip has this bone 0.3 units or less from the left hand.
* `WPNAssemblyPose` gives the place of the left hand on the gun for each clip of the grip.
* The clip node of a reload has three triggers relative to the end of the clip:
  `reloadEndSlave` 0.533 s, `reloadEnd` 0.5 s, and one more 0.467 s before the end. When the
  event of the clip comes first, it ends the reload. A clip that moves until its last frames
  needs 16 more frames (`[third.hold_end]`).
* The graph has a second player for the gun parts (`WeaponSlave_StateMachine`). In the
  vanilla graph its reload state and the reload state of the body have one clip node. esx
  makes a new node for a clip with a new name in the state of the body only, so the game also
  plays `WPNReload`, with its events.
* In the first-person view the events come from the first-person clip only.
* The body and the body in power armor are two views with one graph. The four views of an
  esx behavior source are `first_person`, `power_armor_first_person`, `third_person` and
  `power_armor_third_person`.
* The third-person skeleton has 95 bones: the 94 bones of the first-person skeleton and
  `CamTarget`.

## What Destiny 2 has

* The clips are in the player body entity (`80BAB778`): 72 bones, one animation set with
  1467 clips, one graph with 332 states. They are not in the extraction of the gun.
* The dimension 3 of a state is the weapon tags, as in the first-person graph. The dimension
  1 is the stance (`stand` or `crouch`). A leaf with the stance `811C9DC5` (the hash of an
  empty word) is for each stance.
* The reload is the state `EB22859A` (the hash of the word `reload_1`).
* The gun entity has its own graph with the same state names. That graph gives the clip of
  the gun parts. A pairing by the frame count gave the same clips for three guns. For The
  Chaperone it gave a clip that is in no state of the graph of the gun.
* The clips move the upper body only. The vanilla reload moves the pelvis up to 5 units.
* The third-person clips of a shotgun are additive. Their base in the tools is the first
  frame of the reload of a rifle (the clip `80BB277E`). The test of the extraction for an
  additive clip does not find each one: a clip whose first or last frame has no offset is
  additive.
* The right hand of a third-person clip moves 1 to 3 units on the grip, with open fingers.

## How the step `third` makes a clip

| Part | Rule |
| --- | --- |
| The stance | The first frame of the vanilla third-person reload of the template (`third_ready`). The pelvis and the legs keep that pose. |
| The gun, `gun = "stance"` (default) | The gun has its motion against its own first frame, on its place in the stance. |
| The gun, `gun = "source"` | The gun has its place of Destiny against the right shoulder. On the first and the last `blend` frames it goes from the stance to that place and back. |
| The left hand | Its place of Destiny against the gun. The finger rules are those of the first-person retarget. |
| The right hand, `right_hand = "hold"` (default) | While the source hand is on the grip (a move of less than 4 units against the first frame), it has its place and its fingers of the first-person hold pose. When the hand goes away, it has the motion of the source. |
| The upper body | The rotation of the stance with the turn of the source bone against its first frame. The arms are a two-bone solve from the shoulder to the wrist. |
| `WeaponIKTargetL` | The matrix of the left hand. |
| The events | Those of the first-person reload, moved by the count of frames by which the bolt (or the bones of `align`) starts to move later in this clip. |

## The keys of `[third]`

| Key | Meaning |
| --- | --- |
| `folder` | The folder with the files of `./port destiny third`, beside the file of the gun, or else a path below `data/destiny/port/`. Default `third_person`. |
| `gun`, `blend` | `"stance"` or `"source"`, and the frames of the blend. |
| `right_hand` | `"hold"` or `"source"`. |
| `align` | The weapon bones whose first motion gives the shift of the events. |
| `silent` | The clips with no sound event. |
| `[third.clips]` | Fallout 4 clip = state file, or a clip of `[third.compose]`. |
| `[third.poses]` | Fallout 4 clip = `CLIP:FRAME`, one pose of a third-person clip. |
| `[third.events]` | More events, as `[events]`. |
| `[third.compose.NAME]`, `[third.piece_events]` | As `[compose]` and `[piece_events]`, with state files. |
| `[third.parts]` | State file = the first-person clip that gives the motion of the gun parts. |
| `[third.hold_end]` | More frames of the last pose. |
| `[third.power_armor]` | Fallout 4 clip = the vanilla clip of the power armor that is copied under that name. |

## The results of the first three ports

| | Khvostov | Hammerhead | The Last Word |
| --- | --- | --- | --- |
| Frames of the reload (first person) | 105 (105) | 169 (180) | 127 (127) |
| `gun` | `stance` | `source` | `source` |
| Largest move and turn of the gun | 11.0 units, 50 degrees | 13.2 units, 33 degrees | 27.4 units, 68 degrees |
| Left hand against the gun, result against source | 0.0000 units | 0.0000 units | 0.0000 units |
| Largest change of a bone length | 0.0004 units | 0.028 units | 0.0004 units |
| Frames with the right hand on the grip | 105 of 105 | 138 of 169 | 127 of 127 |
| Rounds after the reload in the game test | 27 to 30 | 57 to 60 | 5 to 8 |

## What is not done

* Only the reload. Destiny has more third-person clips of the body for a weapon (`ready`,
  `fire_1`, the sprint). Fallout 4 has its own clips of the grip for these.
* The legs and the pelvis do not move.
* In third person the magazine of the Khvostov and the box of Hammerhead stay in the gun:
  the gun clips of Destiny do not move them.
* The hand data of a third-person clip is less exact than that of a first-person clip. The
  distance of the left hand to the charging handle of the Khvostov was not measured.
* Power armor has the vanilla reload. No game test has a body in power armor.
* The clip is for each actor with the weapon, also a non-player character. The vanilla game
  has a second reload file for them.
* The crouch variant of the Destiny reload is not used.
* No test with a motion of the player, and no test frame by frame at the normal game speed.
