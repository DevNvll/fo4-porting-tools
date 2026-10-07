# The port of a weapon to Fallout 4: the stages, the gates and the rules

This document is for each source: Fallout: New Vegas, Destiny 2 and Marathon. It gives the
stages of a port, the gate of each stage, what "correct" means, and the rules that four
chats of port work showed. The procedure of one source is in its own document.

| Source | Input | Converter | Procedure |
| --- | --- | --- | --- |
| Fallout: New Vegas | An extracted weapon mod: the model (`.nif`) and the first-person animations (`.kf`) | `./port fnv convert` | [fnv.md](fnv.md) |
| Destiny 2 | The game folder. `./port destiny extract` makes the glTF files. | `./port destiny convert`, `./port destiny model` | [destiny.md](destiny.md) |
| Marathon | The game folder. `./port marathon extract` makes the glTF files. | `./port marathon convert`, `./port marathon model` (the programs of Destiny) | [marathon.md](marathon.md) |

Other documents of this folder: [troubleshooting.md](troubleshooting.md) (each known sign
with its cause and its rule), [checks.md](checks.md) (each check and how to read its
numbers), [game-test.md](game-test.md) (the test in the game) and [lessons.md](lessons.md)
(the history of the corrections).

## The stages of a port

Do the stages in this order. Do not start a stage before the gate of the stage before it is
true.

| # | Stage | What you do | Gate |
| --- | --- | --- | --- |
| 1 | Prepare | Give the settings in `data/config.toml`, and make the rig folders and the environments ([getting-started.md](../getting-started.md)). | `./port doctor AREA` prints `Result: each setting and each check is ok.` |
| 2 | Get the input | New Vegas: extract the archive of the mod and look for `.kf` and `.nif` files. Destiny 2 and Marathon: extract the weapon from the game. | The files are there. For a mod with no animation file: stop. For a weapon that the game build does not have: stop, and tell the user. |
| 3 | Examine the data | Read which clip the game uses for each state, where the gun is in each clip, which clip moves each part, and how each clip starts and ends. Make pictures of the clips. | For each clip that you will use, you know its state, you know that the gun is in the hand, and you know the clip that moves each part. |
| 4 | Convert | Run the converter. For Destiny 2 and Marathon, write the set file first. | The numbers that the converter prints are in the expected range ([checks.md](checks.md)). |
| 5 | Check before the game | Make the numbers of each clip. Look at each hand in pictures from the game camera, the source above the result. | No finger joint bends back. Each hand that holds the gun touches it. You looked at each hand and found none of the four defects (below). |
| 6 | The model and the mod project | Destiny 2 and Marathon: `./port destiny model`. Write `mods/NAME/` (`esx.toml`, the item file, the behavior source). `./port mod build NAME`. | The build has 0 issues and 0 warnings. The weapon checks of esx have no finding. |
| 7 | The byte checks | Run the conversion a second time, and run the regress command of the area. Write down the sha256 of each release file. | The same bytes. For a change of a tool: each clip that is different has a name and a reason. |
| 8 | The game test | Only when the user asked for it or permitted it. Record the weapon in the test copy of the game, and read the trace ([game-test.md](game-test.md)). | 0 failed ops. You looked at frames of each recording. The trace has the clips and the events that you expect. The release has the hashes of stage 7. No game process remains. |
| 9 | The documents | Write `mods/NAME/README.md`: what the mod has, the choices, what is proved, what is not proved, the limits. Add the weapon to the regression. | Each statement has its command or its file. Each program of the document ran. |

## What "correct" means

A port is correct when each property of this table is true. The column "Proof" gives the
command. The column "Not a proof of" gives the fault that passed that check in the chats.

| Property | Proof | Value of the ported weapons | Not a proof of |
| --- | --- | --- | --- |
| The same input gives the same bytes | `./port fnv regress`, `./port destiny regress`, `./port marathon regress`, or a second run into a second folder and `cmp` | 0 files differ | That a clip is correct |
| A change of a tool did not change an earlier weapon | The same regress commands | 0 files differ, or a list of the clips that changed and why | That a clip is correct |
| The gun of each clip is at the place of the source gun | `./port destiny check gun` | At most 0.009 to 0.015 units for each vertex | A rule that changes the source (`[gun]`, `[compose]`, `[hand_pose]`) |
| Each wrist is at the source wrist | The line `[retarget]` of the converter, `./port destiny check gun` | 0.003 units at most (Destiny 2). 1.02 units for the M77, because `knuckles = "align"` moves the wrist. | The fingers |
| The HKX file has the poses | The line `[hkx]`, value `pos err` | Below 0.02 units (Destiny 2). 0.023 to 0.086 units (New Vegas, 40-bit rotations). | That the poses are good |
| No finger joint bends back, and each joint is a hinge | `./port destiny check fingers` | `joints bent back: none` | The place of a finger on the gun |
| The hands are not deeper in the gun than the source hands | `./port destiny check contact` | The Last Word 2.2 to 5.7 percent against 3.3 to 10.5 in the source | A hand that is away from the gun |
| Each hand that holds the gun touches it | `./port destiny check touch`, `touch-table` | 5 to 42 percent of the vertices of a hand are nearer than 0.5 cm in the hold pose | That the pose is the pose of the source game |
| The hands look correct | Pictures from the game camera and close views of each hand, the source above the result. A person or an agent looks. | No number | A fault that the source has also |
| The mod is complete | `./port mod build NAME`, `esx plugin check-weapons`, `esx scene weapon` | 0 issues, 0 warnings, 0 findings | The look in the game, a glass, a clip |
| The game loads the weapon and plays its clips | `./port destiny game record`, with the trace | 40 to 44 ops, 0 failed | The look of the hands, the walk clips, the sound |
| In the sights the eye is on the sight | A game picture of 1280 x 720 | The reticle is less than 1 pixel from (640, 360) | The size of the reticle against the source game |

The first task of the Destiny chat named four defects to look for in pictures: fingers
through the gun, broken or deformed fingers, a wrong wrist rotation, a thumb that is not
aligned. Look for these four in each picture before each report.

No check of this repository compares a result with a picture of Destiny 2 or of Marathon.
"Correct" for those two sources is from the files of the game and from pictures of Blender.

## The rules for each source

Each rule has the event that showed it. [lessons.md](lessons.md) has the full history.

### Measure, then decide

1. **Examine the data before you write the configuration.** The two last Destiny ports
   needed much time for facts that the data shows in minutes: a gun bone at the origin, a
   part that moves in a second clip, a reload from three states.
2. **Each rule has its measurement.** A rule in a set file has the measurement that gave it
   as a comment.
3. **A name is not a fact.** The bone `b_pump` of The Chaperone is a lever that turns 99
   degrees. Count the vertices of a bone and look at a picture.
4. **Prove a cause from the data, then correct.** For the put-away of The Last Word the agent
   compared with the vanilla .44 in the same session, read the trace, and then read the
   trigger time from the graph file: 0.233 s.
5. **Correct the rule, not the frame.** Each hand fault of the New Vegas chat was a fault of
   a rule, and each correction changed the clips of each weapon at the same time.

### Look before you test

6. **Look at each hand in a picture from the game camera before a game test.** The user of
   the New Vegas chat wrote: "validate the retarget with blender before testing ingame." The
   first task of the Destiny chat had the same rule.
7. **Look at the whole picture.** The game pictures of The Chaperone at the hip were made for
   the sight. The left hand was in them, 1 cm from the gun, and the agent did not examine it.
8. **A count is not a look.** In the New Vegas chat the count of hand vertices in the gun
   was better with fingers that were open and wrong (631 against 1184). The user found each
   hand fault in a picture, and no number of the agent found one.
9. **Look at each picture before you use it.** One recording had the idle camera of the game
   in it. A frame sheet showed that.

### What a check proves

10. **A check against the source does not find a fault that the source has.** The left hand
    of The Chaperone was 1.0 cm from the gun in the result and 0.9 cm in the source. Each
    check passed, and the user saw the fault in the game.
11. **Measure the property that you want.** For "the hand touches the gun", measure the
    distance of the hand to the gun (`./port destiny check touch`). The difference to the
    source is a different property.
12. **A check that compares with the source proves the retarget.** It does not prove a rule
    that changes the source. Only a picture of the source game, or the game test, proves
    such a rule.
13. **A game test that passes is not a correct clip.** The first New Vegas test passed 30 of
    30 with the fingers in the gun. The third-person reload of The Chaperone passed with a
    reload that ended 12 frames early and with sounds of a different clip. The trace of the
    events showed the two faults.

### Bytes

14. **The same input must give the same bytes.** Run the conversion two times and compare.
15. **A change of a tool must keep the bytes of each ported weapon.** If a clip must change,
    name the clip and give the reason ([ARCHITECTURE.md](../ARCHITECTURE.md), "Rules for a
    change"). A change of 0.00003 in two source files made two releases different from the
    recorded ones.
16. **A new rule in a shared tool is off by default.** The first finger rule for the M77 was
    in the shared solver with no option, and it changed the poses of the Destiny weapons.
    The rule then went behind a key of the set file.
17. **Test the release that you built last.** Write down the sha256 of each release file
    before the tests, and compare after the tests.

### What you tell the user

18. **State each choice as a choice.** The damage, the capacity, the state of a sight glass
    and the pose clip of a hand are choices. The tools do not read these values from the
    source game.
19. **State what is not proved.** Each document that makes claims has a part "What is not
    proved".
20. **Say how you read a short request.** "port the third person animation" named no weapon.
    The agent ported three weapons and said so.
21. **Run each program that a document shows, and check each number against the built
    files.** The test of one program of the Destiny procedure found a wrong statement in an
    older document.
22. **A picture or a video that you make again gets a new file name.** The chat program
    showed the old picture of a changed file, and the user saw the old defect.

### The games and the computer

23. **Do not start a game without the permission of the user.** Do not write into the `Data`
    folder of an installed game. Do not start Marathon: it has an anti-cheat program.
24. **The game test has one session for the computer.** Run `esx probe status` before a
    start and before a stop. Stop only the session that you started.
25. **Nothing of a game goes into git.** The models, the textures and the animations belong
    to their owners. Do not publish a built mod.
26. **Convert the whole clip set of a weapon.** The Fallout 4 graph asks for clips by name. A
    name that the mod does not have gives the vanilla clip, with the hands of the vanilla
    gun.

## What is not proved

* The rules are from the work on nine weapons in four chats (2026-10-05 and 2026-10-06):
  one hand cannon, one auto rifle, one machine gun, one lever shotgun and one submachine gun
  of Destiny 2, one assault rifle of Marathon, and one pistol, one bullpup rifle and one
  submachine gun of New Vegas. The tools of today do not read the input of that submachine
  gun (the MP7, a 3ds Max source). A different weapon class can need a rule that is not
  here.
* No port was compared with a picture of the source game.
* No port was tested by a person with a keyboard and a mouse, at the weapons workbench, in
  power armor, or in the installed game.
