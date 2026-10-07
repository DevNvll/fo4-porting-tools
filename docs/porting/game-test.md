# The game test with `esx probe`

The game test starts a test copy of Fallout 4 with the release of a mod, sends ops to the
game, and records the picture. `esx probe` does this: the game runs in a headless gamescope
of 1280 x 720 at 60 frames for each second, with no window. It is not the installed game,
and it writes nothing into the `Data` folder of the installed game. The test programs send
no keyboard input and no mouse input.

## The state of the game test programs

The game test programs of `destiny/port/check/` (`./port destiny game ...`) were adapted to
the layout of this repository, and one complete run in it passed on 2026-10-06:

```sh
./port destiny game session TexMechanica texmech-world --world --no-build
./port destiny game all --weapon TheChaperone:6:reloads --weapon TheHuckleberry:30:auto \
    --weapon TheLastWord:8 --out data/destiny/port/work/tex_mechanica_world \
    --mod TexMechanica --tested data/destiny/port/validation/tex_mechanica/release_tested.sha
```

* esx was a build of its commit `d3e520c` (the first version with the test world), given in
  `ESX_BIN`. The session started in the cell `WeapTest` of `TestWorldspace.esp`.
* 10 commands, 0 failed: `record` (44, 40 and 44 ops), `third` (85 ops for each weapon, each
  reload fills the gun), `reloads` (12 of 12), `sight` for the three weapons. The release had
  the tested hashes before and after.
* No recording has the turn of the idle camera.
* The six videos, the step files and the log are in
  `data/destiny/port/validation/tex_mechanica/world/`.
* That `game all` command had no `--session`: it used the ID of the session file. In a new
  run, give `--session ID` (rule 5).

`game results`, `game trace` and `game shots` did not run in this repository. Each other
result of this document is from the chats of 2026-10-05 and 2026-10-06, with the folders of
that time. The validation folders (`data/destiny/port/validation/NAME/`) have the recordings
and the logs of those tests.

What that run showed about the look: in the direct light of the test world the light parts
of The Chaperone and of The Huckleberry are too bright, with a glow. In the dark test cell
`QASmoke` the same materials looked correct. The materials are not corrected for this.
In the view from the right of the third-person test of The Last Word the camera cuts off
the head of the player.

## The permission

Start the game only when the user asked for a game test or permitted it. The first task of
the Destiny chat had the rule: "Do not write into a game Data folder and do not start the
game unless the user asks." When you started the game with no new request, say so in the
report.

Do not start Marathon for a check of a port: it has an anti-cheat program. Do not write into
a game folder, `plugins.txt`, the saves or the Proton prefix. Use esx as it is: do not change
its code, and do not start its graphical interface.

## The rules

1. **One session for the computer.** The probe has one session at a time, for each user and
   each agent of the computer.
2. **`esx probe status` before a start.** Start only when `session` is null and
   `fallout4_pids` is empty.
3. **`esx probe status` before a stop.** Stop only the session that you started, with the ID
   that your start command printed. Do not stop a session that you find. Wait, or ask its
   owner.
4. **After a stop, wait.** Read `esx probe status` until `fallout4_pids` is empty. Then the
   next start is possible.
5. **A label of your own, and `--session ID`.** `./port destiny game session NAME LABEL` keeps
   the session ID and its label in one file for all users
   (`data/destiny/port/work/probe_session.txt`). When the file has a session with a different
   label, the program does not stop it and has the exit code 1. `--take-over` stops that
   session: ask the user before you give it. Give `--session ID` to each other game test
   program: with no `--session`, `game all` takes the ID of the shared file.
6. **The idle camera.** About 2 minutes after the start of a session the game turns the
   camera about the player, because the session has no input. A recording must end before
   that time or start after it. An op that sets the view ends that camera.
7. **The hashes of the release.** `baselines.sha256` (in git) has the sha256 of the release
   of each mod that was tested, and `./port baseline check` compares the files of `data/` with
   it. For a test, take the sha256 of the three files of `data/mods/NAME/build/release/`
   after the build and before the first test. Compare them after the tests and after each
   later change of a file. Do the last tests on the last build. Do not write a
   `release_tested.sha` file again: the two files of the validation folders are from the
   chats.
8. **No other load.** Record with no other heavy job on the computer. A Blender validation
   at the same time gave a recording that was not usable.
9. **Look at each recording.** Make a frame sheet (`./port destiny check strip` or
   `video-sheet`) and look at it before you use the recording. Compare a recording that is
   made again with the old one: its ops, its step times and its clips.
10. **Read the trace.** A count of passed ops is not a correct clip.
11. **Compare with the vanilla weapon in the same session** when the game does a thing that
    the Blender checks do not show.
12. **The state of the computer is a part of the report**: no game process remains, nothing
    was written into the `Data` folder of the installed game, the mod is not installed.

## The session

```sh
esx probe status                                # look first
./port destiny game session NAME LABEL          # builds the mod, starts a session, prints its ID
esx probe stop --session ID                     # only the ID that the start command printed
esx probe status                                # no session, no game process
```

`./port destiny game session NAME LABEL [--cell ID | --world] [--no-build] [--take-over]` takes
the name of a mod. Its steps:

1. It reads the session file. When the file has a session with a different label, the
   program stops here with the exit code 1 and stops nothing: a second user can have started
   that session. `--take-over` goes on. When the label is the same, or with `--take-over`,
   it stops the session of the file, and no other session.
2. It builds the mod with `./port mod build NAME --update-lock`. With `--no-build` it does
   not build: it starts the session with the release that is there. Use `--no-build` to test
   the release that you tested before, with its bytes.
3. It looks at `esx probe status`. When a session is there that this program did not start,
   it does not start a session, and its exit code is 1.
4. It starts the session with `data/mods/NAME/build/release` and prints the session ID.

| Option | Meaning |
| --- | --- |
| `--cell ID` | The cell where the game starts. Default: `QASmoke`, a test cell of the game. |
| `--world` | Give no cell: the game starts in the cell of the test world of the test folder (below). An esx version with no test world stays in the main menu then. |
| `--no-build` | Do not build. |
| `--take-over` | Stop the session of the session file also when it has a different label. Ask the user first. |

The same start with no `./port`:

```sh
esx --data "/path/to/Fallout 4/Data" probe start --mod data/mods/NAME/build/release --cell QASmoke \
    --label LABEL --timeout 300 --proton "/path/to/Proton" --format json
esx probe call OP --session ID --args JSON
```

* `--mod` must be the release folder. With the project folder the game loads no plugin, and
  `item.give` answers "No form has this EditorID".
* `--proton` was necessary on the computer of the chats (Linux). Without it the start ended
  with the exit code 3: "Select an installed Proton version with --proton DIR".
* The answer of the start has the session ID in `data.session`. The start took 20 seconds in
  the chat.
* `esx probe status` has `data.session` (an object with `id` when a session is alive, else
  null) and `data.fallout4_pids`.

### The test world

This part is from the documents of esx of 2026-10-06. It needs an esx version from that date
or later.

* `esx probe install --world FILE` installs a ZIP file or a folder with one plugin into the
  test folder of the probe. The user supplies the file. It is not in esx and not in this
  repository.
* `esx probe status` shows the world in `installs[0].world`.
* With a world, `esx probe start` with no `--cell` starts in the cell of the world.
  `./port destiny game session NAME LABEL --world` does this.
* The world of the tests of 2026-10-06 was `TestWorldspace.esp` with the cell `WeapTest`:
  flat ground with a grid, a plain background color, the player looks north, and the light
  comes from behind the player. The yaws 45, 90 and 135 are correct there for pictures of a
  weapon. The game is ready about 16 seconds after the start.

The pictures of the chats are from the cell `QASmoke`. The light of that cell gives each dark
surface a green tint, and the top of the picture has a black and yellow area (the sky of
the cell).

## The commands of `./port destiny game`

`WEAPON` is the editor ID of the weapon (`TheLastWord`, `Khvostov`, `M77`). `./port destiny
game COMMAND --help` gives each option.

| Command | What it does | Result in `--out DIR` |
| --- | --- | --- |
| `session NAME LABEL` | Builds a mod, starts a session, prints its ID. | The session file. |
| `record --session ID --weapon WEAPON --capacity N [--auto] --out DIR` | The first-person test with a video. With `--auto` each group of shots is a burst (`ActionFireAuto`). | `record.mp4`, `record.log`, `steps.json` (each op with its answer and its time), `trace.json` (each clip and event of the graph). |
| `third --session ID --weapon WEAPON --capacity N [--record] --out DIR` | The third-person reload at a slow game speed, with pictures from three sides. | `SIDE_TAG.png`, `sheet_right.jpg`, `sheet_front.jpg`, `sheet_left.jpg`, `steps.json`, `trace.json`, and with `--record` `record.mp4`. |
| `reloads --session ID --weapon WEAPON --capacity N --out DIR` | One reload for each count of rounds, in the two views. | `reloads.json`: the clip, the time, the rounds and the sounds of each reload. |
| `sight --session ID --weapon WEAPON --capacity N --out DIR` | Pictures at the hip and in the sights. | `hip.png`, `sighted.png`. |
| `trace --session ID --weapon WEAPON --loaded N --view first\|third` | The clips and the events of one reload. | Text. |
| `shots --session ID --weapon WEAPON --loaded N --from T0 --to T1 --count N --out DIR` | Pictures of the gun in a slow third-person reload. | One picture for each time. |
| `all --session ID --weapon EDITORID:CAPACITY[:auto][:reloads] ... --out DIR [--mod NAME --tested FILE.sha] [--dry-run]` | Each test of each weapon of a mod in one session: `record`, `third --record`, `reloads`, `sight`, in this order. | One folder for each weapon, with `record/`, `third/`, `reloads/`, `sight/`. |
| `results --out FOLDER [--record DIR] [--third DIR] [--sight DIR] [--reloads DIR]` | Copies the results of a weapon into its validation folder and prints the numbers. | `game_test.mp4`, `game_test.log`, `game_test_steps.json`, `game_test_third_person.mp4`, `third_person_reload_game.jpg`, `red_dot_game.jpg`, `game_test_reloads.txt`. |

`./port destiny game all` does not start and does not stop a session. It uses the session
of `--session`. With no `--session` it takes the ID of the session file, which can be the
session of a second user: give `--session ID` each time. `--wait` is the age of the session in
seconds at which the first test starts (default 140). The program then sets the first-person
view, which ends the one turn of the idle camera, so a recording does not have it. With
`--mod NAME` it prints the sha256 of each release file after the tests, and with `--tested
FILE` it compares them with a file of `sha256sum` lines. The file has the three lines of the
release, with or with no folder before each name: `grep -F "mods/NAME/build/release/"
baselines.sha256` gives the lines of a release on record. `--dry-run` prints each command and
runs nothing.

The steps of `record`: the first-person view, give and equip the weapon, draw, idle, three
shots (or two bursts), reload, the sights, shots in the sights, leave the sights, gun down
and ready, the sprint events, put away, draw, a reload and a shot at one quarter of the
game speed, then the third-person view with a shot and a reload.

### The times of the chat

| What | Time |
| --- | --- |
| The start of a session | 20 seconds |
| The wait for the idle camera | 140 seconds from the start of the session |
| A first-person recording | 78 to 92 seconds |
| A third-person recording | 109 to 122 seconds |
| Nine tests in one session | About 17 minutes |

## How to read the log of a recording

`record.log` (in a validation folder: `game_test.log`) has one line for each op: the time,
the op, its arguments, `ok` or the error, and the answer. Lines of the test of the M77:

```
 1.5 s  item.give    {"form": "M77", "equip": true}       ok {"equipped": true, "form": "FE000801", "mods_attached": [], "name": "M77 Assault Rifle", ...
 2.0 s  ammo.set     {"loaded": 30, "reserve": 100}       ok {"capacity": 30, "loaded": 30, "reserve": 100, ...
 2.3 s  weapon.draw  {"drawn": true}                      ok {"drawn": true, "graphs_activated": ["M77GunBehavior.hkb"], ...
11.6 s  ammo.get                                          ok {"capacity": 30, "loaded": 14, "reserve": 100, ...
11.6 s  action.run   {"action": "ActionReload"}           ok {"accepted": true, ...
11.6 s  anim.wait    {"event": "reloadEnd"}               ok {"matched": {"kind": "event", ...
14.6 s  ammo.get                                          ok {"capacity": 30, "loaded": 30, "reserve": 84, ...
video validation/m77/game/record.mp4; 40 ops, 0 failed
```

Read these things:

* The last line: the count of ops and the count of failed ops.
* `item.give`: the game found the weapon by its editor ID, and `mods_attached` has each part
  that you gave.
* `weapon.draw`: `graphs_activated` has the graph of the mod. Its name is the prefix of the
  behavior source and the vanilla name (`TLWGunBehavior`, `KHVGunBehavior`, `M77GunBehavior`).
* `ammo.get` before and after the shots and the reload: two bursts used 16 of 30 rounds, and
  the reload filled the gun (14 to 30 rounds, 100 to 84 in reserve).
* The time in the video is the time of the log plus 2 seconds.

## How to read a trace

```sh
./port destiny game trace --session ID --weapon TheChaperone --loaded 3 --view third
```

The program gives and draws the weapon, sets the view and the rounds, starts a reload, waits
for the event `reloadEnd`, and reads the trace of the probe. It prints each start and each
end of a clip whose data has the text `Reload`, and each event after the first of them. A
line has the time from the first line in frames of 30 for each second, the kind
(`clip_start`, `clip_end`, `event`), the owner (`player_1st` or `player_3rd`), and the name
of the clip or of the event with its payload.

The trace of the probe (the op `anim.trace`, with `since` and a `limit` of 4096 at most) has
120 ticks for each second. Each entry has `kind` (`clip_start`, `clip_end`, `event`,
`graph`), `node` (the name of the clip) and `owner`.

| Question | What to read | The fault that this found |
| --- | --- | --- |
| Did the game play the clip of the mod? | The `clip_start` lines: the name of each clip, and for a counted reload the clip of that count (`WPNReload3` for 3 rounds in a gun of 6). | A second clip node that played `WPNReload` at the same time as `WPNReload1`. |
| Did the reload end at the event of the clip? | The time of `reloadEnd` against the frame of `reloadEnd` in the clip. | The third-person reload of The Chaperone ended at frame 22 of the 38 frames of its last piece. The graph sends `reloadEnd` 0.5 s before the end of a clip. |
| Did each sound play one time? | The `SoundPlay` events with their payload. | Three shell sounds in a reload with one shell. |
| Did the game remove the gun at the correct time? | The events of the put-away. | The gun went out of the hand before the hand moved: the graph removes the gun 0.233 s before the end of the clip. |
| Which clips did the test play? | Each `clip_start` of `trace.json`. | The game played 13 of the 24 clips of The Last Word, and 14 of the 27 clips of the Khvostov and of Hammerhead. The others did not play. |

`validation/the_chaperone/game_test_reloads.txt` is the result of `reloads` for The
Chaperone: one line for each reload.

```
view    rounds before  clip        seconds to reloadEnd  rounds after  shell sounds  lever sounds
first   5              WPNReload1  2.75                  6             1             2
third   0              WPNReload6  6.28                  6             6             2
```

To learn a rule of a graph: `esx behavior explain reload --like KEYWORD`,
`esx hkx events FILE --event NAME` and `esx hkx show FILE --selector 'object(N)'` on the built
graph.

## The ops and the names

| Purpose | Op and arguments |
| --- | --- |
| Give the weapon | `item.give {form, equip, mods}`. The answer has `mods_attached`. A vanilla form needs the plugin and the ID: `"Fallout4.esm:0CE97D"`. |
| Draw, put away | `weapon.draw {drawn}` |
| Ammunition | `ammo.set {loaded, reserve}`, `ammo.get`. Give the two counts. |
| An action | `action.run {action}` |
| An event of the graph | `anim.send_event {event, target: "player"}` with `rifleSightedEnd`, `GunUp`, `SprintStart`, `SprintStop` |
| Wait for the reload | `anim.wait {event: "reloadEnd"}`. A wait with `clip_end` ended with a timeout. |
| The trace | `anim.trace {since, limit}` |
| Pictures | `screenshot.take`, `screenshot.orbit` |
| The camera | `camera.set {"view": "first"}`, `camera.orbit {target, yaw, pitch, distance}` |
| The console | `console.run {command}`, for example `sgtm 0.25` for one quarter of the speed |

The action names of the probe: `ActionReload`, `ActionFire`, `ActionRightAttack`,
`ActionRightRelease`, `ActionDraw`, `ActionSheath`, `ActionMelee`, `ActionThrow`,
`ActionSighted`, `ActionSneak`, `ActionJump`, `ActionBoltCharge`, `ActionFireSingle`,
`ActionFireAuto`, `ActionFireEmpty`, `ActionGunDown`, `ActionGunReady`, `ActionIdleStop`.

The event of each action: `ActionSighted` is `rifleSightedStart`, the release of the sights
is `rifleSightedEnd`, the sprint is `SprintStart` and `SprintStop`, the gun down is `GunDown`
and `GunUp`, `ActionReload` is `reloadStart`, `ActionFireSingle` is `attackStart`.

An op with the error detail `retryable` can be sent again (the probe has one connection).

## The recording

`./port destiny game record` records the PipeWire node `gamescope` with GStreamer. The
pipeline that works:

```sh
gst-launch-1.0 -e pipewiresrc target-object=gamescope do-timestamp=true ! videoconvert ! \
    video/x-raw,format=I420 ! videorate ! video/x-raw,framerate=60/1 ! \
    x264enc speed-preset=veryfast bitrate=12000 key-int-max=60 ! matroskamux ! filesink location=FILE.mkv
```

* A node number (`path=367`) did not link. Use `target-object=gamescope`.
* NV12 into `x264enc` gave black frames. Force `format=I420`.
* `videorate` needs `do-timestamp=true`.
* Stop the recorder with SIGINT. A stop with SIGTERM leaves no end of stream.
* `record` sets `fAutoVanityModeDelay` of the game. One recording still had the idle camera
  in its first 3 seconds, so that setting does not prevent the camera in each case.

## The game test of a New Vegas mod

The mods `PPK` and `FAMAS` have test plans (`mods/NAME/tests/*.toml`). A plan is a TOML
file: a profile (the release files, the plugin, the cell `QASmoke`) and steps. Run a plan in
the project folder `data/mods/NAME`:

```sh
esx probe run tests/first-person.toml --proton "/path/to/Proton" --label ppk -o build/test-first-person
esx probe run tests/parts.toml --proton "/path/to/Proton" --label ppk -o build/test-parts
```

* The steps of the plans: `env.check`, `item.give` (with `equip = true`), `ammo.set`,
  `weapon.draw`, `weapon.get`, `anim.state`, `screenshot.take` (`hud = false`), `action.run`
  (with `wait`), `anim.wait`, `console.run`, `ammo.get`.
* A wait: `{ clip_start = "WPNReload", owner = "player_1st" }`,
  `{ event = "SoundPlay", payload = "WPNPistol10mmReloadMagOut" }`,
  `{ event = "reloadComplete" }`. Put the wait on the step that starts the action.
* For pictures at known frames: `console.run` with `sgtm 0.2`, then `sgtm 1`.
* Set the ammunition to 0 for the reload of the empty gun, and to a low count for the other
  one. The game refuses a reload when the magazine is full.
* Keep the timeouts short, so that the idle camera does not start.
* `esx probe run` has no option `--overwrite`. Use a new report folder.
* When a weapon does not draw, test the vanilla template weapon alone first.
* Look at each picture of the report. Compare it with the Blender picture of the same frame.

Results of 2026-10-05: the PPK 34 of 34 steps and 27 of 27 (the suppressor), the FAMAS 32 of
32 and 55 of 55 (the parts).

## What a passed test does not prove

* A test that passes is not a correct clip. The first test of the New Vegas chat passed 30
  of 30 with the fingers in the gun. The third-person reload of The Chaperone passed with a
  reload that ended 12 frames early.
* The tests send no move input. The walk, run and jump clips did not play in any test.
* The game played 13 of the 24 clips of The Last Word, and 14 of the 27 clips of the Khvostov
  and of Hammerhead.
* Held input: the sprint, a held aim, held automatic fire of a New Vegas plan.
* The sound was not recorded.
* Nobody played the game with a keyboard and a mouse.
* The mod was not in the installed game. The weapons workbench was not tested: the probe
  cannot read its menu, so a recipe and a slot name are not proved.
* A body in power armor was not tested.
* The look in other light than that of the test cell.

## What a recording shows that is not a fault of a clip

* The camera kicks at each shot. It is the recoil of the weapon record. The vanilla weapon
  does the same in the same session.
* A moving object leaves a row of copies behind it. Vanilla objects show it also. The agent
  thinks that it is the anti-aliasing of the game, and did not test with it off.
* The Pip-Boy is in the view, because the clips of the source bring the left forearm far
  into the view.
* The graph starts the blend from the draw clip to the idle 0.5 s before the end of the draw
  clip, so the last part of the draw plays at a decreasing weight.
* The game goes into the sights about 2.1 s after `ActionSighted`, for each weapon. The
  cause is not known.

## Faults of the game tests that have no known cause

* `ammo.set` failed with "The engine did not keep the requested counts" in three events. In
  the first one the op had no reserve count. In the last one, each of three first-person
  tests in one session had one failed op: the reserve stayed at 197, 194 and 98, and the
  tests wanted 100, 100 and 90. The program for the sight pictures had run before and had
  set a reserve of 200. After these tests the same op kept the counts 10 times of 10. The
  agent started a new session, ran the first-person tests before the sight pictures, got 0
  failed ops, and used only these results.
* One build gave a plugin with other bytes: the first build after a change of a behavior
  source, with the same count of records and the same two archives. Each build after that
  gave the same bytes. A change of a comment in an item file gives the same release hashes.
* A build with another esx version can give other bytes than a release that was tested
  before. The rule is: compare the hashes (`./port baseline check`). One comparison was made,
  on 2026-10-06: esx at the commit `d3e520c` built each of the 7 mods from nothing (a copy of
  `data/mods/NAME` with no `build/` folder, in a scratch folder), and each of the 3 release
  files of each mod had the bytes of `baselines.sha256`. So a build from nothing gives the
  tested release, and esx `d3e520c` gives the bytes of the older esx (`a996de8`) that made the
  stored releases. No other version was compared.
* The vanilla Deliverer does not draw in the test game, also with no mod.
* A game window for the user (`esx probe start --display inherit`) failed on the display of
  the desktop. A gamescope window worked for 2 minutes and then closed.

## Two agents and one probe

On 2026-10-06 two threads worked in one folder at the same time: the Tex Mechanica mod and
the M77. The two used one session file through the program that is now
`./port destiny game session`.

1. 21:57:21 (UTC): the program of the M77 thread stopped the session of the file, which was
   the session of the other thread (the tests of that thread were complete). It then started
   the session of the M77.
2. 21:58:33: a stop command of the other thread read the ID from the file and stopped the
   session of the M77 thread, 56 seconds after its start. The first game test of the M77
   failed.
3. The other thread found this in the records of the probe sessions, and sent a message
   with the times, the session ID, the cause and the state at that time. It told the user
   under the words "My error".
4. The M77 thread started a new session with a session file of its own, and ran the test
   again.

The program now stops with the exit code 1 for a session file with a different label, and it
does not start when the probe has a session that it did not start. `--take-over` stops the
session of the file with a different label. The session file is still one file for all
users. So two agents that use the command at the same time must have different labels, must
give `--session ID` to each game test program, must run `esx probe status` before each start
and each stop, and must ask the user before `--take-over`.

A test that ran when a second agent stopped the session is not a result. Run it again
before you look for a fault in the mod.

## What is not proved

* The game test programs in this repository: see "The state of the game test programs".
* The part "The test world" is from the documents of esx and from the one run of "The state
  of the game test programs".
* The ops, the action names and the recording pipeline are those of the chats, with esx
  0.1.0 (commit `a996de8`). A later version of esx can have other names.
* The test plans of the two New Vegas mods were not run in this repository.
* Each point of "What a passed test does not prove".
