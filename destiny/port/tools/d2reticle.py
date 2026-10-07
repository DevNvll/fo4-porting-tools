#!/usr/bin/env python3
"""The glass of the sight of a Destiny 2 weapon and its reticle: the meshes, the textures and the materials.

    ./port destiny reticle ITEM -o data/destiny/port/extract/NAME/sight.json
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python \
        destiny/port/tools/d2reticle.py ...          (the same program with no ./port)

ITEM is the name or the hash of a weapon. The program reads the game packages with the modules
of destiny/extract/d2x (it does not change them), so it runs with the Python environment of
d2x. The extraction of the gun has only the parts
of the render stage `opaque`. A sight has more parts, in two other stages:

    transparent (7)   the glass of the sight, with its graphics. Each part is on a weapon bone.
    reticle (16)      one quad at the origin, with the texture of the reticle. Its vertex
                      shader puts it on the aim axis with a matrix that the game calculates,
                      so the file does not say where the player sees it.

The output has each such part of each art entity of the weapon: the positions (meters, the
space of the model, as the game stores them), the normals, the texture coordinates, the
triangles, the bone and the material. For each bone of a glass part it also has the positions
of each opaque part on that bone (`reference`): tools/d2model.py finds the same vertices in
the parts file and so gets the transform from the space of the model to the Fallout 4 bone.

A material is a pixel shader with its values. The file has, for each material: the values of
the constant buffer cb0 as the tag stores them, the constants and the bytes of the expression
program that calculates more values of cb0 when the game runs, and the textures. The shader
files are in the folder `sight` beside the output (NAME_ps.dxbc, NAME_vs.dxbc):
tools/dxasm.py prints their instructions. The textures of a material are in the folder
`textures` (TAG.png). A glass part also uses the texture plates of its entity
(`plate_set`): SET_albedo.png and SET_gstack.png, which the extraction of the gun made.
"""
import argparse
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

from d2x import pkg, investment, entity as ent, model as mdl, texture as tex
from d2x.tag import Reader

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from d2dyes import find_item  # noqa: E402

TRANSPARENT, RETICLE = 7, 16
# (name, offset of the shader, offset of the texture list) of the two shaders of a material
SHADERS = (('vs', 0x48, 0x50), ('ps', 0x2C8, 0x2D0))


def table(data, offset, size):
    """(count, start) of a table of the tag: the count at `offset`, and the place of its first item."""
    count, relative = struct.unpack_from('<QQ', data, offset)
    return (count, offset + 8 + relative + 16) if count else (0, 0)


def vectors(data, offset):
    count, start = table(data, offset, 16)
    rows = np.frombuffer(data, dtype='<f4', count=count * 4, offset=start).reshape(count, 4) if count else np.zeros((0, 4))
    return [[float(x) for x in row] for row in rows]


def read_material(pm, tag, folder, name):
    """The values of one material. It saves the two shaders and the textures."""
    data = pm.read(tag)
    r = Reader(data)
    out = {'tag': '%08X' % tag}
    for label, shader, textures in SHADERS:
        header = r.u32(shader)
        if pm.exists(header) and pm.exists(pm.reference(header)):
            os.makedirs(os.path.join(folder, 'sight'), exist_ok=True)
            file = os.path.join('sight', '%s_%s.dxbc' % (name, label))
            with open(os.path.join(folder, file), 'wb') as f:
                f.write(pm.read(pm.reference(header)))
            out[label + '_shader'] = file
        count, start = table(data, textures + 0x18, 1)
        out[label + '_program'] = data[start:start + count].hex(' ')
        out[label + '_constants'] = vectors(data, textures + 0x28)
        out[label + '_cb0'] = vectors(data, textures + 0x48)
        out[label + '_textures'] = []
        for slot, texture in ((r.u32(o), r.u32(o + 4)) for o in r.array_items(textures, 8)):
            entry = {'slot': slot, 'tag': '%08X' % texture}
            if pm.exists(texture):
                pixels, info = tex.read_pixels(pm, texture)
                entry.update(file=os.path.join('textures', '%08X.png' % texture), width=info.width, height=info.height, srgb=bool(info.srgb))
                os.makedirs(os.path.join(folder, 'textures'), exist_ok=True)
                Image.fromarray(pixels).save(os.path.join(folder, entry['file']))
            out[label + '_textures'].append(entry)
    return out


def shape(part, bones):
    joints = sorted(set(part.joints[:, 0].tolist()))
    if len(joints) != 1:
        raise SystemExit('a part of the sight is on %d bones: the program knows only a part on one bone' % len(joints))
    return {'part': int(part.part_index), 'mesh': int(part.mesh_index), 'stage': mdl.STAGE_NAMES.get(part.stage, str(part.stage)),
            'material': '%08X' % part.material, 'bone': bones[joints[0]] if joints[0] < len(bones) else str(joints[0]),
            'positions': np.round(part.positions.astype(float), 6).tolist(),
            'normals': np.round(part.normals.astype(float), 5).tolist() if part.normals is not None else None,
            'uvs': np.round(part.uvs.astype(float), 6).tolist() if part.uvs is not None else None,
            'triangles': part.triangles.astype(int).tolist()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('item')
    ap.add_argument('-o', '--output', required=True)
    ap.add_argument('--manifest', help='the manifest of the extraction (default: manifest.json beside the output): it has the bone names')
    a = ap.parse_args()
    folder = os.path.dirname(os.path.abspath(a.output))
    bones = json.load(open(a.manifest or os.path.join(folder, 'manifest.json')))['weapon_skeleton']['bones']
    pm = pkg.PackageManager()
    inv = investment.Investment(pm)
    item = find_item(inv, a.item)
    models = []
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
            name = 'region%02d_%08X' % (region, entity_tag) if region >= 0 else '%08X' % entity_tag
            models.append((name, model_tag, variants, tex.find_plate_set(pm, resource.data)))
    out = {'item': item.name, 'item_hash': int(item.item_hash), 'units': 'meters, the space of the model (+X to the muzzle, +Z up)',
           'sights': [], 'materials': {}, 'reference': []}
    used_bones = set()
    for name, model_tag, variants, plate_set in models:
        # the highest detail of each part: the two stages have the levels 1 and 8 of a part
        parts = mdl.read_model(pm, model_tag, stages=(TRANSPARENT, RETICLE), high_detail_only=False, variants=variants)
        best = min((p.lod for p in parts), default=None)
        parts = [p for p in parts if p.lod == best]
        if not parts:
            continue
        sight = {'source': name, 'model': '%08X' % model_tag, 'plate_set': '%08X' % plate_set if plate_set else None, 'shapes': []}
        for p in parts:
            s = shape(p, bones)
            sight['shapes'].append(s)
            if s['stage'] == 'transparent':
                used_bones.add(s['bone'])
            if s['material'] not in out['materials']:
                out['materials'][s['material']] = read_material(pm, p.material, folder, s['material'])
        out['sights'].append(sight)
        print('[reticle] %s: %s' % (name, ', '.join('%s part %d (%d vertices, material %s, %s)' % (
            s['stage'], s['part'], len(s['positions']), s['material'], s['bone']) for s in sight['shapes'])))
    if not out['sights']:
        raise SystemExit('the weapon %s has no part in the stages transparent and reticle' % item.name)
    # the opaque parts on the bones of the glass, in the order of the extraction of the gun
    for name, model_tag, variants, _ in models:
        for index, p in enumerate(mdl.read_model(pm, model_tag, stages=(0,), variants=variants)):
            for joint in sorted(set(p.joints[:, 0].tolist())):
                bone = bones[joint] if joint < len(bones) else str(joint)
                if bone in used_bones:
                    keep = p.joints[:, 0] == joint
                    out['reference'].append({'source': name, 'part': index, 'bone': bone,
                                             'positions': np.round(p.positions[keep].astype(float), 6).tolist()})
    with open(a.output, 'w') as f:
        json.dump(out, f)
    print('[reticle] %s: %d sight entities, %d materials, %d reference parts (%d vertices)' % (
        a.output, len(out['sights']), len(out['materials']), len(out['reference']), sum(len(x['positions']) for x in out['reference'])))


if __name__ == '__main__':
    main()
