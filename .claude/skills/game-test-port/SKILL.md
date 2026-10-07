---
name: game-test-port
description: Gives the procedure to test or record a ported weapon in Fallout 4 with the probe of esx (a headless test copy of the game) and the game test programs of this repository, with the permission rule, the rules for the one session of the computer, the order of the tests, the trace of clips and events, and the sha256 of the tested release. Use when the user says "record the game testing the gun", "test it in game", "run the game with the mod", when a step needs a picture from the game (a glass, a third-person reload, the left hand), or before any command with "esx probe" or "./port destiny game".
---

# Test a port in the game

`esx probe` starts a test copy of Fallout 4 with no window and takes requests. It does not
change the installed game. The game test programs send the steps of a test and record the picture.

**State of these programs:** `game session` and `game all` (`record`, `third`, `reloads`,
`sight`) had one complete run in this repository: 10 commands, 0 failed. `game results`,
`game trace` and `game shots` did not run in it (`docs/porting/game-test.md`).

## Before the start (four rules)

1. **Permission.** Do not start the game with no permission of the user. "Record the game
   testing the gun" is a permission for that test. If you are not sure, ask.
2. **One session for the whole computer.** Run `esx probe status` before each start and
   each stop. Start only when `session` is null and `fallout4_pids` is empty. Stop only the
   session that you started, by its ID. Do not stop a session that you find: wait, or ask.
3. **No input, no game folder.** Send no keyboard input and no mouse input. Do not write
   into a game folder, `plugins.txt`, the saves or the Proton prefix. Do not start the
   graphical interface of esx. Do not start Marathon or Destiny 2.
4. **The checks first.** Do `validate-port` first: a game test does not show a hand fault.

In each command below, `esx` is the program of the setting `esx` (`./port paths get esx`), and
`T` is your folder for the results: `T=data/destiny/port/work/NAME/game_test; mkdir -p $T`. A
recording needs GStreamer, PipeWire and gamescope (`./port doctor` does not examine them). A New
Vegas mod (`PPK`, `FAMAS`) has a test plan of esx, not steps 2 to 5: [references/probe.md](references/probe.md).

## Steps

### 1. Decide if the session builds the mod

* A release that passed a game test before (each of the 7 mods): do not build. Run
  `./port baseline check`. Gate: `0 different`. Then use `--no-build` in step 2.
* A new mod, or a mod with a change: step 2 builds it. Another esx version can give other
  bytes. One comparison was made: esx `d3e520c` built the 7 mods with the bytes on record.

### 2. Start the session, then write down the sha256 of the release

```sh
esx probe status
./port destiny game session MOD LABEL [--cell ID | --world] [--no-build]
grep -F "mods/MOD/build/release/" baselines.sha256 > $T/release.sha     # a release on record
(cd data/mods/MOD/build/release && sha256sum *) > $T/release.sha        # or: a new release
```

The program builds the mod (not with `--no-build`), starts the session with the release
folder and prints the session ID. Keep the ID in a note of your own task. `--cell ID` is the
cell where the game starts (default `QASmoke`). `--world` gives no cell: the game starts in the
test world ([references/probe.md](references/probe.md)). Take the hashes after the build, with
one of the two last lines. Write no `release_tested.sha`: `baselines.sha256` is the record.

The program keeps its ID and its label in `data/destiny/port/work/probe_session.txt`: one file
for all users. When it runs again with the same label, it stops the session of that file. When
the file has another label, the program does not stop that session and has the exit code 1:
a second agent can have started it. `--take-over` stops it: ask the user before you give it.

Gate: the program printed an ID, and `esx probe status` shows that ID with your label.

### 3. Run the tests in this order

```sh
./port destiny game all --session ID --weapon EDITORID:CAPACITY[:auto][:reloads] --out $T \
    --mod MOD --tested $T/release.sha --dry-run
```

Give `--session ID` each time: with none the program takes the ID of the shared file. Run
it with `--dry-run` first: it prints each command and runs nothing. The order is: the
first-person test with a video (`game record`), the third-person reload from three sides
(`game third --record`), one reload for each count of rounds (`game reloads`, with `:reloads`),
then `game sight`. The sight pictures before the first-person test gave a failed `ammo.set`.

About two minutes after its start, a session with no input turns the camera about the player.
`game all` waits until the session is `--wait` seconds old (default 140), then sets the
first-person view: that ends the camera. One program alone: wait in the same way. Record with
no other heavy job on the computer.

Gate: each test has 0 failed ops, and the program prints "the release is the tested one".

### 4. Look at each recording and each picture

```sh
./port destiny check video-sheet $T/EDITORID/record/record.mp4 OUT.jpg --count 20
```

Gate: you opened the sheet and each picture. No frame has the idle camera. Each hand is on
the gun at the hip and in the sights, and the sight is at the center in the sights. When a thing
looks wrong, compare with the vanilla weapon in the same session: that found the put-away fault.
For a recording that is made again: compare its ops, its step times and its clips with the old one.

### 5. Read the trace

```sh
./port destiny game trace --session ID --weapon EDITORID --loaded N --view first
```

`trace.json` of a recording has each clip and each event of the game, at 120 ticks for each
second. Gate: the clips are those of the mod (the graphs have the prefix of the behavior source,
for example `TXCGunBehavior`). `reloadEnd` comes at the time of the event of the clip. Only the
sounds of this clip play. A test with 0 failed ops is not a correct clip.

### 6. Stop your session and check the computer

```sh
esx probe stop --session ID
esx probe status
```

Gate: `session` is null and `fallout4_pids` is empty. If a process stays, read the status
again after some seconds. Do not stop a process by a text of its command line.

### 7. Keep the results

```sh
./port destiny game results --out data/destiny/port/validation/NAME --record $T/EDITORID/record
```

It copies the results into the validation folder (`--third`, `--sight`, `--reloads` also).
When the user accepts a new or changed mod: `./port baseline update`. Say that the file changed.

## Stop and ask the user

* Before the first start of the game in a task. Before `--take-over`. When `esx probe status`
  shows a session that you did not start.
* When a test has a failed op whose cause you do not find: report it, do not hide it.

## Common faults

| Sign | Cause | What to do |
| --- | --- | --- |
| `ammo.set`: "The engine did not keep the requested counts" | No reserve count, or a cause that is not known | Give `loaded` and `reserve`. Keep the order of step 3, or use a new session. |
| "THE RELEASE IS NOT THE TESTED ONE", or `baseline check` prints `DIFFERENT` | A build after the hashes were taken | Do each test again on the last release, or use `--no-build` |

## What to report

* The session ID and its label. Each test with its ops and failed ops. The clips that the
  game played, the time of `reloadEnd`, the pictures that you looked at.
* The sha256 of the tested release, and the result of `./port baseline check`.
* The state of the computer: no game process remains, nothing was written into the `Data`
  folder of the installed game, the mod is not installed.
* What the test does not prove: the walk, run and jump clips, the sound, power armor, the
  weapons workbench, the installed game. If you started the game with no new request, say so.

## More

* [references/probe.md](references/probe.md): esx, the test world, the ops, known faults.
* [docs/porting/game-test.md](../../../docs/porting/game-test.md); [destiny/port/README.md](../../../destiny/port/README.md), "Checks" and "The game test".
