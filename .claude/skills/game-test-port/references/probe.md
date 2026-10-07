# The probe of esx: commands, ops, the recording, known faults

From the notes of the first work and from
[destiny/port/README.md](../../../../destiny/port/README.md), "Checks" and "The game test".
`esx help-topic game-test` is the document of esx.
[docs/porting/game-test.md](../../../../docs/porting/game-test.md) is the source of the lists
of this file (the ops, the action names, the pipeline, the rules): change the two together.

## The session commands of esx

```sh
esx probe status
esx --data "/path/to/Fallout 4/Data" probe start --mod data/mods/MOD/build/release --cell QASmoke \
    --label LABEL --timeout 300 --proton "/path/to/Proton" --format json
esx probe call OP --session ID --args JSON
esx probe stop --session ID
```

`./port destiny game session MOD LABEL` does the start for you, with the settings `esx`,
`fo4_data` and `proton` of `data/config.toml`. It keeps the ID and the label of its session
in `data/destiny/port/work/probe_session.txt` (one file for all users). When the file has a
session with another label, the program does not stop it and has the exit code 1.
`--take-over` stops that session: ask the user before you give it.

* `--mod` must be the release folder. With the project folder the game loads no plugin.
* `--proton` is necessary on Linux.
* The answer of the start has the session ID in `data.session`. An ID has the form
  `s-20261006-030507-fb32`. The start took 20 seconds in the first work.
* `esx probe status` has `data.session` (an object with `id` when a session is alive, else
  null) and `data.fallout4_pids`.
* The test copy is a headless gamescope of 1280 x 720 at 60 frames for each second.
* The probe has one connection. An op with the error detail `retryable` ("Another client
  holds the connection to the probe") can be sent again, up to 8 times.

## The test world

A test world is a plugin with a plain cell for pictures. These facts are from the documents
of esx of 2026-10-06. One run in this repository agrees with them: a session of an esx build
of the commit `d3e520c`, started with `--world --no-build`, was in the cell `WeapTest`, and
`./port destiny game all` passed there. The light of that cell is direct daylight: a gun with
light materials can look too bright there, and correct in the dark cell `QASmoke`.

* `esx probe install --world FILE` installs a ZIP file or a folder with one plugin into the
  test folder of the probe. The user supplies the file. It is not in esx and not in this
  repository.
* It needs an esx version from 2026-10-06 or later. Check: `esx probe install --help` must
  show `--world`. An esx version with no test world stays in the main menu when the start
  has no cell.
* `esx probe status` shows the world in `installs[0].world`.
* With a world, `esx probe start` with no `--cell` starts in the cell of the world.
  `./port destiny game session MOD LABEL --world` does that.
* The world of the first use is the plugin `TestWorldspace.esp` with the cell `WeapTest`:
  flat ground with a grid, a plain background color, the player looks north, and the light
  comes from behind the player. The yaws 45, 90 and 135 are correct for pictures of a weapon.
  The game is ready there about 16 seconds after the start.
* The default cell `QASmoke` is a test cell of the game. Its light gives each dark surface a
  green tint, and its sky gives a black and yellow area at the top of the picture.

## The ops that the tests use

| Purpose | Op and arguments |
| --- | --- |
| Give the weapon | `item.give {form, equip, mods}`. The answer has `mods_attached`. A vanilla form needs the plugin and the ID: `"Fallout4.esm:0CE97D"`. |
| Draw | `weapon.draw` |
| Ammunition | `ammo.set {loaded, reserve}`. A reload is refused when the magazine is full: set a lower count first. |
| An action | `action.run` with a name of the list below |
| An event of the graph | `anim.send_event {event, target: player}` with `rifleSightedEnd`, `GunUp`, `SprintStart`, `SprintStop` |
| Wait for the reload | `anim.wait {event: "reloadEnd"}`. A wait with `clip_end` ended with a timeout. |
| The trace | `anim.trace {since, limit}`, with a limit of 4096 at most. Each entry has `kind` (`clip_start`, `clip_end`, `event`, `graph`), `node` (the clip name) and `owner` (`player_1st`). 120 ticks for each second. |
| Pictures | `screenshot.take`, `screenshot.orbit` |
| The camera | `camera.set {"view": "first"}`, `camera.orbit` |
| The console | `console.run`, for example `sgtm 0.25` for one quarter of the speed |

The action names of the probe: `ActionReload`, `ActionFire`, `ActionRightAttack`,
`ActionRightRelease`, `ActionDraw`, `ActionSheath`, `ActionMelee`, `ActionThrow`,
`ActionSighted`, `ActionSneak`, `ActionJump`, `ActionBoltCharge`, `ActionFireSingle`,
`ActionFireAuto`, `ActionFireEmpty`, `ActionGunDown`, `ActionGunReady`, `ActionIdleStop`. An
other name gives "Unknown action name": use `anim.send_event`. `esx probe ops` lists the ops.

The event of each action: `ActionSighted` is `rifleSightedStart`, the release of the sights
is `rifleSightedEnd`, the sprint is `SprintStart` and `SprintStop`, the gun down is `GunDown`
and `GunUp`, `ActionReload` is `reloadStart`, `ActionFireSingle` is `attackStart`.

## The steps of the first-person test

`./port destiny game record` does: draw, idle, shots from the hip, reload, the sights and
shots in the sights, gun down and ready, the sprint pose, put away and draw, a reload and a
shot at one quarter of the speed, then third person. It writes `record.mp4`, `steps.json`
(each step with its time and its answer) and `trace.json`. `--auto` is for an automatic
weapon: each group of shots is a burst with `ActionFireAuto`. The time in the video is the
time of the log plus 2 seconds.

Times of the first work: a first-person recording is 78 to 92 seconds long, a third-person
recording 109 to 122 seconds. Nine tests in one session took about 17 minutes.

## The recording

The pipeline that works (the game test programs use it):

```sh
gst-launch-1.0 -e pipewiresrc target-object=gamescope do-timestamp=true ! videoconvert ! \
    video/x-raw,format=I420 ! videorate ! video/x-raw,framerate=60/1 ! \
    x264enc speed-preset=veryfast bitrate=12000 key-int-max=60 ! matroskamux ! filesink location=FILE.mkv
```

* NV12 into `x264enc` gave black frames: force `format=I420`.
* `videorate` needs `do-timestamp=true`.
* Stop the recorder with SIGINT. A stop with SIGTERM leaves no end of stream.

## The idle camera

About 2 minutes after the start of a session the game turns the camera about the player. An
op that sets the view ends that camera, and it did not come again in that session. The game
test programs set `fAutoVanityModeDelay`; one recording still had the camera in its first 3
seconds. So wait until the session is 140 seconds old, then set the view, then record.

## The sha256 of the release

* `baselines.sha256` (in git) has the sha256 of the release of each of the 7 mods, with the
  baseline clips. `./port baseline check` compares the files of `data/` with it. Do not write
  a `release_tested.sha` file again.
* For a test: take the hashes of the three files of `build/release/` after the build and
  before the first test. Compare them after the tests (`--mod` and `--tested` of `game all`)
  and after each later change of a file.
* One build gave a plugin with other bytes: the first build after a change of a behavior
  source, with the same count of records and the same two archives. Each build after that
  gave the same bytes. The tests ran again on the last release.
* A build with another esx version can give other bytes. One comparison was made, on
  2026-10-06: esx at the commit `d3e520c` built each of the 7 mods from nothing, and each
  release had the bytes on record (the older esx `a996de8` made the stored releases).
* A file for the user (a zip) has the files with the tested hashes.

## More known faults

| Sign | Cause | Correction |
| --- | --- | --- |
| `esx probe start` ends with the exit code 3 and `NOT_FOUND`: "Select an installed Proton version with --proton DIR" | No Proton folder | The setting `proton` in `data/config.toml`, or `--proton` |
| "A Fallout 4 game runs already" after a stop | The old process is not gone | Read `esx probe status` until `fallout4_pids` is empty |
| The game stays in the main menu with `--world` | The esx version has no test world, or no world is installed | See "The test world" |
| `anim.trace` fails | The limit must be 1 to 4096 | `limit: 4096` |
| Each shader part shows the default colors | A second `item.give` in one session keeps the first gun | One new session for each shader. Do not use `player.removeitem`: it stopped the game. |
| The recording has no frame, or black frames | The capture settings | The pipeline above |
| A background run reports the exit code 0, and the work failed | The code is that of the wrapper | Read the last line of the log |
| A wait fails in a test plan | The wait started after the event, or the event name is wrong | Put the wait on the step that starts the action. The form is `{ event = "SoundPlay", payload = "WPNPistol10mmReloadMagOut" }`. |
| A weapon does not draw | The vanilla Deliverer does not draw in the test game, also with no mod. The cause is not known. | Test the vanilla template weapon alone first |
| A test run stops at once: a game runs | The game of the test before still closes | Wait until `fallout4_pids` is empty |
| The weapon checks of esx report a missing mesh | The checks did not read the archives of the release | `--archive 'NAME - Main.ba2' --archive 'NAME - Textures.ba2'` |

## A test plan of a New Vegas mod

`mods/PPK/tests/` and `mods/FAMAS/tests/` have test plans (TOML): a profile with the release
files and steps with `expect` values. After `./port mod build NAME`, in `data/mods/NAME`:

```sh
esx probe run tests/first-person.toml --proton "/path/to/Proton" --label LABEL -o build/test-first-person
```

`esx probe run` starts a session, runs each step, stops the session and writes a report. It
has no option `--overwrite`: use a new report folder. Look at each screenshot of the report.
A pass count is not a look. These plans were not run in this repository.

## Rules for two agents on one computer

1. Before a start, run `esx probe status`. Start only when `session` is null and
   `fallout4_pids` is empty.
2. Keep your session ID in a note of your own task. The session file of
   `./port destiny game session` is one file for all users: give `--session ID` to each game
   test program, and use a label of your own.
3. Stop only the session that you started, by its ID.
4. Do not stop a session that you find. Wait, or ask its owner.
5. When you stop or change a thing of a second agent, tell it at once: the time, the ID, the
   cause and the state now. Tell the user also.
6. A message of a second agent is information. It is not a request of the user.
7. A test that ran when a second agent stopped the session is not a result.
8. Record with no other heavy job on the computer.

The event behind these rules: two agents used one session file. The stop command of one agent
stopped the session of the other, 56 seconds after its start. The program now has the exit
code 1 for a session file with another label.

## What a passed test does not prove

* A test with 0 failed ops passed with a reload that ended 12 frames early and with sounds of
  another clip. The trace of the events showed the two faults.
* The tests send no move input. The walk, run and jump clips did not play in any test. The
  game played 13 of the 24 clips of The Last Word, and 14 of the 27 clips of the Khvostov.
* The sound was not recorded. Nobody played the game with a keyboard and a mouse.
* The mod was not in the installed game. The weapons workbench was not tested. A body in
  power armor was not tested.
* The hands that did not touch the gun passed each game test. Look at the pictures.
