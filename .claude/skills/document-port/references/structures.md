# The headings of each kind of document

## The README of a mod (`mods/NAME/README.md`)

The headings of `mods/TexMechanica/README.md` and `mods/M77/README.md`:

| Heading | Content |
| --- | --- |
| The title, and one paragraph | What the mod is, the source game of each weapon, the three release files. The sentence that the assets are those of a game and that a built mod must not be published. |
| What the mod has | Each weapon with its editor ID, the vanilla weapon that it copies, its values, its parts, its clips (the count, and a table of the source of each clip). |
| How the project was made | The commands that make the generated files again, complete, from the root of the repository: the extraction, `./port destiny convert`, `./port destiny model`, the step `third`, `./port mod build NAME --update-lock`. |
| Checks that passed (or: What is proved) | Each check with its command and its result: the build, the checks of esx, the regression, the numbers of the clips, the game test with its count of ops, the sha256 of the tested release. |
| What is not proved (or: What is not correct or not done) | Each thing that no test shows: the clips that did not play in the game, power armor, the workbench, the installed game, a comparison with the source game. |
| Limits | Each known defect that stays, with its number. Each choice (the damage, the capacity, a pose clip, the state of a glass). |

## The section of a weapon in the reference of the converter

The sections of `destiny/port/README.md` ("The Khvostov 7G-02", "The Chaperone"):

1. The set file and its template. The commands of the extraction.
2. What the extraction wrote (the count of first-person files, bones and clips), and the
   weapon tag.
3. A table: Fallout 4 clip, source (the state, the clip of the file, the count of frames).
4. One paragraph with a title in bold for each thing that was new in this weapon: the parts,
   the reload, the shot, the sight, the left hand. Each one has the measurement and the key
   of the set file.

Then add the weapon to the parts "What is proved", "What is not proved" and "Limits" of that
document, and to `destiny/port/regress.toml`.

## A row of the troubleshooting table

| Column | Content |
| --- | --- |
| Sign | What the user sees or what the tool prints, in those words. A quote of the message is best. |
| Cause | One sentence, with the number that proves it. Write "not known" when it is not known. |
| Rule | The key of the set file, the command, or "(in the tool)" when the tool does it now. |

Example: "The gun is out of the hand before the hand moves in the put-away | The graph
removes the gun 0.233 s before the end of the clip | `[hold_end] WPNUnEquip = 8`".

## A row of the fault table (the method)

| Column | Content |
| --- | --- |
| Fault | What the agent did. |
| How it showed | Who found it, and in which picture, number or message. |
| Correction | What to do in place of it. |

Example: "The game pictures at the hip were made for the sight | The left hand was in those
pictures, and we did not examine it | Examine each hand in the game picture of the hold pose".

## The parts "What is proved" and "What is not proved"

* "What is proved": each item is a statement and the command that proves it. Say when you
  ran it. Say who ran it when it was not you.
* "What is not proved": each item is a statement that no command of this repository repeats,
  or a thing that no test covers. A measurement of the first work goes here, with the file
  that is its evidence.
* Do not mix the two. A statement of an earlier document that you did not run stays in "What
  is not proved" of your document, or you name the document as its source.

## The report after a correction of the user

The model is the report after "finger looks dislocated on this one frame 78":

1. The result: the finger is correct in the frames 74 to 84.
2. The cause, with numbers: the knuckles of the Fallout 4 hand were 1.42 units from the
   source knuckles, and the finger is a hook on the bolt handle.
3. The change: two keys of the set file, off by default.
4. The proof: the picture of the fault frames (source above result, three views), the finger
   check, the reload in the game recording. The fingertip error went from 6.20 to 2.15 units.
5. The other weapons: the five Destiny ports keep their poses (largest difference 0.0).
6. The limit that stays: one finger turn of 61.8 degrees at frame 83, where the source finger
   turns 92 degrees.
