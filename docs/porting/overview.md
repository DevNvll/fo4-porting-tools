# The port of a weapon to Fallout 4: the stages, the gates and the rules

This covers all three sources. It gives the stages of a port, the gate of each stage, what
"correct" means, and the rules that came out of four chats of port work. Each source has its
own procedure document.

| Source | Input | Converter | Procedure |
| --- | --- | --- | --- |
| Fallout: New Vegas | An extracted weapon mod: the model (`.nif`) and the first-person animations (`.kf`) | `./port fnv convert` | [fnv.md](fnv.md) |
| Destiny 2 | The game folder. `./port destiny extract` makes the glTF files. | `./port destiny convert`, `./port destiny model` | [destiny.md](destiny.md) |
| Marathon | The game folder. `./port marathon extract` makes the glTF files. | `./port marathon convert`, `./port marathon model`, which run the Destiny programs | [marathon.md](marathon.md) |

In the same folder, [troubleshooting.md](troubleshooting.md) lists every known sign with its
cause and its rule, [checks.md](checks.md) explains each check and how to read its numbers,
[game-test.md](game-test.md) covers the test in the game, and [lessons.md](lessons.md) keeps
the history of the corrections.

## The stages of a port

Do the stages in this order. Do not start a stage until the gate of the one before it is
true.

| # | Stage | What you do | Gate |
| --- | --- | --- | --- |
| 1 | Prepare | Fill in `data/config.toml`, then make the rig folders and the environments. See [getting-started.md](../getting-started.md). | `./port doctor AREA` prints `Result: each setting and each check is ok.` |
| 2 | Get the input | For New Vegas, extract the mod archive and look for `.kf` and `.nif` files. For Destiny 2 and Marathon, extract the weapon from the game. | You have the files. Stop if the mod has no animation file. If the game build does not have the weapon, stop and tell the user. |
| 3 | Examine the data | Read which clip the game uses for each state, where the gun is in each clip, which clip moves each part, and how each clip starts and ends. Make pictures of the clips. | For every clip you will use, you know its state, that the gun is in the hand, and which clip moves each part. |
| 4 | Convert | Run the converter. For Destiny 2 and Marathon, write the set file first. | The numbers the converter prints are in the expected range. See [checks.md](checks.md). |
| 5 | Check before the game | Make the numbers of every clip. Look at each hand in pictures from the game camera, with the source above the result. | No finger joint bends back. Every hand that holds the gun touches it. You looked at each hand and found none of the four defects listed below. |
| 6 | The model and the mod project | For Destiny 2 and Marathon, run `./port destiny model`. Write `mods/NAME/`: `esx.toml`, the item file and the behavior source. Then run `./port mod build NAME`. | The build has 0 issues and 0 warnings. The esx weapon checks find nothing. |
| 7 | The byte checks | Run the conversion a second time, and run the regress command of the area. Then run `./port baseline check`. | The same bytes. After a change to a tool, every clip that differs has a name and a reason. No stored result in `data/` differs from its sha256 on record in `baselines.sha256`. |
| 8 | The game test | Only when the user asked for it or permitted it. Record the weapon in the test copy of the game and read the trace, as [game-test.md](game-test.md) describes. | 0 failed ops. You looked at frames of each recording. The trace has the clips and the events you expect. The release has the hashes of stage 7. No game process remains. |
| 9 | The documents | Write `mods/NAME/README.md`: what the mod has, the choices, what is proved, what is not proved, the limits. Add the weapon to the regression. When the user accepts the port, run `./port baseline update`. | Every statement has its command or its file. Every program in the document ran. `baselines.sha256` has the new clips and the new release. |

## What "correct" means

A port is correct when every property in this table is true. "Proof" gives the command. "Not
a proof of" names the fault that passed that check in the chats.

| Property | Proof | Value of the ported weapons | Not a proof of |
| --- | --- | --- | --- |
| The same input gives the same bytes | `./port fnv regress`, `./port destiny regress`, `./port marathon regress`, or a second run into a second folder and `cmp` | 0 files differ | That a clip is correct |
| A change to a tool did not change an earlier weapon | The same regress commands | 0 files differ, or a list of the clips that changed and why | That a clip is correct |
| Nobody replaced a stored result | `./port baseline check` | 602 files, 0 different (2026-10-06) | That the bytes on record are correct |
| The gun in every clip is where the source gun is | `./port destiny check gun` | At most 0.009 to 0.015 units per vertex | A rule that changes the source: `[gun]`, `[compose]`, `[hand_pose]` |
| Every wrist is at the source wrist | The `[retarget]` line of the converter, `./port destiny check gun` | At most 0.003 units for Destiny 2. 1.02 units for the M77, because `knuckles = "align"` moves the wrist. | The fingers |
| The HKX file has the poses | The `pos err` value of the `[hkx]` line | Below 0.02 units for Destiny 2. 0.023 to 0.086 units for New Vegas, with 40-bit rotations. | That the poses are good |
| No finger joint bends back, and every joint is a hinge | `./port destiny check fingers` | `joints bent back: none` for Destiny 2. The M77 has the first joint of a thumb at 3.3 to 4.9 degrees. | The place of a finger on the gun |
| The hands are not deeper in the gun than the source hands | `./port destiny check contact` | The Last Word 2.2 to 5.7 percent against 3.3 to 10.5 in the source | A hand that is away from the gun |
| Every hand that holds the gun touches it | `./port destiny check touch`, `touch-table` | 5 to 42 percent of the vertices of a hand are nearer than 0.5 cm in the hold pose | That the pose is the pose of the source game |
| The hands look correct | Pictures from the game camera and close views of each hand, the source above the result. A person or an agent looks. | No number | A fault that the source also has |
| The mod is complete | `./port mod build NAME`, `esx plugin check-weapons`, `esx scene weapon` | 0 issues, 0 warnings, 0 findings | The look in the game, a glass, a clip |
| The game loads the weapon and plays its clips | `./port destiny game record`, with the trace | 40 to 44 ops, 0 failed | The look of the hands, the walk clips, the sound |
| In the sights the eye is on the sight | A game picture of 1280 x 720 | The reticle is less than 1 pixel from (640, 360) | The size of the reticle against the source game |

The first task of the Destiny chat named four defects to look for in pictures: fingers
through the gun, broken or deformed fingers, a wrong wrist rotation, and a thumb that is not
aligned. Look for all four in every picture before every report.

No check in this repository compares a result with a picture of Destiny 2 or Marathon. For
those two sources, "correct" comes from the game files and from Blender pictures.

## The rules for each source

Every rule comes with the event that showed it. [lessons.md](lessons.md) has the full
history.

### Measure, then decide

1. **Examine the data before you write the configuration.** The last two Destiny ports lost
   much time to facts that the data shows in minutes: a gun bone at the origin, a part that
   moves in a second clip, a reload from three states.
2. **Each rule has its measurement.** In a set file, the measurement that gave a rule sits
   beside it as a comment.
3. **A name is not a fact.** The bone `b_pump` of The Chaperone is a lever that turns 99
   degrees. Count the vertices of a bone and look at a picture.
4. **Prove a cause from the data, then correct.** For the put-away of The Last Word, the
   agent compared with the vanilla .44 in the same session, read the trace, and then read
   the trigger time from the graph file. It was 0.233 s.
5. **Correct the rule, not the frame.** Every hand fault in the New Vegas chat was a fault
   of a rule, and every correction changed the clips of all weapons at once.

### Look before you test

6. **Look at each hand in a picture from the game camera before a game test.** The user of
   the New Vegas chat wrote: "validate the retarget with blender before testing ingame." The
   first task of the Destiny chat had the same rule.
7. **Look at the whole picture.** The game pictures of The Chaperone at the hip were made for
   the sight. The left hand was in them, 1 cm from the gun, and the agent did not examine it.
8. **A count is not a look.** In the New Vegas chat, the count of hand vertices in the gun
   was better with fingers that were open and wrong, 631 against 1184. The user found every
   hand fault in a picture. None of the agent's numbers found one.
9. **Look at each picture before you use it.** One recording had the game's idle camera in
   it, and a frame sheet showed that.

### What a check proves

10. **A check against the source does not find a fault that the source has.** The left hand
    of The Chaperone was 1.0 cm from the gun in the result and 0.9 cm in the source. Every
    check passed, and the user saw the fault in the game.
11. **Measure the property that you want.** For "the hand touches the gun", measure the
    distance from the hand to the gun with `./port destiny check touch`. The difference from
    the source is another property.
12. **A check that compares with the source proves the retarget.** It does not prove a rule
    that changes the source. Only a picture of the source game, or the game test, proves
    such a rule.
13. **A game test that passes is not a correct clip.** The first New Vegas test passed 30 of
    30 with the fingers in the gun. The third-person reload of The Chaperone passed with a
    reload that ended 12 frames early and with sounds of a different clip. The event trace
    showed both faults.

### Bytes

14. **The same input must give the same bytes.** Run the conversion twice and compare.
15. **A change to a tool must keep the bytes of every ported weapon.** If a clip must change,
    name the clip and give the reason, as "Rules for a change" in
    [ARCHITECTURE.md](../ARCHITECTURE.md) says. A change of 0.00003 in two source files made
    two releases different from the recorded ones.
16. **A new rule in a shared tool is off by default.** The first finger rule for the M77 went
    into the shared solver without an option and changed the poses of the Destiny weapons.
    It then moved behind a set file key.
17. **Test the release that you built last.** Take the sha256 of each release file after the
    build, and compare after the tests. `baselines.sha256` records every tested release and
    every baseline clip, and `./port baseline check` shows a stored result that a command
    replaced. Run `./port baseline update` only for a change that the user accepted.

### What you tell the user

18. **State each choice as a choice.** The damage, the capacity, the state of a sight glass
    and the pose clip of a hand are choices. The tools do not read these values from the
    source game.
19. **State what is not proved.** Every document that makes claims has a part "What is not
    proved".
20. **Say how you read a short request.** "port the third person animation" named no weapon.
    The agent ported three weapons and said so.
21. **Run each program that a document shows, and check each number against the built
    files.** Testing one program of the Destiny procedure found a wrong statement in an
    older document.
22. **A picture or a video that you make again gets a new file name.** The chat program
    showed the old picture of a changed file, and the user saw the old defect.

### The games and the computer

23. **Do not start a game without the user's permission.** Do not write into the `Data`
    folder of an installed game. Do not start Marathon, because it has an anti-cheat program.
24. **The game test has one session for the computer.** Run `esx probe status` before a
    start and before a stop. Stop only the session that you started.
25. **Nothing of a game goes into git.** The models, the textures and the animations belong
    to their owners. Do not publish a built mod.
26. **Convert the whole clip set of a weapon.** The Fallout 4 graph asks for clips by name.
    For a name that the mod does not have, the game plays the vanilla clip, with the hands
    of the vanilla gun.

## What is not proved

* The rules come from work on nine weapons in four chats, on 2026-10-05 and 2026-10-06: one
  hand cannon, one auto rifle, one machine gun, one lever shotgun and one submachine gun of
  Destiny 2, one assault rifle of Marathon, and one pistol, one bullpup rifle and one
  submachine gun of New Vegas. Today's tools do not read the input of that last one, the
  MP7, a 3ds Max source. A different weapon class can need a rule that is not here.
* Nobody compared a port with a picture of the source game.
* No person tested a port with a keyboard and a mouse, and no port was tested at the weapons
  workbench, in power armor, or in the installed game.
