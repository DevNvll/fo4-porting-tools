#!/usr/bin/env python3
"""The dyes of a Destiny 2 weapon (its "shader"): the values of each dye, its detail textures, and the dye slot of each mesh part.

    ./port destiny dyes ITEM [--shader NAME] -o data/destiny/port/extract/NAME/dyes.json
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python \
        destiny/port/tools/d2dyes.py ...          (the same program with no ./port)

ITEM is the name or the hash of a weapon. The program reads the game packages with the modules
of destiny/extract/d2x (it does not change them), so it runs with the Python environment of
d2x. With --shader NAME (a shader item of the
game, for example "New Age Black Armory") the dyes of that shader are in place of the default
dyes of the weapon, as when the player applies the shader. `--list TEXT` prints the shader
items whose name has TEXT.

How the game stores the dyes (build 2020-08, found by analysis; the class hashes of the public
tool Charm are those of later builds):

  item definition -> translation block (+0x88): three lists of (channel index, dye index):
      custom dyes (+0x28): what a shader item gives; default dyes (+0x38); locked dyes (+0x48)
  channel index -> table of the class 80805BDE -> channel hash (Weapon1, Weapon2, Weapon3)
  dye index -> table of the class 80805DE8 (rows: art dye hash, dye manifest hash)
      -> global tag assignments (80809780) -> wrapper (8080744A) -> 808071CD -> dye tag (808071F3)
  dye tag: +0x08 name, +0x40 list of (texture slot, texture), +0x88 list of 27 vectors

The meaning of each vector (VECTORS below) is my reading of the values of many dyes with the
names of the public shader templates of Charm and of sbox_destiny_2_gear_shader: those
sources have the order of a later build, which has 21 vectors. A metal dye has 1 in the last
value of its material vector, and a tint is a color: the reading fits each dye that I looked at.

A weapon has three dyes, and each dye has a primary and a secondary material: six slots. Each
mesh part has its slot (the byte at +0x1A of the part): 0 and 1 are the primary and the
secondary of the dye of Weapon1, 2 and 3 of Weapon2, 4 and 5 of Weapon3.
"""
import argparse
import json
import os
import struct
import sys

import numpy as np

from d2x import pkg, investment, entity as ent, model as mdl, texture as tex
from d2x.tag import Reader

CHANNELS = 0x80805BDE
ART_DYES = 0x80805DE8
CHANNEL_NAMES = {1667433279: 'Weapon1', 1667433278: 'Weapon2', 1667433277: 'Weapon3',
                 662199250: 'ArmorPlate', 1367384683: 'ArmorSuit', 218592586: 'ArmorCloth'}
WEAPON = ('Weapon1', 'Weapon2', 'Weapon3')
VECTORS = {0: 'detail_diffuse_transform', 1: 'detail_normal_transform', 2: 'spec_aa_transform',
           9: 'primary_albedo_tint', 10: 'primary_material_params', 11: 'primary_material_advanced_params', 12: 'primary_roughness_remap',
           13: 'secondary_albedo_tint', 14: 'secondary_material_params', 15: 'secondary_material_advanced_params', 16: 'secondary_roughness_remap',
           17: 'primary_worn_albedo_tint', 18: 'primary_wear_remap', 19: 'primary_worn_roughness_remap', 20: 'primary_worn_material_params',
           21: 'secondary_worn_albedo_tint', 22: 'secondary_wear_remap', 23: 'secondary_worn_roughness_remap', 24: 'secondary_worn_material_params'}


class Dyes:
    def __init__(self, pm, inv):
        self.pm, self.inv = pm, inv
        r = Reader(pm.read(inv._largest(CHANNELS)))
        count, start, _ = r.array(0x08)
        self.channels = [CHANNEL_NAMES.get(r.u32(start + i * 4), '%d' % r.u32(start + i * 4)) for i in range(count)]
        data = pm.read(inv._largest(ART_DYES))
        r = Reader(data)
        count, start, _ = r.array(0x08)
        self.art = np.frombuffer(data, dtype='<u4', count=count * 2, offset=start).reshape(count, 2)

    def lists(self, item):
        """The dye lists of an item: {'custom': {channel: dye index}, 'default': ..., 'locked': ...}."""
        r = Reader(self.pm.read(item.definition, cache=False))
        block = r.rel(0x88)
        out = {}
        for label, offset in (('custom', 0x28), ('default', 0x38), ('locked', 0x48)):
            out[label] = {self.channels[r.i16(o)]: r.i16(o + 2) for o in r.array_items(block + offset, 4)} if block else {}
        return out

    def tag(self, index):
        tag = self.inv._assignments.get(int(self.art[index, 1]), 0)
        for _ in range(4):
            if not tag or not self.pm.exists(tag):
                return 0
            data = self.pm.read(tag)
            if len(data) > 64:
                return tag
            words = struct.unpack_from('<%dI' % (len(data) // 4), data)
            following = [w for w in words if 0x80800000 < w <= 0x81FFFFFF and self.pm.exists(w) and w != tag]
            tag = following[0] if following else 0
        return 0

    def read(self, index):
        tag = self.tag(index)
        if not tag:
            raise SystemExit('the dye %d has no tag' % index)
        data = self.pm.read(tag)
        r = Reader(data)
        at = r.rel(0x08)
        name = data[at:data.index(b'\0', at)].decode('ascii', 'replace') if at else ''
        count, start, _ = r.array(0x88)
        vectors = np.frombuffer(data, dtype='<f4', count=count * 4, offset=start).reshape(count, 4)
        textures = [(r.u32(o), r.u32(o + 4)) for o in r.array_items(0x40, 8)]
        dye = {'dye_index': int(index), 'tag': '%08X' % tag, 'name': name, 'vectors': [[float(x) for x in v] for v in vectors],
               'textures': [{'slot': s, 'tag': '%08X' % t} for s, t in textures]}
        for i, key in VECTORS.items():
            if i < count:
                dye[key] = [float(x) for x in vectors[i]]
        return dye


def part_slots(pm, inv, item):
    """{mesh name: [dye slot of each exported part]}: the parts in the order of the primitives of the extraction."""
    out = {}
    for arrangement in item.art_arrangement_indices:
        for region, entity_tag in inv.art_entities(arrangement):
            entity = ent.read_entity(pm, entity_tag)
            resource = entity.first(ent.MODEL)
            if resource is None:
                continue
            model_tag = resource.reader.u32(resource.definition + 0x1DC)
            if not pm.exists(model_tag) or pm.reference(model_tag) != mdl.MODEL:
                continue
            variants = mdl.external_materials(resource.data, resource.definition)
            parts = mdl.read_model(pm, model_tag, stages=(0,), variants=variants)
            name = 'region%02d_%08X' % (region, entity_tag) if region >= 0 else '%08X' % entity_tag
            out[name] = [int(p.dye_index) for p in parts]
    return out


def find_item(inv, text):
    if text.isdigit():
        return inv.item(int(text))
    hashes = inv.find(text)
    exact = [h for h in hashes if inv.display_name(h).lower() == text.lower()]
    if not (exact or hashes):
        raise SystemExit('no item has the name %s' % text)
    return inv.item((exact or hashes)[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('item', nargs='?')
    ap.add_argument('--shader', help='a shader item: its dyes are in place of the default dyes of the weapon')
    ap.add_argument('--list', help='print the shader items whose name has this text')
    ap.add_argument('-o', '--output')
    a = ap.parse_args()
    pm = pkg.PackageManager()
    inv = investment.Investment(pm)
    dyes = Dyes(pm, inv)
    if a.list is not None:
        for h in inv.find(a.list):
            try:
                lists = dyes.lists(inv.item(h))
            except Exception:
                continue
            if all(c in lists['custom'] for c in WEAPON):
                print('%12d  %s' % (h, inv.display_name(h)))
        return
    item = find_item(inv, a.item)
    lists = dyes.lists(item)
    chosen, source = {}, {}
    for channel in WEAPON:
        for label in ('default', 'locked'):
            if channel in lists[label]:
                chosen[channel], source[channel] = lists[label][channel], label + ' dye of the weapon'
    shader = None
    if a.shader:
        shader = find_item(inv, a.shader)
        custom = dyes.lists(shader)['custom']
        for channel in WEAPON:
            if channel in custom and channel not in lists['locked']:
                chosen[channel], source[channel] = custom[channel], 'dye of the shader %s' % shader.name
    out = {'item': item.name, 'item_hash': int(item.item_hash), 'shader': shader.name if shader else None,
           'shader_hash': int(shader.item_hash) if shader else None, 'lists': lists, 'dyes': [], 'part_slots': part_slots(pm, inv, item)}
    folder = os.path.join(os.path.dirname(os.path.abspath(a.output)), 'textures') if a.output else None
    for channel in WEAPON:
        if channel not in chosen:
            out['dyes'].append(None)
            continue
        dye = dyes.read(chosen[channel])
        dye['channel'], dye['source'] = channel, source[channel]
        # the two textures of a dye: the detail diffuse (the lower slot) and the detail normal
        for texture, kind in zip(sorted(dye['textures'], key=lambda t: t['slot']), ('detail_diffuse', 'detail_normal')):
            tag = int(texture['tag'], 16)
            if folder and pm.exists(tag):
                pixels, info = tex.read_pixels(pm, tag)
                os.makedirs(folder, exist_ok=True)
                path = os.path.join(folder, 'dye_%s.png' % texture['tag'])
                tex.save_png(pixels, path)
                dye[kind] = {'file': os.path.relpath(path, os.path.dirname(os.path.abspath(a.output))), 'srgb': bool(info.srgb),
                             'size': [int(info.width), int(info.height)]}
        out['dyes'].append(dye)
    if a.output:
        with open(a.output, 'w') as f:
            json.dump(out, f, indent=1)
    print('%s (item %d)%s' % (item.name, item.item_hash, ', shader %s' % shader.name if shader else ''))
    for dye in out['dyes']:
        if dye is None:
            continue
        print('  %s: dye %d "%s" (%s)' % (dye['channel'], dye['dye_index'], dye['name'], dye['source']))
        for side in ('primary', 'secondary'):
            m = dye[side + '_material_params']
            print('     %-9s tint %s metal %.2f | worn tint %s metal %.2f | detail blends %s' % (
                side, np.round(dye[side + '_albedo_tint'][:3], 3).tolist(), m[3],
                np.round(dye[side + '_worn_albedo_tint'][:3], 3).tolist(), dye[side + '_worn_material_params'][3], np.round(m[:3], 2).tolist()))
    print('  dye slot of each part:', out['part_slots'])


if __name__ == '__main__':
    main()
