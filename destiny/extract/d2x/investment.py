"""Investment (item database) lookups for Destiny 2 pre-Beyond Light ("d2_sk").

Chain for a weapon:
  item name -> display definition -> item hash -> item definition
  item definition -> translation block -> weapon pattern index + art arrangement index
  weapon pattern -> pattern global tag id -> pattern entity (rig, animations, audio)
  art arrangement -> entity assignment hashes -> art entities (render geometry)

All tables are found by class hash, never by fixed tag hash, so the same code
works for other pre-Beyond Light builds.
"""
from dataclasses import dataclass, field

import numpy as np

from . import strings
from .tag import Reader

ITEM_MAP = 0x80807BE4            # item hash -> item definition tag
ITEM_DEFINITION = 0x80807BEA
DISPLAY_MAP = 0x80805CDB         # item hash -> display definition tag
DISPLAY_DEFINITION = 0x80805CE1
STRING_CONTAINER_INDEX = 0x80805F98
SANDBOX_PATTERNS = 0x80805B78
GLOBAL_TAG_ASSIGNMENTS = 0x80809780   # hash -> tag (sorted list)
ART_ARRANGEMENTS = 0x80805DF5    # art arrangement index -> entity assignment hashes
ENTITY_ASSIGNMENTS = 0x808056EA  # entity assignment hash -> entity wrapper tag
ENTITY = 0x80809C0F
ENTITY_WRAPPER = 0x8080744A      # 24-byte tag with the entity hash at 0x10
INVALID_HASH = 0x811C9DC5


@dataclass
class WeaponPattern:
    index: int
    pattern_hash: int
    global_tag_id: int
    content_group: int
    weapon_type: int
    entity: int = 0


@dataclass
class Item:
    item_hash: int
    definition: int
    display: int = 0
    name: str = ''
    pattern_index: int = -1
    art_arrangement_indices: list = field(default_factory=list)
    dyes: list = field(default_factory=list)


class Investment:
    def __init__(self, pm):
        self.pm = pm
        self._item_map = self._hash_map(self._largest(ITEM_MAP))
        self._display_map = self._hash_map(self._largest(DISPLAY_MAP))
        self._containers = self._read_container_index()
        self._container_cache = {}
        self._assignments = self._read_pairs(GLOBAL_TAG_ASSIGNMENTS)
        self._entity_assignments = self._read_pairs(ENTITY_ASSIGNMENTS)
        self._patterns = self._read_patterns()
        self._arrangements = self.pm.read(self._largest(ART_ARRANGEMENTS))
        self._names = None

    # -- table discovery -------------------------------------------------
    def _largest(self, class_hash):
        entries = self.pm.entries
        rows = entries[(entries['reference'] == class_hash) & (entries['type'] == 8)]
        if len(rows) == 0:
            raise LookupError(f'No tag of class {class_hash:08X}. Is this a pre-Beyond Light build?')
        return int(rows['tag'][np.argmax(rows['size'])])

    def _hash_map(self, tag):
        """Tables of 0x18-byte rows: hash at 0x00, tag at 0x10."""
        data = self.pm.read(tag)
        r = Reader(data)
        count, start, _ = r.array(0x08)
        rows = np.frombuffer(data, dtype='<u4', count=count * 6, offset=start).reshape(count, 6)
        return {int(h): int(t) for h, t in zip(rows[:, 0], rows[:, 4])}

    def _read_container_index(self):
        data = self.pm.read(self._largest(STRING_CONTAINER_INDEX))
        r = Reader(data)
        count, start, _ = r.array(0x08)
        rows = np.frombuffer(data, dtype='<u4', count=count * 2, offset=start).reshape(count, 2)
        return rows[:, 1].tolist()

    def _read_pairs(self, class_hash):
        """Tables of 8-byte rows: hash, tag."""
        data = self.pm.read(self._largest(class_hash))
        r = Reader(data)
        count, start, _ = r.array(0x08)
        rows = np.frombuffer(data, dtype='<u4', count=count * 2, offset=start).reshape(count, 2)
        return {int(h): int(t) for h, t in rows}

    def _read_patterns(self):
        data = self.pm.read(self._largest(SANDBOX_PATTERNS))
        r = Reader(data)
        count, start, _ = r.array(0x08)
        patterns = []
        for i in range(count):
            o = start + i * 0x30
            pattern = WeaponPattern(i, r.u32(o), r.u32(o + 4), r.u32(o + 0x10), r.u32(o + 0x14))
            pattern.entity = self.resolve_entity(pattern.global_tag_id)
            patterns.append(pattern)
        return patterns

    # -- lookups ---------------------------------------------------------
    def resolve_entity(self, assignment_hash, table=None):
        """Entity tag for a global tag id / entity assignment hash (0 if none)."""
        tag = (self._assignments if table is None else table).get(assignment_hash, 0)
        if not tag or not self.pm.exists(tag):
            return 0
        reference = self.pm.reference(tag)
        if reference == ENTITY:
            return tag
        if reference == ENTITY_WRAPPER:
            inner = Reader(self.pm.read(tag)).u32(0x10)
            if self.pm.exists(inner) and self.pm.reference(inner) == ENTITY:
                return inner
        return 0

    def string(self, container_index, key):
        if container_index >= len(self._containers):
            return ''
        if container_index not in self._container_cache:
            tag = self._containers[container_index]
            table = strings.read_container(self.pm, tag) if self.pm.exists(tag) else {}
            self._container_cache[container_index] = table
        return self._container_cache[container_index].get(key, '')

    def display_name(self, item_hash):
        tag = self._display_map.get(item_hash)
        if not tag:
            return ''
        r = Reader(self.pm.read(tag, cache=False))
        return self.string(r.u32(0x84), r.u32(0x88))

    def names(self):
        """Dict of item hash -> English name for every item with a name."""
        if self._names is None:
            self._names = {}
            for item_hash in self._display_map:
                name = self.display_name(item_hash)
                if name:
                    self._names[item_hash] = name
        return self._names

    def find(self, text):
        """Item hashes whose name contains `text` (case-insensitive)."""
        text = text.lower()
        return sorted(h for h, name in self.names().items() if text in name.lower())

    def item(self, item_hash):
        definition = self._item_map.get(item_hash)
        if not definition:
            raise KeyError(f'Item {item_hash} is not in this game build')
        item = Item(item_hash, definition, self._display_map.get(item_hash, 0), self.display_name(item_hash))
        r = Reader(self.pm.read(definition, cache=False))
        block = r.rel(0x88)   # translation block
        if block:
            for offset in r.array_items(block, 4):
                item.art_arrangement_indices.append(r.i16(offset + 2))
            for offset in r.array_items(block + 0x48, 4):
                item.dyes.append((r.i16(offset), r.i16(offset + 2)))
            item.pattern_index = r.i16(block + 0x58)
        return item

    def art_entities(self, arrangement_index):
        """Render entities of one art arrangement: list of (region index, entity tag)."""
        r = Reader(self._arrangements)
        count, start, _ = r.array(0x08)
        if not 0 <= arrangement_index < count:
            return []
        row = start + arrangement_index * 0x20
        found = []
        for single in (r.u32(row + 0x8), r.u32(row + 0xC)):
            entity = self.resolve_entity(single, self._entity_assignments) if single != INVALID_HASH else 0
            if entity and (-1, entity) not in found:
                found.append((-1, entity))
        for pointer in r.array_items(row + 0x10, 8):
            group = r.rel(pointer)
            region = r.u32(group)
            for assignment in r.array_items(group + 8, 8):
                entity = self.resolve_entity(r.u32(assignment), self._entity_assignments)
                if entity:
                    found.append((region, entity))
        return found

    def pattern(self, index):
        return self._patterns[index] if 0 <= index < len(self._patterns) else None

    @property
    def patterns(self):
        return self._patterns
