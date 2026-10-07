"""Entity tags and their resources (pre-Beyond Light class hashes, from Charm)."""
from dataclasses import dataclass, field

import numpy as np

from .tag import Reader

ENTITY = 0x80809C0F
ENTITY_RESOURCE = 0x80809C36
# (class at Unk10, class at Unk18) of the entity resources this tool reads.
SKELETON = (0x80808545, 0x80808546)
MODEL = (0x808072B8, 0x808072BD)
ANIMATION = (0x80803466, 0x8080344B)
ANIMATION_SET = 0x808036F6
ANIMATION_CLIP = 0x80808F49


@dataclass
class Resource:
    tag: int
    kind: tuple
    definition: int      # offset of the Unk18 structure in the resource tag
    data: bytes

    @property
    def reader(self):
        return Reader(self.data)


@dataclass
class Skeleton:
    tag: int
    hashes: list         # bone name hash (FNV-1) per node
    parents: list
    rotations: np.ndarray        # (n, 4) xyzw, object space
    translations: np.ndarray     # (n, 3) object space
    scales: np.ndarray           # (n,)
    inverse_rotations: np.ndarray
    inverse_translations: np.ndarray

    def __len__(self):
        return len(self.hashes)


@dataclass
class Entity:
    tag: int
    resources: list = field(default_factory=list)

    def by_kind(self, kind):
        return [r for r in self.resources if r.kind == kind]

    def first(self, kind):
        found = self.by_kind(kind)
        return found[0] if found else None


def read_entity(pm, tag):
    r = Reader(pm.read(tag))
    entity = Entity(tag)
    for offset in r.array_items(0x10, 0xC):
        resource_tag = r.u32(offset)
        if not pm.exists(resource_tag) or pm.reference(resource_tag) != ENTITY_RESOURCE:
            continue
        data = pm.read(resource_tag)
        rr = Reader(data)
        p10, p18 = rr.rel(0x10), rr.rel(0x18)
        kind = (rr.u32(p10 - 4) if p10 >= 4 else 0, rr.u32(p18 - 4) if p18 >= 4 else 0)
        entity.resources.append(Resource(resource_tag, kind, p18, data))
    return entity


def read_skeleton(resource):
    r, base = resource.reader, resource.definition
    count, start, _ = r.array(base + 0x80)
    nodes = np.frombuffer(resource.data, dtype='<i4', count=count * 4, offset=start).reshape(count, 4)
    hashes = [int(v) & 0xFFFFFFFF for v in nodes[:, 0]]
    parents = nodes[:, 1].tolist()
    _, forward, _ = r.array(base + 0x90)
    _, inverse, _ = r.array(base + 0xA0)
    fwd = np.frombuffer(resource.data, dtype='<f4', count=count * 8, offset=forward).reshape(count, 8)
    inv = np.frombuffer(resource.data, dtype='<f4', count=count * 8, offset=inverse).reshape(count, 8)
    return Skeleton(resource.tag, hashes, parents,
                    fwd[:, 0:4].copy(), fwd[:, 4:7].copy(), fwd[:, 7].copy(),
                    inv[:, 0:4].copy(), inv[:, 4:7].copy())


def animation_sets(pm, resource):
    """Animation set tags that an animation resource points at."""
    words = np.frombuffer(resource.data[:len(resource.data) & ~3], dtype='<u4')
    found = []
    for value in words.tolist():
        if 0x80800000 < value <= 0x81FFFFFF and pm.exists(value) and pm.reference(value) == ANIMATION_SET:
            if value not in found:
                found.append(value)
    return found


def animation_set_clips(pm, set_tag):
    """Clip tags of one animation set, in set order."""
    r = Reader(pm.read(set_tag))
    count, start, _ = r.array(0x08)
    return [r.u32(start + i * 4) for i in range(count)]
