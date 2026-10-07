# What the chats learned

The tools of this repository came from four chats between one user and AI agents, on
2026-10-05 and 2026-10-06. This document is the history of those chats for a new person:
each correction of the user, the faults that the tools or the agents made, and how each
fault showed. The rules that came from this history are in [overview.md](overview.md), and
the signs are in [troubleshooting.md](troubleshooting.md).

| Chat | Date | Work |
| --- | --- | --- |
| New Vegas | 2026-10-05 | The MP7, the FAMAS F1 and the Walther PPK of New Vegas. The tools of `fnv/`. |
| The extraction of Destiny 2 | 2026-10-05 and 2026-10-06 | The Last Word as glTF files. The tools of `destiny/extract/`. |
| The Destiny 2 ports | 2026-10-06 | The Last Word, the Khvostov 7G-02, Hammerhead, The Chaperone, The Huckleberry. The tools of `destiny/port/`. |
| Marathon | 2026-10-06 | The M77. The tools of `marathon/`. This chat is a fork of the chat of the Destiny 2 ports. |

How to read the tables:

* The times are those of the transcripts. They are 3 hours later than the local time of the
  files of that day.
* The words of the user are exact, with the letter case and the spelling of the user.
* The column "Lesson" is the reading of the agents that made the notes of the chats, unless
  it is a quote.
* A row with **C** in its first column is a correction of the work. Each other row is a
  request that showed a fault or changed the work.

## The corrections of the user

### New Vegas, 2026-10-05

| | Time | Words of the user | What was wrong | Cause | Correction | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| **C** | 05:09 | "validate the retarget with blender before testing ingame." | The plan was to go to the game with no check of the poses. | No check with pictures was in the plan. | The source and the result in Blender pictures before each game test. This became a standing rule. | Look before you test. |
| **C** | 05:51 | "the fingers are clipping through" (with a game picture of the reload) | The fingers were inside the grip and the magazine. | The build copied the finger rotations of the source. The Fallout 4 finger bones are shorter (6.96 against 8.02 units for the index finger), and the knuckles are about 0.5 units further out. | A solver that puts each joint on the line of the source finger, then a collision step. | The game test passed 30 of 30 with this fault. A count of passed steps is not a look. |
| **C** | 06:01 | "why are these fingers broken" (with crops of the close views of the agent) | The fingers opened and pointed away from the grip. | A collision step turned a finger bone until its end was above the surface, up to 80 degrees. The source fingers are already partly in the gun (0.2 units in to 0.8 units out, with a finger radius of about 0.8). | The step was removed. A small step moves a finger out to a floor distance only. | The contact count was better with the broken step (631 against 1184 vertices). The count alone did not show the fault. The user saw a test picture of a step that was not finished: do not show such a picture. |
| **C** | 06:17 | "the hand is not rotating properly" (a crop of an older game picture) | The fist looked turned away from the gun. | The same cause as at 05:51: the fingers were in the grip. The first idea of the agent was that the game uses the clip in a different way. A Blender render over the game picture showed that the game plays the clip data exactly. | The same correction. In the same work the agent corrected three differences from the vanilla clips. | Find which build and which frame a picture is from. An old picture can show a fault that is already corrected. Put a Blender picture from the game camera beside it. |
| **C** | 06:46 | "now the left hand seems clipping" (a game picture at a slow speed) | The base of the magazine came through the left palm. | The repair of the agent moved each wrist to align the knuckles. The palm moved 0.6 units to the side. | No wrist shift. The two palms agree to 0.5 units with the wrists at one place. | A correction of one fault can make a second one. Check each hand again after each change of a rule. |
| | 12:36 | "can this process be deterministic or does it only work with the MP7?" | Two Python files had data of the MP7. | The tool grew with one weapon. | The answer: deterministic (two runs, the same sha256), and not general. | Prove "the same bytes" with two runs. |
| **C** | 12:41, 12:44 | "make only the changes to make it general and run in the mateba." Then: "if theres no animation, don'tport it I'll find another" | The agent started to read the model and the vanilla revolver for a mod with no animation file. | The archive had 4 models, textures, one sound and the plugin. The mod uses the vanilla revolver animations of New Vegas. | Stop. Check an archive for `.kf` files first. | Check the input before the work. A port of animations needs animations. |
| **C** | 13:25 | "the fingers are a bit deformed" (a crop of 70 x 89 pixels of the left thumb) | The thumb was fully straight with a twist at its base. The skin had lumps. | The Fallout 4 hand mesh is modelled with bent fingers (about 45 and 30 degrees at the two joints). The source thumb is straight on the handguard. | `[fingers] min_bend = 0.3`: each joint keeps 30 percent of its rest bend. With 0 the output has the same bytes as before. | Each check passed with this fault: the Blender sheets, the contact counts, the game test (55 of 55). The user looks at a small part of a picture. Look at each visible finger at a large zoom. |
| **C** | 14:54 | "improve the config file for the port. can we assume most of the defaults? no need to handle archives." | A conversion file of 165 lines for each weapon, and an archive step. | Each value was a key. | Defaults for each value. Two keys are sufficient. The extracted mod is the input. | Ask only what the tools cannot find. |
| **C** | 15:14 | "i mean, I don't want to create a mod. i just want the animations to work on fo4" | Each weapon was a complete esx project (records, attachments, textures, test plans). | The agent had made more than the user wanted. | One command with a folder as its input, no conversion file, no esx. | Decide the scope with the user at the start. Do not add a feature that the user did not ask for. |
| **C** | 16:22 | "the thumb is kinda misaligned need a bit of touches" (a crop of one panel of a check sheet, frame 88) | The thumb was 0.7 units in front of its place on the grip, and its first joint was bent 12 degrees back. | The skin of a finger is not at the center of its bones: the Fallout 4 thumb skin is 0.4 units to the pad side, the New Vegas thumb skin 0.13 units to the nail side. And the least-bend rule accepted a joint that bent back. | `skin_center` (skin on skin, not bone on bone), and the least bend about the hinge of the bone. | The user compares each Fallout 4 panel with the source panel above it. Do the same. |
| **C** | 16:59 | "cleanup the repo files. remove esx integration. just the fnv animation in fnv animation out." | The tool had steps for the model, the attachments, the textures and the project files, and a reader for 3ds Max. | The tool had grown with each request. | 60 files became 21. The tag `before-animation-only` has the removed programs. | The tools of `fnv/` make only the clips. The models of the mods `PPK` and `FAMAS` are from the tools at that tag. |

What these corrections have in common:

* The user found each hand fault in a picture. No number of the agent found one.
* The two later hand faults were faults of a rule. Each rule correction changed the clips of
  the two guns at the same time.
* The four first finger values (the corner lift 0.5, the floor 0.65, the largest move 1.15,
  the filter of 1.5 frames) were tuned with pictures of the MP7. The FAMAS and the PPK were
  ported later with the same values.

### The extraction of Destiny 2, 2026-10-05 and 2026-10-06

| | Time | Words of the user | What was wrong | Cause | Correction | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| **C** | 00:57 | "what is this" (with a picture) | In frame 50 of the reload clip the weapon was 0.9 m from the right hand. | The export wrote keys only for the bones that move in a clip. Blender does not reset a bone that has no key, so the gun bone kept the pose of the clip that was shown before. The game data and the decoder were correct. | Each clip has keys for each of the 80 bones. The preview resets the pose before each clip. `check-glb` reports an action that has bones with no keys. | A fault of the preview can look like a fault of the data. Show other clips first, then the clip, and compare. |
| **C** | 01:02 | "this image doesn't look like a reload. what is this, the gun is disassembled floating and the hand is pointing up". 42 seconds later: "I see on file explorer, looks better" | The chat showed the old copy of the picture. The file on the disk was the corrected one, with the same name. | The chat program keeps a picture by its path. | A new file name for each picture or video that is made again. | The user sees the old defect and thinks that the correction failed. |
| | 01:02 | "dont stop until you have ads, reload, sprint, equip and unequip animations set. send a video or a sheet." | The first report said that the agent did not decode the graph that selects the clips. It had selected three reload clips from pictures, and two of them were reloads of other hand cannons. | The full file has the clips of each weapon that shares the rig. | The decode of the animation graph, and a file with the clip of each state. | "identified from the game data, not from a guess". Read the graph. |
| | 01:22 | Not words of the user: a correction that the agent of this chat sent to the port chat. "The first-person camera anchor of the Destiny rig is the bone `b_utility`, NOT the head bone plus an offset." | The handoff file had the camera at the head bone. In the reload video the gun was too far to the right. | A wrong fact in the handoff file. | The camera is `b_utility`. The message had a proof: in `iron_sight_idle` the sight is at (0.000, 0.006, 0.413) m in the space of `b_utility` on each frame. | A fact of a handoff can be wrong. Give each claim a proof. When a fact is wrong, send the correction with its effects. |

Hawkmoon, the second weapon of the first request, is not in the game build (23 August 2020).
The agent said so in its report.

### The Destiny 2 ports, 2026-10-06

| | Time | Words of the user | What was wrong at that time | Cause | Correction | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| | 01:15 | The first task. The agent of the extraction chat wrote it for the user: "Retarget the Destiny 2 first-person RELOAD animation of The Last Word (a revolver) to the Fallout 4 first-person rig." | In the first result the joint after the knuckle turned 20 to 38 degrees to the side. | The Fallout 4 palm is 0.8 units wider, and the collision step moves a joint in any direction. | The rule "one plane for each finger". Result: 127 frames, 6 events. | The task named the defects that the user looks for: "fingers through the gun, broken or deformed fingers, a wrong wrist rotation, a thumb that is not aligned". Look for these four before each report. |
| | 02:17 | "retarget the other animations from the last word table. once you finish, use esx to pack the weapon into fallout 4" | With only the reload from Destiny, the game blended from and to the idle pose of the vanilla .44, which is a different hand pose. In the new clips the muzzle moved 0.03 to 0.09 units from frame to frame. | 40-bit rotations in the clip writer. | 48-bit rotations. 24 clips, and a build with 0 issues. | Convert the whole clip set from one source. |
| | 03:02 | "record the game testing the gun" | On put-away the gun went out of the hand one frame before the hand moved. The first recording was mostly the idle camera of the game. | The vanilla graph removes the gun 0.233 s before the end of the put-away clip. The Destiny clip is 0.133 s long. | `[hold_end] WPNUnEquip = 8`. Only that clip changed. The 23 other clips kept their bytes. | The game has rules that no Blender check shows. Compare with the vanilla weapon in the same session. Prove the cause from the graph data. |
| | 03:54 | "now port the khovostov" | No extraction of the gun. The state table had no idle, draw, put-away and reload. No clip for the shot. In the game the sight was below the screen center. The build stopped. Two recordings were not usable. | The tag rule of the extraction was proved for a hand cannon only. Destiny aligns a rifle sight when the game runs. One keyword has no rules for power armor. | `./port destiny states`, the template `combatrifle`, `[synth]`, `[sight]`, `like AnimsCombatShotgun`. 27 clips. | "The second weapon needed new code in eight places". A new weapon class needs programming. |
| | 05:20 | "how reusable is this tool without AI?" | Three programs were not in `tools/`. No command wrote a first set file. No procedure for a new weapon. Local paths in the defaults. No tests. | The tool grew with each weapon. | The answer was "Partly." Later: the procedure document, and the monorepo. | Give an honest answer. This question led to this repository. |
| | 05:22 | "port hammerhead now" | The states program gave no tags. The gun has 12 moving parts. In the bind pose the belt is a straight line. Destiny has one clip for one shot. | The weapon tag of Hammerhead is the tag of its class, not its content group. | The rule of the pattern row, the template `combatrifle_parts`, `[bones]`, `part_rest = "hold"`, `[auto]`. | The report of this port came about 35 minutes late, in the report of the next request. Report a finished request before the next one starts. |
| | 06:00 | "make destiny shaders work in the weapons." | The gun was light gray in the game. The Destiny gun is dark. | The colors of a gun are in its dyes. The first conversion gave each metal pixel a specular value of 0.72 to 0.9. | `./port destiny dyes`, the gear shader, a specular value from the reflectance, each shader as a second receiver part. | Say how you read a short request. Measure which guns a feature applies to (the percent of pixels with a dye). |
| | 13:53 | "make the red dot work" | The sight had no reticle. | The extraction has only the render stage `opaque`. esx makes no new effect shader. | `./port destiny reticle`, a sight part from a vanilla template mesh, the aim point at the reticle. | A feature that is missing can be in data that the extraction does not read. |
| **C** | 14:28 | "its stretched. the center reticle is too big" | The reticle was 1.22 units wide, half the width of the glass. | The first version gave the quad its mesh size. The vertex shader puts the quad 2.25 m before the camera, so the player sees 0.44 degrees. | The size from the angle: 0.24 units on the glass, 5 times smaller. | The size of an object that a shader places is in the shader, not in the mesh. The agent found no geometric stretch, said so, and asked: "If you see a different stretch, tell me where." Do the same for a word that is not clear. |
| | 15:09 | "now fixes the khovostov red dot" | The Khvostov had no reticle. | The same cause. | The same tools. 14 minutes. 5 clips in the sights changed, 22 kept their bytes. | When a rule is a tool, the second weapon is fast. State the limit: the ring is white with a pink edge. |
| | 16:21 | "port the third person animation" | In third person the game used the vanilla clips. In the first test the game pulled the left hand to the grip. The right fingers were open. The left arm was up to 8.3 units too short. | The bone `WeaponIKTargetL` was at its rest place. The third-person data of Destiny opens the fingers. Destiny holds a machine gun at the hip. | `./port destiny third`, the step `third`, `WPNAssemblyPose`, `gun = "source"`. | First find what the target game has: Fallout 4 has 4 third-person files for one weapon. The user named no weapon: the agent ported three and said so. |
| | 17:42 | "Port the Chaperone and the Huckleberry. create one single mod with tex tex mechanica weapons, including last word" | The Huckleberry: the hands held no gun, and the parts moved in a second clip. The Chaperone: the reload is three states. In third person: wrong clips, additive clips, a reload that ended 12 frames early, shell sounds of a different clip, a build stop for power armor. | See [troubleshooting.md](troubleshooting.md). | `[gun]`, `[compose]`, `[piece_events]`, one clip for each count of rounds, `[third.hold_end]`, `silent`, `[third.power_armor]`. | Examine the data before the set file. This became step 3 of [destiny.md](destiny.md). |
| | 20:18 | "document the porting insights and process in this folder" | One statement of the reference document was too narrow. | The agent ran the program of step 3 of the new document: only 2 of the 59 full-pose clips of The Huckleberry have the gun in the hand. | The statement was corrected in three places. | Run each program that a document shows. |
| **C** | 21:02 | "the hands seems far from the model, not touching it" (with two game pictures) | The left hand of The Chaperone was 1.02 cm from the gun. The left wrist of The Huckleberry was 2.5 cm from its place on that gun. | The clips of the hands are clips of the weapon class. The source has the same gap (0.90 cm), so each check against the source passed. | `./port destiny pose`, `[hand_pose]`, `./port destiny check touch`. Now 5.2 percent and 20.9 percent of the vertices are nearer than 0.5 cm. | "Measure the property that you want (the hand touches the gun), not only the difference to the source." The story is below. |
| | 23:22 | "create a zip file of the tex mechanica mod in /Downloads folder" | The system has no folder `/Downloads`. | The user meant the `Downloads` folder of the home folder. | The zip file with the three release files, with the tested hashes. | Say how you read a path. Deliver the tested release and prove it by its hashes. The agent also wrote that the assets are those of Destiny 2 and that the zip must not be published. |
| | 23:29, 23:30 | "create a monorepo ... keep the fixtures and outputs and copyrighted assets inside a gitignore folder. ... include skills and documents for porting correctly based on the chat transcriptions." Then: "organize and architecture the code and structure to serve as a reusable tool for both ais and humans" | Three tool sets in two folders, with paths of one computer. | | This repository. | The assets of a game are never in git. A person and an agent use the same commands, documents and checks. |

Three times the user wrote only "continue". Two times the agent had ended its turn with "No
response requested." while a task was open: one time after a message that said "No reply is
necessary", and one time in the middle of a search for a cause. The lesson: "No reply is
necessary" is about the message. It does not close the open task. Do not end a turn while a
task is open.

### Rules of the chat tool

These rules are for the chat tool of these chats. They are not rules of the repository, so
they are only here.

* "No reply is necessary" in a message does not close the open task (above).
* A report in the chat embeds a picture or a video by its absolute path. A document of the
  repository has no path of one computer.
* The chat shows the old picture of a file that was made again with the same name. Give a
  picture or a video that is made again a new file name.
* A `cd` in a compound command changes the working folder that the tool reports. Start each
  command in the root of the repository, or use absolute paths.
* The chat sends the notice "The user hasn't heard from you in a while" when the agent is
  silent. Give a short status line while a long step runs.
* The exit code of a background run is that of its wrapper. Read the last line of the log.

### Marathon, 2026-10-06

| | Time | Words of the user | What was wrong | Cause | Correction | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| | 17:31 | "this should be the same engine so the same tools should work with minimal changes. test by extracting the model, textures and animations of the gun M77 Omnipositor" | A statement to test. The answer: "partly true". | The package reader, the glTF writer and the form of the data are the same. The Oodle version, the 64-bit hashes, each class number and each offset are new. | No change: the package reader, the glTF writer. Three corrections at run time: the animation decoder. New: the Oodle 9 loader, `tag64`, `m2x.py`. | Test a statement such as "the same tools work", and answer with what is the same and what is not. |
| | 21:00 | "now extract the rig and port it to fallout 4" | The first work had no first-person rig and no first-person clip. | The arm entities and the animation graph were not decoded. | The first-person file with the clip of each state. | |
| | 21:06 | "if you can use the same destiny rig, its one less step" | Advice during the work. | | The rig of Marathon is the rig of Destiny (names, axes, camera bone, gun bone). The converter reads the file with no change. | Compare the two rigs with numbers: the names, the lengths, the local axes. |
| **C** | 21:32 | "finger looks dislocated on this one frame 78" (with a picture) | In the reload, the first bone of the left index finger pointed to the wrist in frames 74 to 83. | Two causes together. The knuckles of the Fallout 4 hand were 1.42 units (2 cm) from the source knuckles. And the finger is a hook on the bolt handle: the base rule then put the first bone on the line behind the fingertip. | `knuckles = "align"` and `closed_fingers = true`. The fingertip error in the reload went from 6.2 to 2.15 units. | Before this message the agent had looked at pictures of the reload from the camera only. The finger check found a turn of 170 degrees at once. Run the finger check on each clip before the first look at pictures. |

How the finger correction went, in 23 minutes:

1. Pictures of the left hand at the frames 74 to 82, the source and the result, 4 views. Then
   the finger check on the reload clip.
2. A trace of the solve of that finger at the fault frames.
3. A first correction: a "hook rule" in the shared solver. New pictures.
4. The earlier guns again with the changed solver. The hook rule changed their poses.
5. A trace of the same finger at the frames 28 to 46: a second fault, the hand on the
   magazine.
6. A measurement of the knuckle places of the Marathon hand and of the Destiny hand against
   the Fallout 4 hand. This gave the first cause.
7. The knuckle alignment as an option. A version with the four knuckles only put the thumb
   root 0.82 units to the side of the gun, so the thumb root went into the alignment.
8. The hook rule was replaced with the rule for a closed finger.
9. The rule went behind a set option, and the poses of the five Destiny guns were the poses
   of before (largest difference 0.0).
10. Each clip of the M77 and the finger checks again. Final pictures of the fault frames.

The first idea, a rule for this one case in the shared solver, changed the poses of the
Destiny weapons. The second fault (frames 28 to 46) showed only because the agent looked for the same fault
in other frames.

## The story of "measure the property that you want"

1. 17:42 to 20:18. The agent ported The Chaperone and The Huckleberry. Each number was good:
   the gun at most 0.012 units from the source, no joint bent back. The game tests had 44
   and 40 ops with 0 failed.
2. The agent made game pictures of each gun at the hip and in the sights. They were for the
   sight. The left hand was in them, and the agent did not examine it.
3. 20:18. The report had seven points under "What is not correct or not tested". None was
   about the left hand.
4. 21:02. The user sent two game pictures: "the hands seems far from the model, not touching
   it".
5. The agent took the first frame of the idle check videos. The result was equal to the
   source. So the retarget was correct, and the fault was in the source.
6. The agent examined the first-person graph of Fallout 4 for hand IK. It has none. So the
   game does not correct the hand.
7. The agent measured the Destiny hand mesh against the gun in the hold pose. The Chaperone:
   the nearest vertex of the left hand was 0.89 cm away, and 0 of 1903 vertices were nearer
   than 0.5 cm.
8. The agent searched for a clip that corrects the hand. Each gun file has additive clips of
   2 or 3 frames that have no entry in the animation set. The agent added each one to the
   idle pose and measured.
9. The Chaperone, clip `80BBD62D`: the nearest vertex at 0.03 cm, 33 vertices nearer than
   0.5 cm. Clip `80BBD626` has the same offsets with the opposite sign, and with it the hand
   is 1.0 cm away.
10. Two measurement faults came on the way. The first version of the measure used only the
    last mesh primitive: 59 vertices in place of 1903 for each hand. One later measurement
    used a wrong option. The agent corrected the two before the numbers went into a document.
11. The correction: `./port destiny pose` adds the offsets at the level of the rig controls
    and solves the rig again. The weight of the offsets is 1 while the left wrist is less
    than 3 cm from its place of the hold pose, and 0 at more than 8 cm.
12. The result for the Fallout 4 hand: The Chaperone from 0.0 percent to 5.2 percent, The
    Huckleberry from 12.4 to 20.9 percent.
13. The agent measured the three earlier guns with the new check. They did not have the
    fault (5.1 to 10.6 percent).
14. All game tests ran again. A second complete run gave the same bytes for the 67 clips.

The lessons:

* A check against the source does not find a fault that the source has.
* A count of vertices inside the gun does not show a hand that is away from the gun.
* Examine each hand in the game picture of the hold pose, also when the picture is for a
  different purpose.
* For each property that the user will see, write a check that measures that property.

## The faults that the tools or the agents made, and how each one showed

### The Destiny 2 ports

| Fault | How it showed | Correction |
| --- | --- | --- |
| The reticle had the size of its quad | The user saw a reticle that was too large | The size from the distance of the vertex shader |
| Bright values on the glass | A red haze (Hammerhead), a green haze (The Huckleberry) in the game | The values of Destiny with a small reticle. `glass_scale`. |
| The session started with the project folder | `item.give`: no form has this editor ID | `--mod PROJECT/build/release` |
| `WeaponIKTargetL` at its rest place | In the game the left hand went to the grip | The bone has the matrix of the left hand |
| The right hand of the third-person source | Open fingers on the grip | The grip of the first-person hold pose, while the hand is on the grip |
| The gun on the vanilla stance | The left arm was up to 8 units too short | `gun = "source"` |
| The events of the third-person clip from the median of each part | Wrong times for a gun with a belt | The bolt, or `align` |
| The first tag list of the third-person program | The reload of a rifle for a revolver. The clip of the class for The Huckleberry. No clip of The Chaperone. | The tag list of the first-person clips, in the order of the tag tree. The stance for each stance. |
| The clip of the gun parts by its frame count | For the shell state of The Chaperone: a clip that is in no state of the graph of the gun | The graph of the gun entity |
| No frames after the motion of a third-person reload | The time to `reloadEnd` was 0.4 s shorter than the clip | `[third.hold_end]` |
| Sounds in the default reload clip | Three shell sounds in a reload with one shell | `silent`, and a clip for each count |
| A recording 2 minutes after the start of the session | The camera turned about the player in the video | A session that is older than 2 minutes |
| Tests before the last build | The hash of the plugin was not that of the tested file | All tests again on the last release |
| A stop command with the session ID of the session file | It stopped the session of a second thread, which had started its session with the same program | `esx probe status` first. The ID that the start command printed. The program now stops with the exit code 1 for a session file with a different label. |
| Tests before the hand distance check | The game tests of The Chaperone passed, and the user then found the hand fault in a game picture | The numbers of each clip and the hand distance before the game test ([destiny.md](destiny.md), step 9) |
| The clips of the weapon class for the left hand, with no pose clip of the gun | The user saw in the game that the left hand did not touch the gun | `./port destiny pose`, `[hand_pose]`, and `./port destiny check touch` for each new gun, before the game test |
| The game pictures at the hip were made for the sight | The left hand was in those pictures, and the agent did not examine it | Examine each hand in the game picture of the hold pose |
| A statement in a document was written from memory | The test of a program of the document showed a different number | Run each program that a document shows |
| Three statements about a shader were not measured | The agent measured the built textures before the report, and removed them. One was false: the three shaders have an iridescence value (33, 35 or 25). | Check each number of a document against the built files |
| `pkill -f` with a text of the command line | It stopped the shell of the agent (exit code 144), at least two times. One time it left two Blender processes. | Stop a process by its process ID |
| A change of the third-person program moved two source files by 0.00003 | The releases were different from the recorded ones | The byte check after each change |

### New Vegas

| Fault | How it showed | Found by | Correction |
| --- | --- | --- | --- |
| Hand poses in the four `WeaponIKTarget` bones | A comparison with the vanilla clips | The agent | These bones keep the reference transform |
| A full pose in an additive clip of the submachine gun graph | A read of the blend hint of the vanilla clip | The agent | The tools of `fnv/` do not replace `WPNIdleSightedWobble` or a clip whose name ends with `Add` |
| A clip of an ammunition check as the first idle | A game picture after the draw | The agent | `WPNIdleReadyA` to `D` are plain idles |
| A casing that passes near the camera | A game picture of the fire step | The agent | A limit of a bullpup gun |
| The first test plan had failed waits | Failed steps | The agent | The correct form of a wait for a sound event. A wait on the step that starts the action. |
| The PPK did not draw | The setup step of the test failed | The agent | The cause was the vanilla Deliverer. The agent removed one thing after the other (the reload variant, the clips, the behavior source, the textures) and then tested the vanilla weapon alone. The template became the 10mm pistol. |
| A byte check gave 27 different clips | A hash comparison | The agent | The step `parts` had not run, so the collision step did not run, with no error. The retarget now stops when the parts file is not there. |
| A byte check gave "0 changed" after a real change | A hash comparison | The agent | The `hkx` step writes into the work folder. Only `install` copies. |
| Two check runs of one clip at the same time | Wrong pictures | The agent | An output name for each run |
| The plugin hash of the MP7 changed after a plain build | sha256 | The agent | The cause was not found. The game test ran again: 37 of 37. |

Methods that were tried and rejected, with the reason:

| Method | Why not |
| --- | --- |
| Copy the finger rotations | 1563 of 6209 hand vertices in the gun at the idle |
| Turn a finger bone above the surface, up to 80 degrees | It opens the hand on a round grip |
| A collision step with the depth of the source as the target | It does not converge |
| A wrist shift to the knuckles | The palm moves 0.6 units to the side |
| A fit of the palm by the nearest points of the two meshes | A result of 1.5 units, which the agent judged an artifact |
| The thumb with the rotations of the source | Deeper in the gun: 564 vertices, 1.27 units at frame 40 |
| Turn only the last part of a finger for the least bend | The fingertip went into the gun |

### The extraction of Destiny 2

| Fault | How it showed | Correction |
| --- | --- | --- |
| A bone with no keys keeps the pose of the clip before | The weapon 0.9 m from the hand in one frame | Keys for each bone. Reset the pose before each clip. |
| Additive clips shown as full poses | The agent reviewed the sheet of the 119 clips, then measured the control tracks | The manifest marks each additive clip (44 of 119 for The Last Word) |
| The camera at the head bone | The gun too far to the right in the reload video | `b_utility` |
| The preview camera pointed in a wrong direction (2 times) | The agent saw it in its own pictures | Look at each picture before you send it |
| The first-person file had no hands | The first renders. The armor item has no hand mesh. | The hands come from the player body entity |
| The indexes of the graph were used as clip indexes | The clip of a state did not fit | The index goes through the entry table of the animation set |
| The weapon tag rule was not complete | Some states gave no clip | The tags of the weapon, most specific first. For a port, `./port destiny states` reads the graph again. |
| The test "this bone moves" took the noise of the codec for motion | The final check | Limits above the noise |
| Cache files of Python in a folder that must not change | The port chat found `__pycache__` in the reference tools | `PYTHONDONTWRITEBYTECODE=1`. `./port` sets it. |

### Marathon

| Fault | How it showed | Correction |
| --- | --- | --- |
| The Oodle 3 shim with the Oodle 9 library | A segmentation fault. The backtrace was in the start code of the library. | A loader for Oodle 9 (`marathon/extract/oodle9/oodle9.c`) |
| The loader read freed memory | The first build of the loader | The pointer points into the mapped image |
| A text search for `M77` | Thousands of matches in binary data | Longer texts |
| The header of an array was read wrong | Row counts with no sense | The class is at +8, not at +12 |
| The decoder version `marathon` on this build | "-1 is not a valid Space_Type" | Three corrections at run time |
| 12 clips, not 15 | The count of the rows of the animation set | The plain clip list is read also |
| The pieces at their own coordinates | The first picture of the weapon file: the pieces on top of the grip | The named points |
| Three faults of the render program | An error, a small gun in the picture, a turned picture | Corrected |
| The first hook rule in the shared solver | The pose files of the Destiny guns were different | A set option, off by default |
| The first game test of the M77 failed | The recording stopped early, and the probe had no session | A second agent had stopped the session ([game-test.md](game-test.md)) |
| Two wrong statements in the document | A check of the manifest before the report | Corrected. They were written from memory. |

## Two areas, two answers

The tools of `fnv/` and the tools of `destiny/port/` do different things for one clip name.
The New Vegas chat read the blend hint of the vanilla clip `WPNIdleSightedWobble` of the
submachine gun graph: it is an additive clip, so the tools of `fnv/` do not replace it. The
Destiny sets give `WPNIdleSightedWobble` the sighted idle of the weapon, because with the
vanilla clip the hands had the pose of the vanilla gun in the sights. The game tests of the
Destiny weapons played that clip. No test compares the two answers on one weapon.

The same is true for the wrist. For a New Vegas rig a wrist shift to the knuckles was wrong
(the magazine came through the palm). For the rig of Marathon the key `knuckles = "align"`
moves the wrist 1.02 units, and the fingers are then at their places. Each answer has its
measurement. No rule says which one a new rig needs: measure the knuckles and the palm of
the two hands with the wrists at one place.

## The time of each piece of work

The times are those of an AI agent that works with no pause.

| Work | Elapsed |
| --- | --- |
| The reload of The Last Word, with the new tools | 61 minutes |
| The 23 other clips and the esx mod | 43 minutes |
| The first game recording, with one defect corrected | 33 minutes |
| The Khvostov, complete | 57 minutes |
| Hammerhead, until the validation ended | 39 minutes |
| The dyes and the shaders | 35 minutes |
| The reticle of Hammerhead | 52 minutes |
| The reticle of the Khvostov | 14 minutes |
| The third-person reload of three guns | 80 minutes |
| The Chaperone, The Huckleberry and the single mod | 156 minutes |
| The left hand on the two guns | 67 minutes |
| The extraction of the M77 (the model, the textures, the clips of the weapon) | About 65 minutes |
| The first-person rig of the M77 and its Fallout 4 port | About 71 minutes |

## What is not proved

* The notes of the chats mark some lessons as the inference of the agent that wrote them:
  the cause of the two turns that ended with "No response requested.", the reading that the
  question about the tool without AI led to the monorepo, and the reading that visible
  clipping of fingers is worse for the user than a small difference from the source pose.
  The user did not confirm them.
* The notes of the New Vegas chat come from a short form of the transcript with no tool
  results. Some answers of the agent are not in it as text.
* This document does not have each message of the chats. `data/transcripts/` and
  `data/notes/` (not in git) have the transcripts and the notes.
