"""Print the dye slot data of each mesh part of an item of this game build. Read-only.

    ./port destiny notes dye-slots ITEM_HASH ...

The program imports d2x (destiny/extract). With no ./port, run destiny/port/notes/dye_slots.py
with the Python of the d2x environment (data/destiny/extract/venv/bin/python) and with
PYTHONPATH=destiny/extract.
"""
import sys
import struct
if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip())
    raise SystemExit(0 if len(sys.argv) > 1 else 2)

import numpy as np
from d2x import pkg, investment, entity as ent, model as mdl
from d2x.tag import Reader

pm = pkg.PackageManager()
inv = investment.Investment(pm)


def parts_with_slots(model_tag, variants=()):
    """(mesh index, part index, material, dye_index, flags, uvs, normal w per vertex, triangles) for each visible part."""
    data = pm.read(model_tag)
    r = Reader(data)
    out = []
    for mesh_index, mesh in enumerate(r.array_items(0x10, 0x88)):
        vertex0, vertex1, weights_tag, _, index_tag = (r.u32(mesh + i * 4) for i in range(5))
        if not pm.exists(vertex0) or not pm.exists(index_tag):
            continue
        buffer0, stride0 = mdl._read_buffer(pm, vertex0)
        buffer1, stride1 = mdl._read_buffer(pm, vertex1) if pm.exists(vertex1) else (b'', 0)
        indices = mdl._read_indices(pm, index_tag)
        restart = 0xFFFFFFFF if indices.dtype.itemsize == 4 else 0xFFFF
        stage_offsets = struct.unpack_from('<25h', data, mesh + 0x28)
        part_offsets = r.array_items(mesh + 0x18, 0x20)
        n = len(buffer0) // stride0
        raw0 = np.frombuffer(buffer0, dtype=np.uint8, count=n * stride0).reshape(n, stride0)
        raw1 = np.frombuffer(buffer1, dtype=np.uint8, count=n * stride1).reshape(n, stride1) if stride1 else None
        for stage in mdl.VISIBLE_STAGES:
            for part_index in range(stage_offsets[stage], stage_offsets[stage + 1]):
                if part_index >= len(part_offsets):
                    continue
                po = part_offsets[part_index]
                material = r.u32(po)
                variant = r.i16(po + 4)
                if 0 <= variant < len(variants):
                    material = variants[variant]
                lod = r.u8(po + 0x1B)
                if lod not in mdl.HIGH_DETAIL_LODS or not pm.exists(material):
                    continue
                primitive = r.i16(po + 6)
                index_offset, index_count = r.u32(po + 8), r.u32(po + 0xC)
                chunk = indices[index_offset:index_offset + index_count]
                tris = mdl._strip_runs(chunk, restart) if primitive == 5 else chunk[:len(chunk) // 3 * 3].astype(np.uint32).reshape(-1, 3)
                if len(tris) == 0:
                    continue
                vs, _ = mdl.material_shaders(pm, material)
                if vs is None:
                    continue
                layouts = mdl._layout(mdl.shader_input_signature(vs), stride0, stride1)
                used = np.unique(tris)
                w = None
                for raw, layout in ((raw0, layouts[0]), (raw1, layouts[1])):
                    if raw is None:
                        continue
                    for name, index, width, offset, byte_wide in layout:
                        if name == 'NORMAL' and index == 0 and offset + width <= raw.shape[1] and not byte_wide and width >= 8:
                            w = np.ascontiguousarray(raw[used, offset:offset + width]).view('<i2')[:, 3]
                out.append({'mesh': mesh_index, 'part': part_index, 'stage': stage, 'material': material, 'dye_index': r.u8(po + 0x1A),
                            'flags': r.u32(po + 0x18), 'vertices': len(used), 'normal_w': w})
    return out


for text in sys.argv[1:]:
    item = inv.item(int(text))
    print('======== %s' % item.name)
    for arrangement in item.art_arrangement_indices:
        for region, entity_tag in inv.art_entities(arrangement):
            e = ent.read_entity(pm, entity_tag)
            resource = e.first(ent.MODEL)
            if resource is None:
                continue
            model_tag = resource.reader.u32(resource.definition + 0x1DC)
            if not pm.exists(model_tag) or pm.reference(model_tag) != mdl.MODEL:
                continue
            variants = mdl.external_materials(resource.data, resource.definition)
            print('region %s entity %08X model %08X' % (region, entity_tag, model_tag))
            for p in parts_with_slots(model_tag, variants):
                w = p['normal_w']
                slots = dict(zip(*np.unique(w & 7, return_counts=True))) if w is not None else None
                wvals = dict(list(zip(*np.unique(w, return_counts=True)))[:8]) if w is not None else None
                print('   mesh %d part %2d stage %d material %08X dye_index %3d flags %08X vertices %5d | normal w & 7: %s | normal w: %s' % (
                    p['mesh'], p['part'], p['stage'], p['material'], p['dye_index'], p['flags'], p['vertices'],
                    {int(k): int(v) for k, v in slots.items()} if slots else None, {int(k): int(v) for k, v in wvals.items()} if wvals else None))
