"""Entity model geometry (pre-Beyond Light layout, from Charm).

Vertex layouts are not stored with the buffers. As in the game (and Charm),
the layout comes from the input signature of the material's vertex shader.
"""
import struct
from dataclasses import dataclass, field

import numpy as np

from .tag import Reader

MODEL = 0x808073A5
MATERIAL = 0x808071E8

# Render stages (index into the 24 stage part offsets of a mesh).
STAGE_NAMES = {
    0: 'opaque', 1: 'decals', 2: 'investment_decals', 3: 'shadow', 6: 'decals_additive',
    7: 'transparent', 9: 'light_shaft_occlusion', 12: 'depth_prepass', 16: 'reticle',
}
VISIBLE_STAGES = (0, 1, 2, 6, 7)
HIGH_DETAIL_LODS = (0, 1, 2, 3, 10)


@dataclass
class Part:
    mesh_index: int
    part_index: int
    stage: int
    lod: int
    material: int
    positions: np.ndarray            # (n, 3) model space, Tiger axes
    normals: np.ndarray              # (n, 3)
    tangents: np.ndarray             # (n, 4) or None
    uvs: np.ndarray                  # (n, 2) or None, DirectX convention (v down)
    colors: np.ndarray               # (n, 4) uint8 or None
    joints: np.ndarray               # (n, 4) uint16 bone indices
    weights: np.ndarray              # (n, 4) float32
    triangles: np.ndarray            # (m, 3) uint32
    flags: int = 0
    dye_index: int = 0
    extra: dict = field(default_factory=dict)


def shader_input_signature(dxbc):
    """Input elements of a DXBC shader: list of (semantic, index, component count)."""
    if dxbc[:4] != b'DXBC':
        raise ValueError('Not DXBC bytecode')
    chunk_count, = struct.unpack_from('<I', dxbc, 0x1C)
    for i in range(chunk_count):
        offset, = struct.unpack_from('<I', dxbc, 0x20 + i * 4)
        if dxbc[offset:offset + 4] not in (b'ISGN', b'ISG1'):
            continue
        base = offset + 8
        count, = struct.unpack_from('<I', dxbc, base)
        elements = []
        for j in range(count):
            name_offset, index, system_value, _, _, mask = struct.unpack_from('<5IB', dxbc, base + 8 + j * 24)
            end = dxbc.index(b'\0', base + name_offset)
            name = dxbc[base + name_offset:end].decode()
            if name.startswith('SV_') or system_value != 0:
                continue
            elements.append((name.upper(), index, bin(mask).count('1')))
        return elements
    return []


def _element_size(name, components):
    """Stored byte size of one vertex element (not the same as the shader mask)."""
    if name in ('COLOR', 'BLENDINDICES', 'BLENDWEIGHT'):
        return components, True
    if name in ('POSITION', 'NORMAL', 'TANGENT'):
        return 8, False          # always four 16-bit values
    return components * 2, False


def _layout(signature, stride0, stride1):
    """Splits signature elements between vertex buffer 0 and 1 by byte size."""
    layouts, current, used = [[], []], 0, 0
    for name, index, components in signature:
        size, byte_wide = _element_size(name, components)
        if current == 0 and used >= stride0:
            current, used = 1, 0
        layouts[current].append((name, index, size, used, byte_wide))
        used += size
    return layouts


def _read_buffer(pm, header_tag):
    header = pm.read(header_tag)
    size, stride = struct.unpack_from('<IH', header, 0)
    data = pm.read(pm.reference(header_tag), cache=False)
    return data[:size], stride


def _read_indices(pm, header_tag):
    header = pm.read(header_tag)
    is_32 = header[1] != 0
    size, = struct.unpack_from('<Q', header, 8)
    data = pm.read(pm.reference(header_tag), cache=False)[:size]
    return np.frombuffer(data, dtype='<u4' if is_32 else '<u2')


def _strip_to_triangles(strip, restart):
    triangles = []
    run = 0
    for i in range(len(strip) - 2):
        a, b, c = int(strip[i]), int(strip[i + 1]), int(strip[i + 2])
        if restart in (a, b, c):
            run = 0 if c == restart else run
            if c == restart:
                continue
            # A restart inside the window: the next valid window starts a new strip.
            run = 0
            continue
        if a != b and b != c and a != c:
            triangles.append((a, b, c) if run % 2 == 0 else (b, a, c))
        run += 1
    return np.array(triangles, dtype=np.uint32).reshape(-1, 3)


def _strip_runs(strip, restart):
    """Triangles of a strip with primitive restart; winding alternates per run."""
    triangles = []
    start = 0
    values = strip.tolist()
    values.append(restart)
    for end, value in enumerate(values):
        if value != restart:
            continue
        run = values[start:end]
        for i in range(len(run) - 2):
            a, b, c = run[i], run[i + 1], run[i + 2]
            if a == b or b == c or a == c:
                continue
            triangles.append((a, b, c) if i % 2 == 0 else (b, a, c))
        start = end + 1
    return np.array(triangles, dtype=np.uint32).reshape(-1, 3)


def material_shaders(pm, material_tag):
    """(vertex shader bytecode, pixel shader bytecode) of a material; None when absent."""
    r = Reader(pm.read(material_tag))
    out = []
    for offset in (0x48, 0x2C8):
        header = r.u32(offset)
        if pm.exists(header) and pm.exists(pm.reference(header)):
            out.append(pm.read(pm.reference(header)))
        else:
            out.append(None)
    return tuple(out)


def material_textures(pm, material_tag):
    """Pixel shader textures of a material: list of (slot, texture header tag)."""
    r = Reader(pm.read(material_tag))
    return [(r.u32(o), r.u32(o + 4)) for o in r.array_items(0x2D0, 8)]


def external_materials(resource_data, definition):
    """Material per variant shader index, from the model resource of the entity."""
    r = Reader(resource_data)
    materials = [r.u32(o) for o in r.array_items(definition + 0x310, 4)]
    table = []
    for offset in r.array_items(definition + 0x2D0, 0xC):
        count, start = r.i32(offset), r.i32(offset + 4)
        table.append(materials[start] if count > 0 and 0 <= start < len(materials) else 0xFFFFFFFF)
    return table


def read_model(pm, model_tag, stages=VISIBLE_STAGES, high_detail_only=True, variants=(), external_id=None):
    """All renderable parts of one entity model.

    `variants` is the result of `external_materials` for parts that take their
    material from the entity. `external_id` keeps only parts of one body type
    (0 masculine, 1 feminine) when the model holds both.
    """
    data = pm.read(model_tag)
    r = Reader(data)
    scale = np.array(r.floats(0x50, 3), dtype=np.float32)
    translation = np.array(r.floats(0x60, 3), dtype=np.float32)
    uv_scale = np.array(r.floats(0x70, 2), dtype=np.float32)
    uv_translation = np.array(r.floats(0x78, 2), dtype=np.float32)
    parts = []
    for mesh_index, mesh in enumerate(r.array_items(0x10, 0x88)):
        vertex0, vertex1, weights_tag, _, index_tag = (r.u32(mesh + i * 4) for i in range(5))
        if not pm.exists(vertex0) or not pm.exists(index_tag):
            continue
        buffer0, stride0 = _read_buffer(pm, vertex0)
        buffer1, stride1 = _read_buffer(pm, vertex1) if pm.exists(vertex1) else (b'', 0)
        weight_buffer, weight_stride = _read_buffer(pm, weights_tag) if pm.exists(weights_tag) else (b'', 0)
        indices = _read_indices(pm, index_tag)
        restart = 0xFFFFFFFF if indices.dtype.itemsize == 4 else 0xFFFF
        stage_offsets = struct.unpack_from('<25h', data, mesh + 0x28)
        part_offsets = r.array_items(mesh + 0x18, 0x20)
        vertex_count = len(buffer0) // stride0
        raw0 = np.frombuffer(buffer0, dtype=np.uint8, count=vertex_count * stride0).reshape(vertex_count, stride0)
        raw1 = (np.frombuffer(buffer1, dtype=np.uint8, count=vertex_count * stride1).reshape(vertex_count, stride1)
                if stride1 else None)
        for stage in stages:
            for part_index in range(stage_offsets[stage], stage_offsets[stage + 1]):
                if part_index >= len(part_offsets):
                    continue
                po = part_offsets[part_index]
                material = r.u32(po)
                variant = r.i16(po + 4)
                if variant >= 0 and variant < len(variants):
                    material = variants[variant]
                if external_id is not None and r.i16(po + 0x14) != external_id:
                    continue
                primitive = r.i16(po + 6)
                index_offset, index_count = r.u32(po + 8), r.u32(po + 0xC)
                lod = r.u8(po + 0x1B)
                if high_detail_only and lod not in HIGH_DETAIL_LODS:
                    continue
                if not pm.exists(material):
                    continue
                chunk = indices[index_offset:index_offset + index_count]
                if primitive == 5:
                    triangles = _strip_runs(chunk, restart)
                else:
                    triangles = chunk[:len(chunk) // 3 * 3].astype(np.uint32).reshape(-1, 3)
                if len(triangles) == 0:
                    continue
                vertex_shader, _ = material_shaders(pm, material)
                if vertex_shader is None:
                    continue
                layouts = _layout(shader_input_signature(vertex_shader), stride0, stride1)
                used, remap = np.unique(triangles, return_inverse=True)
                attributes = {}
                for raw, layout in ((raw0, layouts[0]), (raw1, layouts[1])):
                    if raw is None:
                        continue
                    for name, index, width, offset, byte_wide in layout:
                        if offset + width > raw.shape[1]:
                            continue
                        block = np.ascontiguousarray(raw[used, offset:offset + width])
                        values = block if byte_wide else block.view('<i2')
                        attributes.setdefault((name, index), values)
                position = attributes.get(('POSITION', 0))
                if position is None:
                    continue
                positions = position[:, :3].astype(np.float32) / 32767.0 * scale + translation
                count = len(used)
                joints = np.zeros((count, 4), dtype=np.uint16)
                weights = np.zeros((count, 4), dtype=np.float32)
                weights[:, 0] = 1.0
                blend_indices = attributes.get(('BLENDINDICES', 0))
                blend_weights = attributes.get(('BLENDWEIGHT', 0))
                if blend_indices is not None and blend_weights is not None:
                    joints[:, :blend_indices.shape[1]] = blend_indices
                    weights[:] = 0
                    weights[:, :blend_weights.shape[1]] = blend_weights.astype(np.float32) / 255.0
                elif weight_stride:
                    raw_w = np.frombuffer(weight_buffer, dtype=np.uint8).reshape(-1, weight_stride)[used]
                    half = weight_stride // 2
                    weights[:] = 0
                    if weight_stride == 4:      # two indices, two weights
                        joints[:, :2] = raw_w[:, 0:2]
                        weights[:, :2] = raw_w[:, 2:4].astype(np.float32) / 255.0
                    else:                        # four weights, four indices
                        weights[:, :half] = raw_w[:, :half].astype(np.float32) / 255.0
                        joints[:, :half] = raw_w[:, half:]
                elif position.shape[1] == 4:
                    # Rigid skinning: the bone index is in the position W value.
                    joints[:, 0] = np.clip(position[:, 3], 0, None).astype(np.uint16)
                # 0xFE / 0xFF mean "no bone".
                weights = np.where(joints >= 0xFE, 0.0, weights)
                joints = np.where(joints >= 0xFE, 0, joints).astype(np.uint16)
                total = weights.sum(axis=1, keepdims=True)
                weights = np.where(total > 0, weights / np.where(total > 0, total, 1), np.array([[1, 0, 0, 0]], np.float32))
                normal = attributes.get(('NORMAL', 0))
                normals = normal[:, :3].astype(np.float32) / 32767.0 if normal is not None else None
                tangent = attributes.get(('TANGENT', 0))
                tangents = tangent.astype(np.float32) / 32767.0 if tangent is not None and tangent.shape[1] == 4 else None
                uv = attributes.get(('TEXCOORD', 0))
                uvs = uv[:, :2].astype(np.float32) / 32767.0 * uv_scale + uv_translation if uv is not None else None
                colors = attributes.get(('COLOR', 0))
                parts.append(Part(
                    mesh_index, part_index, stage, lod, material,
                    positions.astype(np.float32), normals, tangents, uvs, colors,
                    joints, weights.astype(np.float32), remap.reshape(-1, 3).astype(np.uint32),
                    flags=r.u32(po + 0x18), dye_index=r.u8(po + 0x1A),
                    extra={'signature': [(n, i, c) for n, i, c in shader_input_signature(vertex_shader)],
                           'strides': (stride0, stride1, weight_stride), 'primitive': primitive},
                ))
    return parts
