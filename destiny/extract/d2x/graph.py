"""Animation graph of an animation resource (class 80803465, pre-Beyond Light).

The graph maps state names (hashes) to clips of the animation set. A state is
either a plain clip list or a decision tree. The tree tests several
"dimensions" in turn. Dimension 3 is the weapon tag hierarchy (class
80808EE1); the other dimensions are player conditions with hashed names.

Layout (found by analysis of the game data):
  0x08  array of (state name hash u32, state index u32), sorted by hash
  0x18  array of (kind u64, relative pointer) per state
        kind 1 -> struct: array of (clip index u32, weight f32)
        kind 2 -> struct: 0x00 array of leaf entries, each an array of (clip index, weight)
                          0x10 array of dimension ids (u8)
                          0x20 array of nodes (0x1C bytes): 16-byte tag mask, value hash u32,
                               child i16, next sibling i16, link i16
                               link < 0: leaf entry (-link - 1); link > 0: group (link - 1)
                          0x30 array of groups: (dimension id u16, first node u16); group 0 is the root
"""
from dataclasses import dataclass, field

import numpy as np

from .tag import Reader, fnv1

GRAPH = 0x80803465
TAG_TREE = 0x80808EE1
WEAPON_DIMENSION = 3

# The game stores FNV-1 hashes of these names. The names were found with a word
# list against the hashes in the game data. Add a name here when you find one.
STATE_WORDS = (
    'ready', 'put_away', 'reload_empty', 'reload_full', 'reload_special', 'fire', 'fire_1',
    'iron_sight_idle', 'iron_sight_fire', 'iron_sight_jump', 'sprint_enter', 'sprint_loop', 'sprint_exit',
    'sprint_loop_airborne', 'throw_grenade', 'weapon_down', 'crouch_slide', 'jump',
    'idle', 'cast_blink', 'double_jump', 'land_soft', 'land_hard', 'iron_sight_double_jump',
    'iron_sight_land_soft', 'iron_sight_land_hard', 'sprint_loop_jump_airborne',
)
TAG_WORDS = (
    'rifle', 'pistol', 'revolver', 'sidearm', 'sidearm_auto', 'sidearm_charged', 'sniper_rifle', 'shotgun',
    'machine_gun', 'fusion_rifle', 'launcher', 'grenade_launcher', 'grenade_launcher_2', 'grenade_launcher_3',
    'rocket_launcher', 'rocket_launcher_02', 'smg', 'bow', 'bow_heavy', 'sword', 'scoped',
    'hand_cannon', 'the_last_word', 'thorn', 'sunshot', 'thunderlord', 'coldheart', 'hard_light', 'cerberus',
    'ghost', 'shield', 'arc_blade', 'fire_relic', 'loaded_equip_sniper',
)
# Values of the player-condition dimensions. These names are NOT from the game:
# they describe which clips the value selects (the sprint loop, for example).
CONDITION_LABELS = {
    (0x0A, 0xA4C2F6BD): '', (0x0A, 0x2B059A81): 'alt', (0x0A, 0xACE6F0CE): 'sprint',
    (0x0C, 0x81808481): '', (0x0C, 0xDC094287): 'sprint',
}


@dataclass
class Choice:
    conditions: tuple        # ((dimension id, value hash), ...) for the non-weapon dimensions
    weapon_tag: int          # weapon tag that selected this leaf (0 for a plain clip list)
    clips: list              # [(clip index, weight), ...]


@dataclass
class State:
    index: int
    names: list              # name hashes that select this state
    kind: int
    choices: list = field(default_factory=list)


def read_tag_tree(data):
    """Weapon tag hierarchy: list of (tag hash, parent index); index 0 is the top."""
    r = Reader(data)
    _, element, _ = r.array(0x08)
    count, start, _ = r.array(element)
    return [(r.u32(start + i * 8), r.u16(start + i * 8 + 4)) for i in range(count)]


def weapon_tags(rows, content_group):
    """Tags that select clips for a weapon, most specific first.

    Example for The Last Word: the_last_word, revolver, pistol, rifle.
      - the content group and the tags above it (the_last_word, pistol)
      - the first child of its class: the base type of the class (pistol -> revolver).
        The weapon component of The Last Word lists both pistol/revolver and pistol/the_last_word.
      - the first top-level tag (rifle): the default of all guns
    """
    index = {tag: i for i, (tag, _) in enumerate(rows)}
    chain = []
    i = index.get(content_group, -1)
    while 0 < i < len(rows) and rows[i][0] not in chain:
        chain.append(rows[i][0])
        i = rows[i][1]
    if not chain:
        return [rows[1][0]] if len(rows) > 1 else []
    top = index[chain[-1]]
    base = next((tag for tag, parent in rows if parent == top and tag != rows[top][0]), None)
    ordered = chain[:-1]
    if base is not None and base not in ordered:
        ordered.append(base)
    ordered.append(chain[-1])
    default = next((tag for i, (tag, parent) in enumerate(rows) if i > 0 and parent == 0), None)
    if default is not None and default not in ordered:
        ordered.append(default)
    return ordered


def read_set_entries(set_data):
    """Entry table of an animation set: list of (animation name hash, seconds, clip index).

    Graph clip numbers are indexes into this table, not into the clip list.
    """
    r = Reader(set_data)
    return [(r.u32(o + 16), r.f32(o + 20), r.u16(o + 24)) for o in r.array_items(0x68, 32)]


def _clip_list(r, offset):
    return [(r.u32(o), round(r.f32(o + 4), 3)) for o in r.array_items(offset, 8)]


def read_graph(data, weapon_tags):
    """All states of a graph, resolved for one weapon.

    `weapon_tags` is the tag list of the weapon (most specific first), from `weapon_tags`.
    """
    r = Reader(data)
    name_count, names_at, _ = r.array(0x08)
    state_count, states_at, _ = r.array(0x18)
    names = {}
    for i in range(name_count):
        names.setdefault(r.u32(names_at + i * 8 + 4), []).append(r.u32(names_at + i * 8))
    rank = {tag: position for position, tag in enumerate(weapon_tags)}
    states = []
    for index in range(state_count):
        kind = r.u64(states_at + index * 16)
        base = r.rel(states_at + index * 16 + 8)
        state = State(index, names.get(index, []), kind)
        states.append(state)
        if kind == 1:
            state.choices.append(Choice((), 0, _clip_list(r, base)))
            continue
        entries = [_clip_list(r, o) for o in r.array_items(base, 16)]
        node_count, nodes_at, _ = r.array(base + 0x20)
        group_count, groups_at, _ = r.array(base + 0x30)
        groups = [(r.u16(groups_at + i * 4), r.u16(groups_at + i * 4 + 2)) for i in range(group_count)]

        def node(i):
            o = nodes_at + i * 0x1C
            return r.u32(o + 16), r.i16(o + 20), r.i16(o + 22), r.i16(o + 24)

        def weapon_leaf(first):
            """Most specific weapon tag below `first` that the weapon has: (tag, leaf entry)."""
            best = None
            stack = [first]
            while stack:
                i = stack.pop()
                if not 0 <= i < node_count:
                    continue
                tag, child, sibling, link = node(i)
                if sibling >= 0:
                    stack.append(sibling)
                if tag in rank:
                    if link < 0 and (best is None or rank[tag] < rank[best[0]]):
                        best = (tag, -link - 1)
                    if child >= 0:
                        stack.append(child)
            return best

        def walk(group, conditions):
            if not 0 <= group < len(groups):
                return
            dimension, first = groups[group]
            if dimension == WEAPON_DIMENSION:
                found = weapon_leaf(first)
                if found and found[1] < len(entries):
                    state.choices.append(Choice(conditions, found[0], entries[found[1]]))
                return
            i = first
            seen = set()
            while 0 <= i < node_count and i not in seen:
                seen.add(i)
                value, child, sibling, link = node(i)
                here = conditions + ((dimension, value),)
                if link > 0:
                    walk(link - 1, here)
                elif link < 0 and -link - 1 < len(entries):
                    state.choices.append(Choice(here, 0, entries[-link - 1]))
                i = sibling

        walk(0, ())
    return states


def find_tag_tree(pm, resource_data):
    """Tag tree tag referenced by an animation resource (0 if none)."""
    words = np.frombuffer(resource_data[:len(resource_data) & ~3], dtype='<u4')
    for value in words.tolist():
        if 0x80800000 < value <= 0x81FFFFFF and pm.exists(value) and pm.reference(value) == TAG_TREE:
            return value
    return 0


def find_graph(pm, resource_data):
    words = np.frombuffer(resource_data[:len(resource_data) & ~3], dtype='<u4')
    for value in words.tolist():
        if 0x80800000 < value <= 0x81FFFFFF and pm.exists(value) and pm.reference(value) == GRAPH:
            return value
    return 0


STATE_NAMES = {fnv1(word): word for word in STATE_WORDS}
TAG_NAMES = {fnv1(word): word for word in TAG_WORDS}


def state_name(state):
    """Readable name of a state: the game name if it is known, else `state_<hash>`."""
    known = sorted(STATE_NAMES[h] for h in state.names if h in STATE_NAMES)
    if known:
        prefix = known[0]
        for other in known[1:]:   # reload_empty / reload_full / reload_special -> reload
            while not other.startswith(prefix):
                prefix = prefix[:-1]
        prefix = prefix.rstrip('_')
        return prefix if len(prefix) >= 4 else known[0]
    return f'state_{min(state.names):08X}' if state.names else f'state_{state.index}'


def condition_label(conditions):
    parts = []
    for dimension, value in conditions:
        label = CONDITION_LABELS.get((dimension, value), f'{dimension:x}_{value:08X}')
        if label and label not in parts:
            parts.append(label)
    return '_'.join(parts)


def resolve(pm, animation_resource_data, set_tag, content_group):
    """States of an animation resource for one weapon, with clip indexes of the set.

    Returns a list of dicts: name, hashes, and choices (condition, weapon tag, clips as
    (clip index in the set, weight)).
    """
    graph_tag = find_graph(pm, animation_resource_data)
    tree_tag = find_tag_tree(pm, animation_resource_data)
    if not graph_tag or not tree_tag:
        return []
    tags = weapon_tags(read_tag_tree(pm.read(tree_tag)), content_group)
    entries = read_set_entries(pm.read(set_tag))
    resolved = []
    for state in read_graph(pm.read(graph_tag), tags):
        choices = []
        for choice in state.choices:
            clips = [(entries[i][2], weight) for i, weight in choice.clips if i < len(entries)]
            if clips:
                choices.append({'condition': condition_label(choice.conditions),
                                'condition_hashes': [f'{d:X}:{v:08X}' for d, v in choice.conditions],
                                'weapon_tag': TAG_NAMES.get(choice.weapon_tag, f'{choice.weapon_tag:08X}')
                                if choice.weapon_tag else '',
                                'clips': clips})
        if choices:
            resolved.append({'name': state_name(state), 'hashes': [f'{h:08X}' for h in state.names],
                             'game_names': sorted(STATE_NAMES[h] for h in state.names if h in STATE_NAMES),
                             'choices': choices})
    return resolved
