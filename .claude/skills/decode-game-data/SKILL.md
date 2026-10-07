---
name: decode-game-data
description: Gives the method to find a table, a layout or a shader rule in the packages of Destiny 2 or Marathon (the Tiger engine) that the extraction tools d2x and m2x do not read yet, with the analysis commands "./port destiny tag", "./port destiny notes", "./port destiny shader-text" and "./port marathon notes". Use when a port needs data that the extraction does not have (dyes, a sight glass, third-person clips, the colors of a Marathon material, the name of a state or of a bone that is only a hash), when m2x stops with "no tag of the class" and "the layouts of this file are for another build", after an update of a game, or when a value in an extraction has no sense.
---

# Find a table or a layout in the game packages

Three features of the ports were missing because their data was in a place that the
extraction did not read: the dyes, the glass and the reticle of a sight, and the
third-person clips. This is the method that found them, and that made the tools work for
Marathon, where no public tool has the class numbers.

## When to use it, and when not

* Use it for research in the game data, and for a new build of a game.
* To extract a weapon with the tools as they are: `extract-game-weapon`.
* The result of this work is a change of a tool: follow `change-shared-tool` for the edit.

## Before the start

`./port doctor` is ok for the area. Do not start the game. The tools only read the game
folder. The analysis programs write below `data/` only. `./port marathon notes` and
`./port destiny notes` list each program with its arguments, and each one has `--help`.

## The commands

| Command | What it gives |
| --- | --- |
| `./port destiny tag HASH ...` | The raw data of package entries, into `data/destiny/extract/out/raw` |
| `./port destiny notes weapon-tags MANIFEST.json` | The weapon tags that the pattern entity of a weapon lists |
| `./port destiny notes graph-tags MANIFEST.json` | The weapon tag tree and the leaves of the main states of each first-person rig |
| `./port destiny notes third-graph-dump OUT.json`, `third-clip-index OUT.npy` | Each state and leaf of the third-person graph of the player body; a table of each clip tag |
| `./port destiny notes dye-slots`, `dye-values`, `dye-dump`, `dyes-explore` | The dye data of an item |
| `./port destiny shader-text FILE.dxbc` | The instructions of a Direct3D 11 shader |
| `./port marathon notes class-graph [SAMPLES]` | For each tag class: the count, the sizes, the package groups, the classes that its entries name |
| `./port marathon notes scan-text TEXT` | Each package entry that has a text (it needs many minutes) |
| `./port marathon notes paths PREFIX` | The development paths in the tags of the packages with a name prefix |
| `./port marathon notes find-value VALUE [--all] [--pkg PREFIX]` | The tags that have a 32-bit value (a tag, a name hash) |
| `./port marathon notes describe TAG`, `walk ENTITY [--depth N]` | The texts and the tags that a tag names; the tree of entities below an entity |
| `./port marathon notes dxil MATERIAL [--vs] [-o FILE.ll]` | The pixel shader of a material as LLVM text (it needs `llvm-dis`) |
| `./port marathon tag64` | The table of the 64-bit tag hashes again, after an update of the game |

## Steps

### 1. Prove the reader before you look for a layout

`./port marathon setup` opens the packages and reads 50 entries. That proves the package
reader and the Oodle library. For a new game, read some thousand random entries.

### 2. Read how a public tool names the structure

For Destiny 2, Charm has the layouts of the entity, model, material, texture and string
structures. It is a reference, not a dependency, and its build can be another one: its dye
has 21 vectors, and this build has 27. For Marathon no public tool has the classes.

### 3. Go from a known name to its table

1. Search for a text that is long. `M77` has 3 characters and gave random matches in binary
   data. `Omnipositor` and `ar_m77` did not.
2. Make the hash of the name, and find the tags that have it (`find-value`).
3. Describe each tag, and walk the entity.

Names are FNV-1 hashes of 32 bits (start `0x811C9DC5`, prime `0x01000193`, multiply, then
exclusive or). To find the word of a hash, hash a list of candidate words. That gave
`reload_1` (`EB22859A`), `reload_enter`, `chamber_1`, the bone names and the slot names.

### 4. Read a table by its class

* Find a table by its class, and take the largest tag of the class. Never use a fixed tag.
* An array field is a count and a relative pointer. The pointer leads to a header of 16
  bytes (the count, then the class at +8), and the rows are after the header. One analysis
  read the class at +12 and got row counts with no sense.
* A relative pointer is a 64-bit value at an offset: the target is the offset plus the value.

### 5. Prove the layout

Gate: the layout gives a value that the file has a second time, and the two agree: the
bounds of a model against its vertices (0.00001 m at most), the largest index against the
vertex count, the frame count of a clip against its header.

Gate: the layout works for a second weapon of a different type, and for a third. A layout
from one weapon can be wrong for a second: the weapon tag rule of the first extraction was
proved on a hand cannon only, and it gave no idle, draw or reload for a rifle.

### 6. Read a shader for the rule of a material

For Destiny 2: `./port destiny shader-text` on the files that `./port destiny reticle` writes.
For Marathon: `./port marathon notes dxil`. In its output, `dx.op.sample` reads a texture,
`dx.op.cbufferLoadLegacy` reads a vector of the constants, and `dx.op.storeOutput` writes a
render target (0 the color, 1 the normal with the smoothness, 2 the metal value and the
occlusion). Compare the constants of two materials of the same shader, and look at each
channel of each texture. A value that the game calculates when it runs is not in the files:
that is a limit, and the input state that you select is a choice.

### 7. Put the result into the tools

Write the layout into the docstring of the module and into the README of the area. Put an
analysis program into the `notes/` folder of the area, with a command in its `port.toml` and
a help text. A new word goes into `STATE_WORDS` (`destiny/extract/d2x/graph.py`) or
`WEAPON_BONE_WORDS` (`d2x/names.py`). A new bone name changes the bone names in the files of
that weapon, so the set files that name the bone change also: run the regressions
(`change-shared-tool`).

## Stop and ask the user

* When the weapon or the data needs another build of the game.
* Before a download of a tool or of a file that the task did not name.
* Before a change of `d2x` that changes the files of an earlier extraction.

## Common faults

| Sign | Cause | What to do |
| --- | --- | --- |
| Thousands of matches of a text search | A short text | A longer text |
| Row counts with no sense | A wrong offset in the header of an array | Step 4 |
| The animation decoder stops: "-1 is not a valid Space_Type" | Its layouts are for another build | `m2x.patch_parser()` has three corrections for this build. One process must not read a rig of Marathon and a rig of Destiny 2. |
| `llvm-dis` refuses a shader of Marathon | The data layout text of DXIL | `./port marathon notes dxil` changes the text for the reader. The file of the game is not changed. |
| A chain of shell commands stopped one step | `grep ... &&` with no match | Run each step alone, and read its exit code |
| A statement in a document that the data does not have | Written from memory | Check each number against the manifest before the report |

## What to report

* Each class with its layout, and the proof of step 5. The weapons that you tested.
* Each name that you found, and each hash that still has no word.
* Each reading. A reading is not a fact of a file: "the meaning of the 27 dye vectors is my
  reading of the values".

## More

* [destiny/extract/README.md](../../../destiny/extract/README.md), "How it works".
* [marathon/extract/README.md](../../../marathon/extract/README.md), "The layouts that the
  tools read" and "What was necessary".
* [docs/reference/glossary.md](../../../docs/reference/glossary.md).
