# Each known sign, its cause and its rule

From the ports of five Destiny 2 weapons, of the M77 of Marathon and of three New Vegas
weapons. A rule with "(in the tool)" needs no key now. The sign still tells you where to look
when it comes back. The last column names the skill with the procedure. This file is a short
copy of [docs/porting/troubleshooting.md](../../../../docs/porting/troubleshooting.md): that
document is the source, and it has more rows. Change the two together.

## The source data and the extraction

| Sign | Cause | Rule | Skill |
| --- | --- | --- | --- |
| A preview picture shows the gun far from the hand, "disassembled floating" | A bone with no keys keeps the pose of the clip that was shown before | Each clip has keys for each bone (in the tool). `./port destiny check-glb` reports "bones without keys". Reset the pose before each clip. | `extract-game-weapon` |
| The user sees the old defect after the correction | The chat shows the old picture of a file that was made again | A new file name for each picture or video that is made again | `document-port` |
| The hands hold no gun; the gun bone is at the origin of the world | The clip is a clip of another rig | `[gun] rest = true`. Measure each clip: `./port destiny check gun-on-grip`. | `write-set-file` |
| A weapon bone has a hash, not a name | The name is not in the word list | `[roles]` (a kind of the template) or `[bones]` (a Fallout 4 bone) | `write-set-file` |
| `./port destiny states` gives no state for the weapon | The weapon tag is the tag of the class, not the content group | The tag comes from the row of the pattern entity (in the tool) | `extract-game-weapon` |
| `./port destiny find` has no row | The weapon is not in this game build (Hawkmoon) | No rule. Tell the user. | `extract-game-weapon` |
| `./port marathon extract` stops: "has no row in the art table" | The item is a variant | `--art "BASE ITEM"` | `port-marathon-weapon` |
| The extraction of a Marathon weapon prints "the rest places of the gun parts differ by 1.000000" | The arm rig does not have the bones of this weapon | No rule. Its first-person file is not correct. | `port-marathon-weapon` |
| m2x stops: "no tag of the class ...: the layouts of this file are for another build" | A new build of the game | `./port marathon tag64`, then find the new layout | `decode-game-data` |

## The first-person clips

| Sign | Cause | Rule | Skill |
| --- | --- | --- | --- |
| A part does not move in the clip of the hands | Its motion is in a second clip | `[gun.parts]` | `port-staged-reload` |
| The reload is three states, and one plays one time for each round | A shotgun | `[compose]`, `[piece_events]`, one line `when ammo == N play CLIP` for each count | `port-staged-reload` |
| A part moves across the view where two clips of `[compose]` join | The game puts a hidden part behind the camera or 1.4 m away | `cut` | `port-staged-reload` |
| A state has no clip for this weapon | The graph has no entry for the tags of the weapon | `[synth]` | `write-set-file` |
| The sprint loop is one pose | The file has no motion in that clip | `[synth]` with `pose = "sprint"` | `write-set-file` |
| In the sights the eye is not on the sight | The source game aligns the sight when it runs | `[sight]`: `point` and `clips` | `port-sight-and-reticle` |
| The gun is out of the hand before the hand moves in the put-away | The graph removes the gun 0.233 s before the end of the clip | `[hold_end] WPNUnEquip = 8` (3 for a clip of 12 frames) | `write-set-file` |
| A part is at a wrong place in a vanilla clip (a belt that is a straight line) | The bind pose of the file is not the hold pose | `part_rest = "hold"` | `write-set-file` |
| In the sights, or now and then in the idle, the hands have the pose of the vanilla gun | The mod has no clip with that name, so the graph takes the vanilla clip | A clip for each name: `WPNIdleReadyA` to `D`, `WPNIdleSightedWobble`, `WPNEquipFast`, `WPNFireSingleReadyA` and `B` | `write-set-file` |
| In a clip with vanilla motion the shoulders go through the view | A large turn of the gun, with the arms as one body with the gun | No `[synth]` for the melee clip | `write-set-file` |
| `reloadComplete` comes when the picture does not show a loaded gun | The event rule looks at the magazine only | `[events]` | `write-set-file` |
| A reload sound is at a wrong frame | The part moves again after it is in | `[events]` | `write-set-file` |
| The weapon is automatic and the source has one clip for one shot | The source game plays the clip again for each shot | `[auto]` | `write-set-file` |
| A shot has no motion of a part | The file has none there | No rule. Write it as a limit. | `write-set-file` |
| In the idle the muzzle moves 0.03 to 0.09 units from frame to frame | 40-bit rotations | 48-bit rotations in the writer of `destiny/port` (in the tool) | `change-shared-tool` |

## The hands and the fingers

| Sign | Cause | Rule | Skill |
| --- | --- | --- | --- |
| The left hand does not touch the gun, in the source also | The clip of the hands is a clip of the weapon class | A pose clip of the gun, and `[hand_pose]` | `fix-hand-pose` |
| The left hand touches the gun (12.4 percent), but it is not at its place | The same cause: the wrist was 2.5 cm from the place that it has in a clip of this gun | Measure each pose clip candidate of the gun. Then `[hand_pose]`. | `fix-hand-pose` |
| A finger points to the wrist in one frame, or the fingertips are 1 unit from the source | A rig of Marathon: the hand bone is at another place, and a closed finger | `knuckles = "align"`, `closed_fingers = true` | `fix-hand-pose` |
| The joint after the knuckle turns 20 to 38 degrees to the side | The Fallout 4 palm is 0.8 units wider, and the collision step moves a joint in any direction | One plane for each finger (in the tool) | `fix-hand-pose` |
| A finger is deeper in the grip than the source finger | The plane through the fingertip cancelled the push of the collision step | The plane is fitted to the joints after the collision step (in the tool) | `fix-hand-pose` |
| New Vegas: the fingers are in the gun | The finger rotations were copied, and the Fallout 4 finger bones are shorter | The path solver and the collision step (in the tool) | `fix-hand-pose` |
| New Vegas: the fingers are open and point away from the grip | A step that turned a bone out of the gun | That step is removed (in the tool) | `fix-hand-pose` |
| New Vegas: a part comes through the palm | The wrist was moved to align the knuckles | No wrist shift (in the tool) | `fix-hand-pose` |
| New Vegas: a straight finger with lumps, or a joint that bends back | The Fallout 4 hand mesh is modelled with bent fingers | `[fingers] min_bend = 0.3` | `fix-hand-pose` |
| New Vegas: a thumb 0.7 units from its place | The skin of the thumb is not a tube about its bones | `[fingers] skin_center = true` | `fix-hand-pose` |

## The model, the materials and the sight

| Sign | Cause | Rule | Skill |
| --- | --- | --- | --- |
| A dark metal is light gray in the game | A high specular value for each metal pixel | The specular value from the reflectance (in the tool) | `port-dyes-and-materials` |
| The light parts of a gun are too bright, with a glow, in direct daylight | Not known. Seen for The Chaperone and The Huckleberry in the test world. In the dark cell `QASmoke` the same materials looked correct. | No rule yet. The materials are not corrected for it: a limit. | `port-dyes-and-materials` |
| Flat gray surfaces where Destiny has paint | The colors are in the dyes | `dyes = "dyes.json"` in `[model]` | `port-dyes-and-materials` |
| A shader item does not change the gun | The gun has no pixel with a dye, or its dyes are locked | No rule. Say so. | `port-dyes-and-materials` |
| A piece of a Marathon weapon is gray | The game calculates the colors of the regions when it runs | No rule. A limit. | `port-dyes-and-materials` |
| The sight has no glass and no reticle | The extraction has only the stage `opaque` | `./port destiny reticle`, `[model.sight]` | `port-sight-and-reticle` |
| The reticle is too large | The quad had its mesh size | `distance` and `eye` of `[model.sight.reticle]` | `port-sight-and-reticle` |
| A haze on the glass, or a glow around the reticle | A color above 1 in an effect material | A smaller `glass_scale`; a small reticle | `port-sight-and-reticle` |
| The glass stays in its place when its cover opens | The sight part is on the wrong node | `P-Scope` on the bone of the glass | `port-sight-and-reticle` |
| `esx render` shows no glass | It draws no effect material | Only a game test shows a glass | `port-sight-and-reticle` |

## The third-person clips

| Sign | Cause | Rule | Skill |
| --- | --- | --- | --- |
| The left hand goes to the grip in the reload | `WeaponIKTargetL` was at its rest place | The bone has the matrix of the left hand (in the tool) | `port-third-person-clips` |
| The left hand is at the place for the vanilla gun in each clip of the grip | `WPNAssemblyPose` is the vanilla one, or a wrong one | `[third.poses] WPNAssemblyPose = "WPNReload:0"` | `port-third-person-clips` |
| The left arm is too short | The source game holds the gun at another place than the vanilla stance | `gun = "source"` | `port-third-person-clips` |
| The right fingers are open on the grip | The third-person data of Destiny | `right_hand = "hold"`, the default | `port-third-person-clips` |
| The tool says "the clip has offsets only" | An additive clip | `--additive STATE`, with `--base` | `port-staged-reload` |
| The gun parts do not move | The gun entity has no clip for the state | `[third.parts]` | `port-staged-reload` |
| The reload ends before its motion ends | The graph sends `reloadEnd` 0.5 s before the end of the clip | `[third.hold_end]` | `port-staged-reload` |
| Sounds of another reload clip play | The graph plays `WPNReload` on a second clip node | A clip with a new name for each count, and `silent = ["WPNReload"]` | `port-staged-reload` |
| The build stops: no folder of `power_armor_third_person` has the clip | The two third-person views have one graph | `[third.power_armor]` | `port-staged-reload` |

## The build, the probe and the tools

| Sign | Cause | Rule | Skill |
| --- | --- | --- | --- |
| The build stops: "no matching subgraph rules for PowerArmorRace" | `like AnimsCombatRifle` | `like AnimsCombatShotgun`, and `remove_keywords = ["AnimsCombatRifle"]` | `port-destiny-weapon` |
| A hammer clip plays after each shot | The flag `Bolt Action` of the vanilla .44 | `flags = { "Bolt Action" = false }` | `port-destiny-weapon` |
| New Vegas: the game does not play `WPNReloadEmpty` | The vanilla graph has no such state | `when empty play WPNReloadEmpty` in the behavior source | `port-fnv-animations` |
| `item.give`: "No form has this EditorID" | The session started with the project folder | The release folder | `game-test-port` |
| The video shows the camera turning about the player | The idle camera, 2 minutes after the start | A session that is 140 seconds old, then set the view | `game-test-port` |
| `ammo.set`: "The engine did not keep the requested counts" | No reserve count, or not known | `loaded` and `reserve`; the first-person tests before the sight pictures | `game-test-port` |
| The sha256 of the plugin is not the tested one | A build after the tests | Each test again on the last release | `game-test-port` |
| `./port baseline check` prints `DIFFERENT` | A command replaced a stored result: a convert run with `-o` into a baseline folder, or a build | Find the command. `./port baseline update` only for a change that the user accepted. | `change-shared-tool` |
| `./port selftest` prints `FAIL` | One of its four parts: `python`, `port.toml`, `tests`, `git` | The lines below the part name the fault | `change-shared-tool` |
| `./port destiny game session` stops with the exit code 1: "the session file has the session ... with the label ..." | A second agent can have started that session | `esx probe status`. Wait, or ask its owner. `--take-over` only after the user says so. | `game-test-port` |
| The session is gone in the middle of a test | A second agent stopped it | Run the test again | `game-test-port` |
| The user wants a faster reload | The clips have the speed of the source files. No key of a set file changes it. | A `speed` line in the `reload` block of the behavior source (from the document of esx: not tested here) | `port-destiny-weapon` |
| A byte check says "0 changed" after a real change of `fnv/` | The step `hkx` writes into the work folder, and only `install` copies | `./port fnv regress`, or run each step | `change-shared-tool` |
| Each clip of a `fnv` conversion is different, and the log has "moved 0" | The step `parts` did not run, so the collision step had no gun | Run `parts` first (the retarget now stops with no parts file) | `change-shared-tool` |
| `__pycache__` folders in the source tree | Blender does not read `PYTHONDONTWRITEBYTECODE` | `sys.dont_write_bytecode = True` in each Blender program | `change-shared-tool` |
| `./port` stops with the exit code 3 | A thing that the command needs is missing | The message names the command that makes it | `set-up-workspace` |
| The shell of the agent stops (exit 144) | `pkill -f TEXT` also stops the shell that has that text | Stop a process by its process ID | |
| A command fails in zsh: "no matches found" | A glob with no match, or a variable that zsh does not split | Quote each glob; use a small `sh` script | |
