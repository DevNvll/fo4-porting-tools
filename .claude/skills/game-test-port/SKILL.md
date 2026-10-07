---
name: game-test-port
description: Gives the procedure to test or record a ported weapon in Fallout 4 with the probe of esx (a headless test copy of the game) and the game test programs of this repository, with the permission rule, the rules for the one session of the computer, the order of the tests, the trace of clips and events, and the sha256 of the tested release. Use when the user says "record the game testing the gun", "test it in game", "run the game with the mod", when a step needs a picture from the game (a glass, a third-person reload, the left hand), or before any command with "esx probe" or "./port destiny game".
---

# Test a port in the game

`esx probe` starts a test copy of Fallout 4 with no window and takes requests. It does not
change the installed game. The game test programs send the steps of a test and record the picture.

**State of these programs:** `game session` and `game all` (`record`, `third`, `reloads`,
`sight`) had one complete run in this repository, in the test world: 10 commands, 0 failed.
`game results`, `game trace` and `game shots` did not run in it (`docs/porting/game-test.md`).

## Before the start (three rules)

1. **Permission.** Do not start the game with no permission of the user. "Record the game
   testing the gun" is a permission for that test. If you are not sure, ask.
2. **One session for the whole computer.** Run `esx probe status` before each start and
   each stop. Start only when `session` is null and `fallout4_pids` is empty. Stop only the
   session that you started, by the ID that your start command printed. Do not stop a
   session that you find: wait, or ask its owner.
3. **No input, no game folder.** Send no keyboard input and no mouse input. Do not write
   into a game folder. Do not start Marathon or Destiny 2.

In each command below, `esx` is the program of the setting `esx` (`./port paths get esx`).
Do the checks of `validate-port` first: a game test is slow, and it does not show a hand
fault by itself.

## Steps

### 1. Write down the sha256 of the release

```sh
(cd data/mods/MOD/build/release && sha256sum *) > data/destiny/port/validation/NAME/release_tested.sha
```

The file has one line for each release file, with the file name and no folder. A build with
a newer esx version can give other bytes than a release that was tested before. To test or
record a release that was tested before, do not build: use `--no-build` in step 2.

### 2. Start the session

```sh
esx probe status
./port destiny game session MOD LABEL [--cell ID | --world] [--no-build]
```

The program builds the mod (not with `--no-build`), starts the session with
`data/mods/MOD/build/release` and prints the session ID. Keep the ID in a note of your own
task. `--cell ID` is the cell where the game starts (default `QASmoke`). `--world` gives no
cell: the game starts in the cell of the test world of the test folder
([references/probe.md](references/probe.md)).

The program keeps its ID in `data/destiny/port/work/probe_session.txt`. That is one file for
all users of this repository. When it runs again, it stops the session of that file. If the
label of the file is not your label, it prints a warning: a second agent can have started
that session. Use a label of your own, read the warning, and stop if it comes.

Gate: the program printed an ID, and `esx probe status` shows that ID with your label.

### 3. Run the tests in this order

```sh
./port destiny game all --weapon EDITORID:CAPACITY[:auto][:reloads] --out DIR \
    --mod MOD --tested data/destiny/port/validation/NAME/release_tested.sha --dry-run
```

`--dry-run` prints each command and runs nothing: run it first. The order of the tests is:
the first-person test with a video (`game record`), the third-person reload from three sides
(`game third --record`), one reload for each count of rounds (`game reloads`, with
`:reloads`), then pictures at the hip and in the sights (`game sight`). Keep this order: the
sight pictures before the first-person test gave a failed `ammo.set` in each test.

About two minutes after the start of a session the game turns the camera about the player,
because the session has no input. `game all` waits until the session is `--wait` seconds old
(default 140) and then sets the first-person view, which ends that camera. When you run one
program alone, wait in the same way, or end the recording before two minutes. Record with no
other heavy job on the computer: a Blender validation at the same time spoiled a recording.

Gate: each test has 0 failed ops. With `--mod` and `--tested` the program compares the
sha256 of the release after the tests with your file, and prints "the release is the tested one".

### 4. Look at each recording and each picture

```sh
./port destiny check video-sheet DIR/EDITORID/record/record.mp4 OUT.jpg --count 20
```

Gate: you opened the sheet and each picture. No frame has the idle camera. Each hand is on
the gun at the hip and in the sights, and the sight is at the center in the sights. When a thing
looks wrong, compare with the vanilla weapon in the same session: that found the put-away fault.

### 5. Read the trace

```sh
./port destiny game trace --session ID --weapon EDITORID --loaded N --view first
```

`trace.json` of a recording has each clip and each event that the game started, at 120 ticks
for each second. Gate: the clips are the clips of the mod (the graphs have the prefix of the
behavior source, for example `TXCGunBehavior`). `reloadEnd` comes at the time of the event of
the clip. Only the sounds of this clip play. A test with 0 failed ops is not a correct clip.

### 6. Stop your session and check the computer

```sh
esx probe stop --session ID
esx probe status
```

Gate: `session` is null and `fallout4_pids` is empty. If a process stays, read the status
again after some seconds. Do not stop a process by a text of its command line.

### 7. Keep the results

```sh
./port destiny game results --out data/destiny/port/validation/NAME --record DIR/EDITORID/record
```

It copies the results into the validation folder (`--third`, `--sight`, `--reloads` also).

## Stop and ask the user

* Before the first start of the game in a task.
* When `esx probe status` shows a session that you did not start.
* When a test has a failed op whose cause you do not find. Report it. Do not hide it.

## Common faults

| Sign | Cause | What to do |
| --- | --- | --- |
| `item.give`: "No form has this EditorID" | The session started with the project folder | The release folder (`game session` does this) |
| `ammo.set`: "The engine did not keep the requested counts" | No reserve count, or a cause that is not known | Give `loaded` and `reserve`. Keep the order of step 3, or use a new session. |
| The session is gone in the middle of a test | A second agent stopped it | The test is not a result. Run it again before you look for a fault in the mod. |
| The sha256 of the plugin is not the tested one | A build after the tests | Do each test again on the last release, or use `--no-build` |

## What to report

The session ID and its label, each test with its count of ops and of failed ops, the clips
that the game played, the time of `reloadEnd`, the pictures that you looked at, the sha256 of
the tested release, and the state of the computer: no game process remains, nothing was
written into the `Data` folder of the installed game, the mod is not installed. Then what the
test does not prove: the walk, run and jump clips (no move input), the sound, power armor, the
weapons workbench, the installed game. If you started the game with no new request, say so.

## More

* [references/probe.md](references/probe.md): esx, the test world, the ops, known faults.
* [docs/porting/game-test.md](../../../docs/porting/game-test.md); [destiny/port/README.md](../../../destiny/port/README.md), "Checks" and "The game test".
