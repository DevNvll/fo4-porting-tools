# Troubleshooting: sign, cause, rule

One list for the three sources. Find the sign that you see, read the cause, and apply the
rule. Each row names the weapon where the sign was found.

How to use the list:

1. Write the sign in the words of the user or of the check. If a word is not clear, say how
   you read it.
2. Find the group, then the row.
3. If the sign is not here, find the stage. Put the source and the result in one picture.
   * The source has the fault also: the data of the source lacks something. Look for a pose
     clip, a second clip, a different render stage or a different rig.
   * The source is correct and the Blender result is wrong: the retarget, or a rule of the
     set file.
   * The Blender result is correct and the game is wrong: a rule of the game. Compare with
     the vanilla weapon in the same session, read the trace, then read the graph.
4. Measure the property that is wrong. Correct the rule. Run the byte checks. Add a row here.

Words of the list:

* "(in the tool)" means that the tools do this now, with no key. The sign tells you where
  to look if it comes back.
* "Limit" means that no rule corrects the sign. Write it in the document of the mod.
* The PPK, the FAMAS and the MP7 are New Vegas weapons. The M77 is the Marathon weapon. Each
  other weapon is of Destiny 2.
* `[key]` is a key of a set file ([destiny/port/README.md](../../destiny/port/README.md#the-keys-of-a-set-file)).
  `[fingers]` is a key of a conversion file of New Vegas ([fnv/README.md](../../fnv/README.md)).

| Group | What it has |
| --- | --- |
| [The hands](#the-hands) | Fingers in the gun, broken fingers, a hand that does not touch |
| [The gun and its parts](#the-gun-and-its-parts) | A gun that is not in the hand, a part that does not move or is at a wrong place |
| [The reload, the shot and the other clips](#the-reload-the-shot-and-the-other-clips) | States with no clip, events at wrong frames |
| [The sight](#the-sight) | The eye, the glass, the reticle |
| [The materials](#the-materials) | Wrong colors |
| [Third person](#third-person) | The body with the gun |
| [The game, the graphs and esx](#the-game-the-graphs-and-esx) | The build, the probe, the recording |
| [The tools and the computer](#the-tools-and-the-computer) | The converters, the extraction, the shell |

## The hands

| Sign | Cause | Rule or correction | Found in |
| --- | --- | --- | --- |
| The left hand does not touch the gun. 0 percent of its vertices are nearer than 0.5 cm (`./port destiny check touch`), in the source also. | The clip of the hands is a clip of the weapon class. The source has the same gap, so each check against the source passes. | `./port destiny pose` with a pose clip of the gun, and `[hand_pose]`. Measure each candidate: two candidates had the same offsets with opposite signs. | The Chaperone |
| The left hand touches the gun (12.4 percent), but it is not at its place on the magazine. | The same cause. The left wrist was 2.5 cm from the place that it has in a clip of this gun. | Compare the hold pose with a clip of the gun itself, and measure each pose clip candidate (`./port destiny pose MANIFEST.json --list`, `--measure --pose TAG`). Then `[hand_pose]`. | The Huckleberry |
| The joint after the knuckle turns 20 to 38 degrees to the side. | The Fallout 4 palm is 0.8 units wider, and the collision step moves a joint in any direction. | One plane for each finger (in the tool). | The Last Word |
| In the hold pose a finger is deeper in the grip than the source finger (0.93 against 0.69 units). | The plane through the fingertip cancelled the push of the collision step. | The plane is fitted to the joints after the collision step (in the tool). | The Last Word |
| In the sights, or now and then in the idle, the hands have the pose of the vanilla gun. | The mod has no clip with that name, so the graph takes the vanilla clip. | A clip for each name of the graph: `WPNIdleReadyA` to `D`, `WPNIdleSightedWobble`, `WPNEquipFast`, `WPNFireSingleReadyA` and `B`. | The Last Word |
| In a clip with vanilla weapon motion the shoulders go through the view. | A large turn of the gun, with the arms as one body with the gun. | No `[synth]` for the melee clip. The game uses the vanilla clip. | The Last Word |
| A finger points to the wrist in one frame, or it is straight on a part that it holds. The user wrote: "finger looks dislocated on this one frame 78". | The finger is a hook or a fist. Each point of the source finger is nearer to the Fallout 4 knuckle than the length of the first finger bone. | `closed_fingers = true`. Look for the same fault in other frames of the clip (the M77 had a second place, frames 28 to 46). | M77 |
| Each fingertip is about 1 unit from the source fingertip. Each finger starts 2 cm from the finger that it follows. | A rig of Marathon: the hand bone is at a different place in the hand. The knuckles are 1.42 units from the source knuckles (Destiny: 0.50). | `knuckles = "align"` | M77 |
| The fingers are inside the grip and the magazine. The user wrote: "the fingers are clipping through". | The tool copied the finger rotations. The Fallout 4 finger bones are shorter (the index finger: 6.96 against 8.02 units), and the knuckles are about 0.5 units further out. | Each joint on the line of the source finger, then a collision step (in the tool). | MP7 |
| The fingers are open and point away from the grip. The user wrote: "why are these fingers broken". | A collision step turned a finger bone until its end was above the surface, up to 80 degrees. On a round grip that opens the hand. | That step was removed. A small step moves a finger out to a floor distance only (in the tool). The count of vertices in the gun was better with the wrong step, so the count did not show this fault. | MP7 |
| The fist looks turned away from the gun. The user wrote: "the hand is not rotating properly". | The fingers were in the grip. The wrist was correct: the game plays the clip data exactly. | The same correction as for the fingers in the grip. | MP7 |
| A gun part comes through the palm. The user wrote: "now the left hand seems clipping". | A wrist shift that aligned the knuckles moved the palm 0.6 units to the side. | No wrist shift for a New Vegas rig: the two palms agree to 0.5 units with the wrists at one place. The collision step got a floor of 0.65 of the finger radius and a largest move of 1.15 units (in the tool). | MP7 |
| A finger is fully straight, and its skin has lumps. The user wrote: "the fingers are a bit deformed". | The Fallout 4 hand mesh is modelled with bent fingers (about 45 and 30 degrees). The source finger is straight. | `[fingers] min_bend = 0.3`, the default. | FAMAS |
| The thumb is 0.7 units from its place on the grip, and its first joint bends 12 degrees back. The user wrote: "the thumb is kinda misaligned". | The skin of a finger is not at the center of its bones: the Fallout 4 thumb skin is 0.4 units to the pad side, and the New Vegas thumb skin 0.13 units to the nail side. The old least-bend rule accepted a joint that bent back. | `[fingers] skin_center = true`, the default, and the least bend about the hinge of the bone (in the tool). | PPK |
| The right thumb is deep in the gun for the whole clip, in the source also (1.6 units). | The reload of the source mod was made for a different model of the gun. | Limit. Zero vertices in the gun is not the target: the source hands are partly in the gun. | FAMAS |
| The right thumb is deeper in the gun than the source thumb (3.0 against 1.3 units). | The collision step moves a finger 1.15 units at most. | Limit. Not corrected. The hand is below the view in first person. | Hammerhead |
| A finger turns many degrees in one frame, and the source finger does also. | The hand takes or lets go a part in that frame. | Look at the frames from two sides. If no finger has a wrong shape, write it as a limit: 31 degrees (the Khvostov, frame 64), 61.8 degrees (the M77, frame 83; the source turns 92 degrees), a thumb bend of 81 degrees (the MP7). | The Khvostov, M77, MP7 |
| In one clip the shoulders move 10 units. | The vanilla weapon motion goes below the view, and the arms cannot reach that far. | The tool moves the collarbone (`max_shoulder_adjustment` in the report). The gun is out of the view at that time. | PPK |
| The base of the magazine shows between the thumb and the index finger. | The Fallout 4 thumb is thinner than the source thumb. | Limit. Only a pose change by hand hides it. | MP7 |

## The gun and its parts

| Sign | Cause | Rule or correction | Found in |
| --- | --- | --- | --- |
| The hands hold no gun. The gun bone is at the origin of the world. | The clip is a clip of a different rig. The cause in the decoder is not known. | `[gun] rest = true`. Measure the distance of the gun bone to the grip bone for each clip (`./port destiny check gun-on-grip`; [destiny.md](destiny.md), step 3): the node count alone does not find each such clip. | The Huckleberry |
| In one frame of a Blender picture the gun is 0.9 m from the hand. The user wrote: "the gun is disassembled floating". | A clip had keys only for the bones that move. Blender keeps the pose of the clip before for a bone with no key. | Each clip has keys for each bone (in the tool). `./port destiny check-glb` reports "bones without keys". Reset the pose before each clip. | The Last Word |
| A part does not move in the clip of the hands. | Its motion is in a second clip. | `[gun.parts]`, with the additive clip that has the same frame count, or with a clip of the gun entity (`weapon_NNN_TAG`; its frame count can be different by one: 104 and 105). | The Huckleberry, M77 |
| A part is at a wrong place in a vanilla clip (a belt that is a straight line). | The bind pose of the file is not the hold pose. | `part_rest = "hold"` | Hammerhead |
| A weapon bone has a hash and no name. | The name is not in the word list. | `[roles]` (a kind of the template) or `[bones]` (a Fallout 4 bone). | The Khvostov, Hammerhead |
| A part moves in a way that the name of its bone does not say. | A bone name is not a part name: `b_pump` is a lever that turns 99 degrees. | Count the vertices of the bone and look at a picture. Then give the bone its kind. | The Chaperone |
| In the put-away the gun is out of the hand before the hand moves. | The graph removes the gun 0.233 s before the end of the clip. | `[hold_end] WPNUnEquip = 8` for a clip of 4 or 5 frames. The M77 has a clip of 12 frames and adds 3. | The Last Word, M77 |
| In the idle the muzzle moves 0.03 to 0.09 units from frame to frame. | 40-bit rotations: steps of 0.04 degrees over seven bones. | 48-bit rotations, the default of `destiny/port/tools/d2hkx.py` (in the tool). The clips of `fnv/` have 40 bits. | The Last Word |
| A part moves across the view where two clips of `[compose]` join. | Destiny puts a hidden part behind the camera or 1.4 m away. | `cut = ["b_shell"]` | The Chaperone |
| A shot has no motion of a part. | The file has none there. | Limit. Sounds can come from `[events]`. | The Chaperone (at the hip), The Huckleberry |
| A hammer clip plays after each shot. esx warns `WEAPON_BOLT_ACTION`. | The vanilla .44 has the flag `Bolt Action`. | `flags = { "Bolt Action" = false }` in the item file. | The Last Word |
| `esx plugin check-weapons --reference` warns about `WeaponOptics1` and `WeaponOptics2`. | The template has no such node. | Add the two nodes to the template. | The Last Word |
| In the first picture of a weapon file the pieces are on top of the grip. | Each piece of a Marathon weapon was at its own coordinates. | The named points of the gun entity give the place of each piece (in the tool). Only a piece with a known place is in the weapon file. | M77 |
| The extraction prints "the rest places of the gun parts differ by 1.000000". | The arm entity has the gun bones of a different weapon. | Not solved. The first-person file of that weapon is not correct. | V75 SCAR (Marathon) |
| The bolt does not show in the reload. | The body of the gun is one rigid mesh in the files of Marathon. No mesh is on the bone of the bolt. | Limit. Only the events show the bolt. | M77 |
| A casing passes near the camera at each shot. | A bullpup gun with the hold pose of New Vegas ejects near the face. | Limit. | FAMAS |

## The reload, the shot and the other clips

| Sign | Cause | Rule or correction | Found in |
| --- | --- | --- | --- |
| The reload is three states, and one of them plays one time for each round. | A shotgun. | `[compose]`, `[piece_events]`, and one line `when ammo == N play CLIP` for each count in the behavior source. | The Chaperone |
| A state has no clip for this weapon (no shot clip). | The graph has no entry for the tags of the weapon. | `[synth]`: the weapon motion of the vanilla clip on the Destiny hold pose. `synth_bones` of the template moves the bolt as the vanilla clip does. | The Khvostov |
| The sprint loop is one pose. | The file has no motion in that clip. | `[synth]` with `pose = "sprint"` and the vanilla sprint as the reference. | The Khvostov, Hammerhead |
| The weapon is automatic, and the source has one clip for one shot. | The source game plays the clip again for each shot. | `[auto]`: the length and the events of the vanilla automatic clip (67 frames, 20 shots). | Hammerhead |
| `reloadComplete` comes when the picture does not show a loaded gun. | The event rule looks at the magazine only. The box is in, but the belt is not. | `[events] WPNReload = [[105, "reloadComplete"]]` | Hammerhead |
| A reload sound is at a wrong frame (frame 61). | The part moves again after it is in: the magazine turns. | `[events] WPNReload = [[31, "SoundPlay.WPNShotgunCombatReloadMagIn"]]` | The Huckleberry |
| The sound of the open bolt is at frame 0 of the reload. | The reload of an empty gun: the bolt is to the rear from the first frame. | `[events] WPNReload = [[76, "SoundPlay.WPNShotgunCombatReloadBoltOpen"]]`, the frame where the hand pulls the handle. | M77 |
| The game does not play `WPNReloadEmpty`. | The vanilla graph has no state for it. | A behavior source with the line `when empty play WPNReloadEmpty`. | PPK, MP7 |
| The game test refuses a reload. | The magazine is full. | Set a lower count first (`ammo.set`). | The New Vegas game tests |
| The reload clip is the reload of a different gun of the class. | The full first-person file has the clips of each weapon of the class. A choice from pictures and from `moving_weapon_bones` was wrong. | Read the graph: `./port destiny states`, or `states` of the manifest. | The Last Word |
| A clip of an ammunition check plays as the first idle. | The graph plays `WPNIdleReadyA` to `D` at random, one directly after the draw. | These four clips are plain idles. | MP7 |
| The user wants a faster or a slower reload. | The clips have the speed of the source files (30 frames for each second). No key of a set file changes the speed of a clip. | A line `speed 1.5` in the `reload` block of the behavior source (the document of esx, `docs/BEHAVIOR.md`). No mod of this repository has it, and it was not tested here. Do not change `reload_seconds` for this. | Not tested |
| The item file needs the time of the reload. | `reload_seconds` is the time of the event `reloadEnd`. It is not the length of the clip. | The frame of `reloadEnd` / 30. `./port fnv convert CONFIG plan` prints it for a New Vegas weapon. | Each weapon |

## The sight

| Sign | Cause | Rule or correction | Found in |
| --- | --- | --- | --- |
| In the sights the eye is not on the sight (Destiny 2, Marathon). | The source game aligns the sight when it runs. The clip in the sights is the clip of the weapon class. | `[sight]`: `point` and `clips`. The moves: 2.69 units up (the Khvostov), 3.40 down (Hammerhead), 0.76 up (The Chaperone), 0.75 up (The Huckleberry), 3.56 up (the M77). | The Khvostov |
| In the sights the eye is not on the sight (New Vegas). | New Vegas moves the camera to the node `##SightingNode` when the player aims. Fallout 4 has the sights in the clip. | The sighted pose is the aim pose, moved until that node is on the view axis (the default of the tool). | PPK, FAMAS |
| In the reload video of the source the gun is too far to the right, and the aim clip does not put the sight in the middle. | The camera was at the head bone. The camera bone of the Destiny rig is `b_utility`. | `b_utility` (in the tool). In `iron_sight_idle` the sight is on the view axis. | The Last Word |
| The sight has no glass and no reticle. | The extraction has only the render stage `opaque`. | `./port destiny reticle` and `[model.sight]`. | Hammerhead |
| The reticle is too large. The user wrote: "its stretched. the center reticle is too big". | The quad had its mesh size. The vertex shader gives the reticle the size of an angle. | `distance` and `eye` of `[model.sight.reticle]`. `scale` changes the result. | Hammerhead |
| A haze on the sight glass, or a glow around the reticle. | A color above 1 in an effect material. Two cases: a red haze from a reticle with the scale 5 on a large quad, and a green haze from a border with the value 3.0. | A small reticle. A smaller `glass_scale` (`glass_scale = 0.5` for The Huckleberry). | Hammerhead, The Huckleberry |
| The glass stays in its place when its cover opens. | The sight part is on the wrong node. | The connect point `P-Scope` on the bone of the glass (`WeaponOptics1`). For a sight that is rigid on the gun: the node `NAME` + `Receiver`. | Hammerhead, the Khvostov |
| A small shape of the sight is at a coarse place. | A template shape keeps 16-bit vertex values: steps of 1/64 unit at 20 units from the place of the shape. | The place of the shape is the center of its geometry (in the tool). | Hammerhead |
| `esx render` shows no glass. | It draws no effect material (the note `SCENE_NOT_DRAWN`). | Only a game test shows a glass. | Hammerhead |
| `./port destiny model` prints `THE CLIPS IN THE SIGHTS DO NOT AIM THROUGH THE RETICLE`. | `point` of `[sight]` is not the center of the reticle. | Put the point that the program prints into `point`, and run the steps `retarget hkx install` again. | Each gun with a reticle |
| The reticle shows at the hip also, and it moves with the gun. | In Fallout 4 the reticle is on the glass. In Destiny it shows only in the sights, on the aim axis. | Limit. | Each gun with a reticle |
| The ring of the reticle is white with a pink edge. | An edge value of 8 (red) makes a glow. | Limit. No reference picture of Destiny is there. | The Khvostov |

## The materials

| Sign | Cause | Rule or correction | Found in |
| --- | --- | --- | --- |
| A dark metal is light gray in the game. | A specular value of 0.7 to 0.9 for each metal pixel, with the reflection of the environment. | The specular value from the reflectance of the surface (in the tool). `specular` and `occlusion` of `[model]` change the weights. | The Last Word, the Khvostov, Hammerhead |
| The light parts of a gun are too bright, with a glow, in direct daylight. | Not known. The run in the test world (the cell `WeapTest`, direct daylight) showed it. In the dark test cell `QASmoke` the same materials looked correct. | No rule yet. The materials are not corrected for it: write it as a limit. `specular` and `occlusion` of `[model]` are the two weights of the conversion, but no value was tested for this sign. | The Chaperone, The Huckleberry |
| The gun has flat gray surfaces where the source game has paint. | The colors are in the dyes, not in the textures. | `./port destiny dyes`, then `dyes = "dyes.json"` in `[model]`. | Hammerhead |
| A shader item does not change the gun. | The gun has no pixel with a dye (The Last Word 0 percent, the Khvostov less than 0.1 percent), or its dyes are locked. | No rule. Say so. | The Last Word, the Khvostov |
| Three pieces of the gun are gray. | A `detail` material of Marathon has seven regions. The game calculates the colors of six of them when it runs. | Limit. | M77 |
| The reflection of a colored metal (gold, red) has no color. | Fallout 4 has a white specular color. | Limit. The color is in the diffuse texture. | Hammerhead |
| Each material has one flat color. | The archive of the source mod has no texture file. | Stand-in colors. The textures of the base mod replace them. The tools of today do not make textures. | PPK |

## Third person

| Sign | Cause | Rule or correction | Found in |
| --- | --- | --- | --- |
| The left arm is too short (up to 8.3 units). | Destiny holds the gun at a different place than the vanilla stance. | `gun = "source"` in `[third]`. | Hammerhead, The Last Word |
| `./port destiny third` says "the clip has offsets only". | An additive clip. | `--additive STATE`, with `--base`. A clip whose first or last frame has no offset is additive. | The Chaperone |
| The gun parts do not move. | The gun entity has no clip for the state. | `[third.parts]`, with the first-person clip. This is a choice: no file says that the parts move in third person. | The Huckleberry |
| The reload ends before its motion ends (at frame 22 of 38). | The graph sends `reloadEnd` 0.5 s before the end of the clip. | `[third.hold_end]` | The Chaperone |
| Sounds of a different reload clip play. | The graph plays `WPNReload` on a second clip node. | A clip with a new name for each count of rounds, and `silent = ["WPNReload"]`. | The Chaperone |
| The build stops: no folder of `power_armor_third_person` has the clip (`CLIP_MISSING`). | The two third-person views have one graph. | `[third.power_armor]` | The Chaperone |
| In the game the left hand goes to the grip in the reload. | The bone `WeaponIKTargetL` was at its rest place. | The bone has the matrix of the left hand (in the tool). | The Khvostov, Hammerhead, The Last Word |
| In each third-person clip of the grip the left hand is at the place for the vanilla gun, or at the grip. | `WPNAssemblyPose` is the vanilla one, or a wrong one. | `[third.poses] WPNAssemblyPose = "WPNReload:0"` | The Khvostov, Hammerhead, The Last Word |
| The right fingers are open on the grip. | The third-person data of Destiny opens them. | `right_hand = "hold"`, the default. | The Khvostov, Hammerhead, The Last Word |
| The events of the reload are early or late. | The first rule took the median of each part, which is wrong for a gun with a belt. | `align`: the bolt of the template, or the bones that you name. | Hammerhead |
| The reload is the reload of a different weapon class. | The first tag list of the tool. | The tag list of the first-person clips, in the order of the tag tree (in the tool). Compare the frame count with the first-person reload. | The Last Word, The Chaperone, The Huckleberry |
| The clip of the gun parts is of a different state. | The pairing by the frame count. | The graph of the gun entity gives the clip (in the tool). | The Chaperone |
| The magazine stays in the gun. The hand goes to the hip and comes back with nothing. | The gun clips of Destiny do not move the magazine in third person. | Limit. | The Khvostov, Hammerhead |
| The left hand has the place for the vanilla gun, or it floats in front of a shorter gun. | Each third-person clip is a vanilla clip of the template. | Limit for a port with no third-person clip. | M77, MP7, PPK |

## The game, the graphs and esx

| Sign | Cause | Rule or correction | Found in |
| --- | --- | --- | --- |
| The build stops: "no matching subgraph rules for PowerArmorRace". | `like AnimsCombatRifle` has no rules for power armor. | `like AnimsCombatShotgun` in the behavior source, and `remove_keywords = ["AnimsCombatRifle"]` in the item file. | The Khvostov |
| `item.give`: "No form has this EditorID". | The session started with the project folder. | `esx probe start --mod PROJECT/build/release`. `./port destiny game session` does this. | The Destiny game tests |
| `esx probe start` ends with the exit code 3 and `NOT_FOUND`: "Select an installed Proton version with --proton DIR". | No `--proton` option. | `--proton "/path/to/Proton"`, or the setting `proton` for `./port destiny game session`. | Hammerhead |
| "A Fallout 4 game runs already" after a stop. A test run that starts directly after a test ends at once. | The game of the test before is not gone. | Read `esx probe status` until `fallout4_pids` is empty. | The Destiny game tests, PPK |
| The video shows the camera turning about the player. | The idle camera of the game, about 2 minutes after the start of the session. | Record in a session that is older than 140 seconds, or end before 2 minutes. An op that sets the view ends that camera. | The Khvostov, The Huckleberry |
| `anim.wait` with `clip_end` ends with a timeout. | Not known. The reload worked. | `anim.wait {"event": "reloadEnd"}` | The Last Word |
| `action.run`: "Unknown action name". | The probe has a fixed list of actions. `ActionSightedRelease` is not one of them. | `anim.send_event` with `rifleSightedEnd`, `SprintStart`, `SprintStop` or `GunUp`. | The Last Word, MP7 |
| `anim.trace` fails. | The limit must be 1 to 4096. | `limit: 4096` | The Last Word |
| `ammo.set`: "The engine did not keep the requested counts". | First case: no reserve count. Second case: not known. | Give `loaded` and `reserve`. Run the first-person tests before the sight pictures, or in a new session. | The Last Word, the Tex Mechanica mod |
| `item.give "44"` finds no form. | A vanilla form needs the plugin and the ID. | `"Fallout4.esm:0CE97D"` | The Last Word |
| Each shader part shows the default colors. | A second `item.give` in one session keeps the first gun. | One new session for each shader. Do not use `player.removeitem`: it stopped the game. | Hammerhead |
| "Another client holds the connection to the probe". | The probe has one connection. | Send the op again when the error is `retryable`, up to 8 times. | The Destiny game tests |
| The hash of the plugin is not the tested hash. | One build gave other bytes: the first build after a change of a behavior source. For the MP7 the cause was not found. | Do each test again on the last release, and compare the hashes before and after. | The Tex Mechanica mod, MP7 |
| `./port baseline check` prints `DIFFERENT` for a file of `data/`. | A command replaced a stored result: a convert run with `-o` into a baseline folder, a new extraction, or a build. | Find the command. For a release: a build with another esx version can give other bytes. Run `./port baseline update` only for a change that the user accepted. | This repository |
| `./port destiny game session` stops with the exit code 1: "the session file has the session ... with the label ...". | The session file has a session with a different label. A second user can have started it. | Run `esx probe status`. Wait, or ask the owner of that session. `--take-over` stops it: ask the user first. | This repository |
| The recording has no frame, or black frames. | The capture settings. | The pipeline of [game-test.md](game-test.md). | The Last Word |
| A test fails, and the probe has no session. | A second agent stopped the session: the two used one session file. | `esx probe status` before each start and each stop. Stop only your ID. Run the test again before you look for a fault in the mod. | M77, the Tex Mechanica mod |
| A wait for a sound event fails. | The event name `SoundPlay.NAME` is wrong for a wait. | `{ event = "SoundPlay", payload = "WPNRifleSubmachineGunReloadMagOut" }` | MP7 |
| Waits fail in a test at a slow game speed. | A wait started after its event. Timeouts of about 100 s started the idle camera, and the first-person graph then sends no clip event. | Put the wait on the step that starts the action. Use shorter timeouts. | MP7 |
| The weapon does not draw. The setup step of the test fails. | The vanilla Deliverer does not draw in the test game, also with no mod. The cause was not found. | Test the vanilla template weapon alone first. The template of the PPK is the 10mm pistol. | PPK |
| `esx probe run --overwrite`: option error. | No such option. | Remove the report folder, or use a new one. | The New Vegas game tests |
| The weapon checks of esx report a missing mesh. | The checks did not read the archives of the release. | `--archive 'NAME - Main.ba2' --archive 'NAME - Textures.ba2'` | MP7 |
| `esx render ... -o FILE` stops when the file is there. | It does not replace a file. | `--overwrite` | The Destiny chat |
| `esx probe start --display inherit` ends with a timeout after 180 s. | The display of the desktop had no socket file. | A gamescope window with its own display. That window closed after 2 minutes (a segmentation fault of gamescope; the cause was not found). | MP7 |
| The game goes into the sights about 2.1 s after `ActionSighted`. | Not known. It is the same for each weapon. | Not a fault of a clip. Report it. | Each Destiny game test |
| The camera kicks at each shot. | The recoil of the weapon record. | Not a fault of a clip. The vanilla weapon does the same in the same session. | The Last Word |
| A moving object leaves a row of copies behind it. | The agent thinks that it is the anti-aliasing of the game. No test with it off was done. | Not a fault of a clip. Vanilla objects show it also. | The Last Word |
| The top of the picture has a black and yellow area. | The sky of the test cell `QASmoke`. | Not a fault. It is there before the weapon is in the hand. | The Last Word |
| The Pip-Boy is in the view. | The clips of the source bring the left forearm far into the view. | Not a fault of the retarget. | The Last Word |
| Each dark surface has a green tint. | The light of the test cell `QASmoke`. | Not a fault. The vanilla .44 has the same tint there. | The Destiny game tests |
| The last part of the draw clip does not show fully. | The graph starts the blend to the idle 0.5 s before the end of the draw clip. | A fact of the graph. | The Last Word |

## The tools and the computer

| Sign | Cause | Rule or correction | Found in |
| --- | --- | --- | --- |
| `./port` stops with the exit code 3. | A thing that the command needs is missing. The program did not start. | Read the message, or run `./port doctor`: each missing thing has the command that makes it. | This repository |
| `./port selftest` prints `FAIL` for a part. | `python`: a file does not compile. `port.toml`: a table has a fault, or a program file is not there. `tests`: a test of `portkit` failed. `git`: git has, or can add, a file with a game file ending or a NUL byte. | The lines below the part name each fault. For `git`: move the file below `data/`. | This repository |
| A program prints one line for a file that is not there, with no traceback. | A program that imports `portkit` shows a file error as one line. | `FO4PORTS_TRACEBACK=1` shows the place in the program. | This repository |
| `./port destiny states` gives no state for the weapon. | The weapon tag is the tag of the class. The content group is not in the tag tree. | The weapon tag comes from the row of the pattern entity (in the tool). | Hammerhead |
| The set file of the extraction has no `ready`, `fire` or `reload`. | The tag rule of the extraction is proved for a hand cannon only. | `./port destiny states MANIFEST.json` reads the graph again. | The Khvostov, The Chaperone |
| `./port destiny find` prints "No item name contains ..." (exit code 1). | The weapon is not in this build of the game. | Tell the user the build date. Do not take a different weapon in its place. | Hawkmoon |
| An additive clip shows a pose that looks complete. | The extraction applies the offsets to the first frame of one full-pose clip. | The name ends with `_add`, and the manifest has `additive: true`. Do not use it as a full pose. | The Last Word |
| Blender scales the frame numbers of a clip. | The scene was not at 30 frames for each second before the import. | Set 30 frames for each second before the import. | The Last Word |
| `./port destiny check validate` stops at a clip with `[hold_end]`. | The source has fewer frames than the result. | The checks use the last source pose again (in the tool). | The Destiny chat |
| A byte check of New Vegas clips shows each clip as different. | Only `retarget synth hkx` ran. The work folder had no `parts.json`, so the collision step did not run, with no error. | Run `parts` first. The `retarget` step now stops when the parts file is not there. | MP7 |
| A byte check shows "0 changed" after a real change. | The `hkx` step of `fnv convert` writes into the work folder. Only `install` copies to the output folder. | Compare the files of `out/fo4/hkx` of the work folder, or run `install`. | The New Vegas chat |
| `./port fnv convert` gives a shorter clip list. | The rig folder has no clip of the template. | The tool now stops with advice. `./port fnv make-rig` makes the clips. | The New Vegas tools |
| The source tree has `__pycache__` folders. | Blender does not read `PYTHONDONTWRITEBYTECODE`. | `sys.dont_write_bytecode = True` in each program that runs in Blender. | The New Vegas tools |
| Two check runs of one clip at the same time give wrong pictures. | One work folder for two runs. | An output name for each run. | MP7 |
| A change of a shared solver changes the poses of other weapons. | The new rule was in the solver with no option. | A set key that is off by default. Then make each other weapon again and compare. | M77 |
| Two releases are different from the recorded ones after a small change of a tool. | A change of 0.00003 in two source files. | A small change counts. Run the regression after each change. | The Destiny chat |
| A background run reports the exit code 0, and the work failed. | The code is that of the wrapper. | Read the last line of the log. | The Destiny chat |
| A stop command stops the shell of the agent (exit code 144). | `pkill -f TEXT` also finds the shell, whose command line has that text. | Stop a process by its process ID. | The Destiny chat |
| A command fails in zsh. | zsh does not split a variable into words. A glob with no match stops the command. `=====` in a command fails. | `${=VAR}` or a small `sh` script. Quote each glob. | Each chat |
| The disk for temporary files is almost full. | The folder for temporary files is a RAM disk. | Put the build and the work data in a folder on a disk. In this repository each result is below `data/`. | MP7 |
| The chat shows the old picture after a correction. | The chat program keeps a picture by its path. | A new file name for each picture or video that you make again. | The Last Word, each chat |
| The packages of Marathon do not open: a segmentation fault. | The Oodle 3 shim. Oodle 9 reads the thread block of Windows. | `./port marathon setup` builds the Oodle 9 shim. | M77 |
| The animation decoder stops: "-1 is not a valid Space_Type". | Its version `marathon` is for an earlier build. | Three corrections at run time (in the tool). | M77 |
| m2x stops: "no tag of the class ...: the layouts of this file are for another build". | The game has a new build. | After an update, run `./port marathon tag64`. If the message stays, the layouts must be found again ([marathon/extract/README.md](../../marathon/extract/README.md)). | Marathon |
| `./port marathon extract` stops: "has no row in the art table. Give --art ITEM". | The item is a variant of a different item. | `--art "BASE ITEM"`. `./port marathon find` prints `no entity of its own` for such an item. | M77 |
| A text search of the packages gives thousands of matches. | The text has 3 characters. | A longer text (`Omnipositor`, not `M77`). | M77 |
| The shader reader prints nothing useful for a shader of Marathon. | The shader is DXIL, not the bytecode of Direct3D 11. | `./port marathon notes dxil MATERIAL` (it needs `llvm-dis`). | M77 |

## What is not proved

* Each row is from the weapon that its last column names. A rule was not tested on each
  other weapon.
* A row with "(in the tool)" says what the chat changed. No test of this repository makes
  the old fault again to show that the tool prevents it.
* The cause is "not known" in these rows: the gun bone at the origin of the world, the wait
  with `clip_end`, the second case of `ammo.set`, the plugin with other bytes, the sights
  that come 2.1 s late, the vanilla Deliverer that does not draw, the window of gamescope
  that closed, the light parts that are too bright in daylight.
* The row for a faster reload is from the document of esx. It was not tested.
* [The sign table of the skill](../../.claude/skills/diagnose-port-fault/references/signs.md)
  is a short copy of this document. Change the two together.
* The rows of the New Vegas chat for esx and for the probe are from esx of 2026-10-05. A
  later version of esx can behave in a different way.
