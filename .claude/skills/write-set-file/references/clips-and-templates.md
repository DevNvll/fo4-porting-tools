# The clip of each state, the templates and the events

## The Fallout 4 clip of each state of Destiny 2 or Marathon

`states.json` has the clip of each state of the animation graph for the tags of the weapon.
The names of the states are the same words in the two games.
[docs/porting/destiny.md](../../../../docs/porting/destiny.md) has the same table with fewer
notes: change the two together.

| State | Fallout 4 clip | Notes |
| --- | --- | --- |
| `idle`, the first clip | `WPNIdleReady` | 96 to 99 frames, a loop. |
| `idle`, the second and the third clip | `WPNIdleReadyA` to `D` | The state has three clips with the thresholds 0.962, 0.981 and 1.0. The game plays the four Fallout 4 clips now and then in place of the idle. With no second clip, use the idle. |
| `iron_sight_idle` | `WPNIdleSighted`, `WPNIdleSightedWobble` | The graph blends `WPNIdleSightedWobble` into the sighted idle. It must be the sighted idle of the weapon: the reader cannot read the vanilla clip. |
| `fire` | `WPNFireSingleReady`, `A`, `B`; with `[auto]` `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack` | The M77 has three clips in this state (thresholds 0.333, 0.667, 1.0): one for each name. |
| `iron_sight_fire` | `WPNFireSingleSighted`; with `[auto]` `WPNFireAutoSighted` | |
| `ready` | `WPNEquip`, `WPNEquipFast` | 22 to 33 frames. |
| `put_away` | `WPNUnEquip`, with `[hold_end]` | 4 or 5 frames in Destiny, 12 in the M77. |
| `reload_empty`, `reload_full`, `reload_special` | `WPNReload` | 127 frames (The Last Word), 105 (the Khvostov), 180 (Hammerhead), 91 (The Huckleberry), 104 (the M77, the value `empty`). |
| `reload_enter`, `6C41757C`, `chamber_1` | `WPNReload1` to `WPNReloadN`, `WPNReload` | The three states of a shotgun (`port-staged-reload`). |
| `sprint_loop` | `WPNSprint` | When the clip is one pose: `[synth]` with `pose = "sprint"`. |
| `sprint_enter`, `sprint_exit` | No clip | The Fallout 4 graph blends from the idle to the sprint loop and back. |
| No state | `[synth]`: `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNJumpImpactLand`. `[static]`: `WPNIdleGunDown`. | The weapon motion of the vanilla clip on the hold pose, or on the pose in the sights. |
| The melee | No clip | The game uses the vanilla clip, with the hands of the vanilla gun. |

Facts about the states:

* A state with no known word has only its hash. The names are FNV-1 hashes of words:
  `reload_1` is `EB22859A`, `reload_enter` is `12CFA0E5`, `chamber_1` is `FACB2E5D`,
  `sprint_ready` is `DB28BEA1`. The state `6C41757C` (one shell) has no known name.
* A state can have no clip for a weapon. The Khvostov has no clip of the first-person rig
  for its shot: the shot clips are in `[synth]`, and the bolt moves as in the vanilla clip
  (`synth_bones` of the template: 3.67 units).
* A state can have no part motion. The shot of The Chaperone at the hip has no motion of
  the lever in the file. No rule corrects that. Write it as a limit.
* The clip in the sights of Destiny is the clip of each gun of the class. Destiny aligns the
  sight when the game runs. So each weapon needs `[sight]`.
* The clip counts of the six ports: 24 (The Last Word), 27 (the Khvostov, Hammerhead, The
  Huckleberry, the M77), 30 (The Chaperone).

## The templates

A template is a vanilla weapon as a file in `destiny/port/templates/`. It gives the weapon
bones with their rest places, the sound names of the events, the pose of the body bones, the
grip point, and the clips whose weapon motion a set can take.

| Template | Vanilla weapon | Vanilla record | Behavior keyword | Use it for |
| --- | --- | --- | --- | --- |
| `revolver44` | The .44 revolver (`Animations/44Pistol`) | `44` | `Anims44` | A hand cannon. `WeaponMagazine` is the crane, and `WeaponExtra1` is the hammer. |
| `combatrifle` | The combat rifle, with the clips of the combat shotgun (`Animations/CombatShotgun`) | `CombatRifle` or `CombatShotgun` | `AnimsCombatShotgun` | A long gun: a rifle, a shotgun, a submachine gun. 11 weapon bones. The reload events have the sound name `WPNShotgunCombat`. |
| `combatrifle_parts` | `combatrifle` with `WeaponExtra2` and `WeaponExtra3` | the same | the same | A gun with many moving parts. 13 weapon bones, all that the skeleton has. Hammerhead uses 12. |

The vanilla clips of each template are game files in `data/destiny/port/rig/`.
`./port destiny make-rig` makes them.

## When no template fits

A bolt action, a bow, a sword, or a gun that needs another vanilla graph has no template. Stop
and tell the user that this needs a new template file, and that it can need new code for the
reload events. Then:

1. Find the vanilla weapon whose graph and third-person clips fit, and print its values:
   `esx item new weapon RECORD --standalone --all-parts -o FILE` and
   `esx record show Fallout4.esm RECORD`.
2. Write `destiny/port/templates/NAME.toml` from the nearest template (`base = "combatrifle"`
   takes each value of that template). Give it `game_clips`, and the third-person keys
   `third_game_clips`, `third_clips` and `third_ready`.
3. `./port destiny make-rig` puts the vanilla clips of each template into the rig folder.
4. `./port destiny measure-template data/destiny/port/rig/NAME CLIP ...` prints the values
   for the file from the vanilla clips: the rest place of each weapon bone, the bones that
   each clip moves, and the grip point.
5. A template is a shared file: follow `change-shared-tool`, and run `./port destiny regress`.

The Chaperone is a shotgun with a lever, and it uses `combatrifle`: its lever is the kind
`bolt` (`[roles] b_pump = "bolt"`). So look at the motion of the parts before you ask for a
new template. For a New Vegas mod, the templates are those of `fnv/templates/`:
[docs/porting/fnv.md](../../../../docs/porting/fnv.md), "A new template weapon".

What is not proved: the combat rifle template took 6 minutes in the first work. No template
was added in this repository after its tools moved here.

## The events

* `weaponFire` is at frame 0 of each shot clip. An automatic clip has one for each shot.
* The sound of a draw is `SoundPlay.{sound}EquipUp` (and `EquipUpFast`) at frame 0, from
  `[events]`.
* A reload gets its events from the motion of the parts. A template with the kind `magazine`:
  `ReloadMagOut` and `ReloadMagIn` from the magazine, `reloadComplete` 2 frames after the
  magazine is in, `ReloadBoltOpen` and `ReloadBoltClose` from the bolt. The revolver gets the
  events of the crane, the rounds and the hammer.
* `reloadComplete` fills the gun. `reloadEnd` ends the reload state. `initiateStart` is one
  frame before `reloadEnd`.
* A clip of `[compose]` takes its events from `[piece_events]` and `[events]` only.
* Three cases in which the tools gave a wrong frame, each corrected with `[events]`:
  * Hammerhead: `reloadComplete` at frame 105, 2 frames after the cover is closed. When the
    box is in, the belt is not in the gun.
  * The Huckleberry: the sound `MagIn` at frame 31. The magazine turns again after it is in,
    and the tools found the end of that motion (frame 61).
  * The M77: the sound `BoltOpen` at frame 76, the pull of the hand. The bolt is to the rear
    from frame 0 (an empty gun), so the tools put the event at frame 0.

## Units and axes

The file has +Y up, +Z forward and +X to the left of the player, in meters, at 30 frames for
each second. Fallout 4 has +Z up, +Y forward and +X to the right, in game units. The scale is
the true scale: 1 m is 69.99125 units. A point of a set file (`point`, `muzzle`, `eye`) is in
Fallout 4 weapon space.
