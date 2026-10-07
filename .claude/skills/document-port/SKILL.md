---
name: document-port
description: Gives the rules and the structure for the documents and the reports of this repository (the section of a weapon in a reference document, the README of a mod in mods/NAME, a row of the troubleshooting table, the report to the user), in simple technical English with the command that proves each statement and a part "What is not proved", and a script that checks the commands and the links of a Markdown file. Use when the user says "document the porting insights and process", when a port, a correction or a change of a tool is finished and needs its document, before each final report, and when a document names a command, a number or a file.
---

# Write the document of a port, and the report

A document of this repository tells the reader which command proves each statement. A
statement with no proof is in a part with the title "What is not proved". Two statements
that were written from memory were wrong, and a test of the commands of a document found a
wrong statement in an older document.

## When to use it, and when not

* Use it for each document below `docs/`, `mods/NAME/README.md`, the README of an area, and
  each report to the user.
* A comment in a set file: `write-set-file` has the form.

## The language

Write simple technical English (the style of ASD-STE100):

* Short sentences. One instruction for each sentence. Imperative for a step.
* The active voice. Say who does the action: "the tool prints", "I selected".
* One word for one thing. A clip is always "clip", not "animation" in one place and
  "sequence" in another. [docs/reference/glossary.md](../../../docs/reference/glossary.md) has the words:
  "conversion file" (New Vegas), "gun entity", "ops" (the count of a game test).
* No em dash, and no dash between two clauses. Use a period or a colon.
* Sentence case for each heading.
* No path of one computer. Write `/path/to/...`, or name the setting of `data/config.toml`.
* A command is in a code block, complete, from the root of the repository.

## Steps

### 1. Start with the result

Then, in this order: what the mod or the change has, the choices, what is proved, what is
not proved, the limits, the files. [references/structures.md](references/structures.md) has
the headings of each kind of document.

### 2. Give the proof of each statement

For each statement, name the command or the file that proves it. Say which statements are
measurements of the first work that no command of this repository repeats.

### 3. Check each number and run each command

Check each number against the built file (the set file, `summary.txt`, the manifest, the
output of the tool). Give a number its true precision: "less than 1 pixel", not "0.4 pixels".
Use the later value when two sources do not agree. Then check the commands and the links:

```sh
python3 .claude/skills/document-port/scripts/check_doc.py FILE.md [FILE.md ...]
```

The script finds each `./port` text that is not a command of `./port list` or of `./port`
itself, each option that the help of its command does not have, each link with no target,
each path of one computer and each em dash. It does not run a conversion. Run each example
yourself when its result is a statement of the document, if the rules of your task let you
run it. When two documents have the same list (the sign tables, the numbers of a correct
port, the probe rules), change the two together: the document below `docs/` is the source.

Gate: the script prints `ok` for each file, and you ran or verified each command.

### 4. Mark each choice and each assumption

"Capacity 30: this is my choice. The tools do not read the Destiny value." The damage, the
time between two shots, the state of a glass, a pose clip, the rule for the right hand in
third person are choices. An assumption has the word "assumption". A reading of data with no
name has the words "I read this as".

### 5. Pictures and videos

Look at each picture before you use it. Say what it shows: the clip, the frame, the camera.
A picture or a video that is made again gets a new file name before you embed it: a chat can
show the old picture of a file with the same name, and the user then sees the old defect.
Each picture and video is below `data/`. Nothing of a game goes into git.

### 6. A new fault gets a row

For each fault that the work found, add one row to
[docs/porting/troubleshooting.md](../../../docs/porting/troubleshooting.md): the sign as the
user or the tool gives it, the cause, the rule. Add a fault of the method to
[docs/porting/lessons.md](../../../docs/porting/lessons.md) with how it showed.

### 7. The report to the user

1. The result, in the first sentence.
2. The proof: each check with its command and its result.
3. The correction of the user, if there was one: the cause with its numbers, the change.
4. Each choice.
5. What is not correct, not tested or not proved. A fault whose cause you did not find.
6. Your own errors, under the words "My error".
7. After a game test, the state of the computer: no game process remains, nothing was
   written into the `Data` folder of the installed game, the mod is not installed.
8. The files, with paths. Say that the result has assets of a game and must not be published.

Say how you read a short request ("You did not name a weapon, so I ported ..."). Report a
finished request before the next one starts. Give a short status line while a long step runs.

## Stop and ask the user

* When a statement needs a test that the rules of your task do not let you run. Put it under
  "What is not proved" and say why.
* Before you publish or send a file that has assets of a game.

## Common faults

| Fault | Event |
| --- | --- |
| A statement from memory | Two statements of the Marathon README were wrong. A check of the manifest found them before the report. |
| A statement that is too wide | "No dye of these four looks has an iridescence value" was false: the three shaders have the values 33, 35 or 25 |
| A word such as "works" with no run | Write what you ran, and what it printed |
| A command of the chat, with old paths | Use only the commands of `./port list` and the folders of this repository |
| An old picture in the chat | A new file name for each picture that is made again |
| A late report | The report of one port came 35 minutes late, in the report of the next request |
| No public source named | Name it, and say what is your own reading |

## What to report about the document itself

The files that you wrote, the output of the check script, the statements that you could not
verify and where you put them, and each link that has no target.

## More

* [references/structures.md](references/structures.md): the headings of each kind of document.
* [docs/ARCHITECTURE.md](../../../docs/ARCHITECTURE.md), "Rules for a change".
* [mods/TexMechanica/README.md](../../../mods/TexMechanica/README.md) and
  [mods/M77/README.md](../../../mods/M77/README.md): two documents of a mod.
* [docs/reference/commands.md](../../../docs/reference/commands.md).
