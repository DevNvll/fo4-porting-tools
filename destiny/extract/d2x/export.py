"""Weapon extraction: item name -> raw tags, textures, and .glb files."""
import dataclasses
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from . import anim, entity as ent, graph as gr, model as mdl, texture as tex
from .gltf import GlbBuilder
from .names import bone_name
from .tag import fnv1

RIG = (0x80808F96, 0x80808F8F)
PLAYER_BONE = fnv1('b_r_grip')
CAMERA_BONE = 'b_utility'     # first-person eye point and view axes (view along +Z)
WEAPON_ROOT = 'b_handle'
ARM_BONES = ('b_r_clav', 'b_l_clav')


def to_export_axes(vectors):
    """Tiger (X forward, Y left, Z up) to glTF (Y up, Z forward): [x, y, z] -> [y, z, x]."""
    return np.ascontiguousarray(np.asarray(vectors)[..., [1, 2, 0]])


def quat_matrix(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def matrix_quat(m):
    trace = m[0, 0] + m[1, 1] + m[2, 2]
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        q = [(m[2, 1] - m[1, 2]) * s, (m[0, 2] - m[2, 0]) * s, (m[1, 0] - m[0, 1]) * s, 0.25 / s]
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2])
        q = [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s]
    elif m[1, 1] > m[2, 2]:
        s = 2.0 * np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2])
        q = [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s]
    else:
        s = 2.0 * np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1])
        q = [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def decompose(matrix):
    translation = matrix[:3, 3].copy()
    scale = np.linalg.norm(matrix[:3, :3], axis=0)
    rotation = matrix_quat(matrix[:3, :3] / np.where(scale > 1e-8, scale, 1))
    return translation, rotation, scale


@dataclass
class SkeletonData:
    tag: int
    hashes: list
    names: list
    parents: list
    world: np.ndarray        # (n, 4, 4) bind pose, object space, export axes
    local: np.ndarray        # (n, 4, 4) bind pose, parent space

    def __len__(self):
        return len(self.hashes)

    def index_of(self, name_hash):
        return self.hashes.index(name_hash) if name_hash in self.hashes else -1


def skeleton_data(resource):
    skeleton = ent.read_skeleton(resource)
    count = len(skeleton)
    world = np.zeros((count, 4, 4))
    translations = to_export_axes(skeleton.translations)
    rotations = skeleton.rotations[:, [1, 2, 0, 3]]
    for i in range(count):
        world[i, :3, :3] = quat_matrix(rotations[i]) * skeleton.scales[i]
        world[i, :3, 3] = translations[i]
        world[i, 3, 3] = 1
    local = world.copy()
    for i, parent in enumerate(skeleton.parents):
        if parent >= 0:
            local[i] = np.linalg.inv(world[parent]) @ world[i]
    names, used = [], {}
    for name_hash in skeleton.hashes:
        name = bone_name(name_hash)
        if name in used:
            used[name] += 1
            name = f'{name}.{used[name]:03d}'
        else:
            used[name] = 0
        names.append(name)
    return SkeletonData(resource.tag, skeleton.hashes, names, skeleton.parents, world, local)


@dataclass
class MeshSet:
    name: str
    parts: list
    source: SkeletonData         # skeleton that the part joint indices refer to
    plates: dict = field(default_factory=dict)
    plate_key: str = ''
    material_plates: dict = field(default_factory=dict)   # material tag -> plates, for parts without gear plates


class Workspace:
    """Output folder of one extraction, with the raw tag dump."""

    def __init__(self, pm, root):
        self.pm = pm
        self.root = Path(root)
        self.raw = self.root / 'raw'
        self.textures = self.root / 'textures'
        self.raw.mkdir(parents=True, exist_ok=True)
        self.textures.mkdir(parents=True, exist_ok=True)

    def dump(self, tag):
        path = self.raw / f'{tag:08X}.bin'
        if not path.is_file():
            path.write_bytes(self.pm.read(tag))
        return path


def rig_for(workspace, entity):
    """Parser rig (skeleton + runtime rig) of an entity, or None."""
    skeleton, rig = entity.first(ent.SKELETON), entity.first(RIG)
    if skeleton is None or rig is None:
        return None
    return anim.Rig(workspace.dump(skeleton.tag), workspace.dump(rig.tag), workspace.pm.version)


def collect_clips(workspace, entity, rig, prefix, log=print):
    """Decodes every clip of every animation set of an entity."""
    pm = workspace.pm
    tags, seen = [], set()
    for resource in entity.by_kind(ent.ANIMATION):
        for set_tag in ent.animation_sets(pm, resource):
            for order, clip_tag in enumerate(ent.animation_set_clips(pm, set_tag)):
                if clip_tag in seen or not pm.exists(clip_tag) or pm.reference(clip_tag) != ent.ANIMATION_CLIP:
                    continue
                seen.add(clip_tag)
                tags.append((set_tag, order, clip_tag))

    # Additive clips hold offsets only. They are shown on the first frame of the
    # first full-pose clip of the set (in the game, on the pose that plays then).
    base, base_name = None, None
    for _, order, clip_tag in tags:
        try:
            data, tracks = rig.controls(workspace.dump(clip_tag))
        except Exception:
            continue
        if data.animation_header.node_count >= rig.bone_count and not rig.is_additive(tracks):
            base, base_name = tracks, f'{prefix}_{order:03d}_{clip_tag:08X}'
            break

    clips, records = [], []
    for set_tag, order, clip_tag in tags:
        header = anim.clip_header(pm.read(clip_tag))
        name = f'{prefix}_{order:03d}_{clip_tag:08X}'
        record = {'name': name, 'tag': f'{clip_tag:08X}', 'set': f'{set_tag:08X}', 'order': order,
                  'animation_hash': f'{header["hash"]:08X}', 'frames': header['frames'],
                  'seconds': round(header['frames'] / anim.FRAME_RATE, 3), 'nodes': header['nodes']}
        try:
            clip = rig.decode(workspace.dump(clip_tag), name, base)
        except Exception as error:   # one bad clip must not stop the export
            record['error'] = f'{type(error).__name__}: {error}'
            log(f'  clip {clip_tag:08X} did not decode: {record["error"]}')
            records.append(record)
            continue
        if clip.additive:
            clip.name = record['name'] = f'{name}_add'
            record['additive'] = True
            record['shown_on'] = base_name
        record['codecs'] = list(clip.codecs)
        record['package'] = pm.pkg_name(clip_tag)
        record['moving_bones'] = int(clip.animated.sum())
        clips.append(clip)
        records.append(record)
    return clips, records


def linked_rigs(pm, pattern_entity, weapon_hashes):
    """Entities linked from the weapon whose skeleton holds a player body and the weapon bones."""
    found = []
    for resource in pattern_entity.resources:
        words = np.frombuffer(resource.data[:len(resource.data) & ~3], dtype='<u4')
        for value in np.unique(words[(words > 0x80812000) & (words <= 0x81FFFFFF)]).tolist():
            if value == pattern_entity.tag or not pm.exists(value) or pm.reference(value) != ent.ENTITY:
                continue
            if any(value == tag for tag, _, _ in found):
                continue
            candidate = ent.read_entity(pm, value)
            skeleton = candidate.first(ent.SKELETON)
            if skeleton is None or candidate.first(RIG) is None:
                continue
            hashes = ent.read_skeleton(skeleton).hashes
            if PLAYER_BONE not in hashes:
                continue
            shared = sum(1 for h in weapon_hashes if h in hashes)
            if shared:
                found.append((value, shared, len(hashes)))
    found.sort(key=lambda row: (-row[1], row[2]))
    return [tag for tag, _, _ in found]


HEAD_BONES = ('b_head', 'b_neck_1', 'b_neck_2', 'b_jaw', 'b_l_eye', 'b_r_eye')


def find_player_body(pm, log=print):
    """Player entity with the 72-bone body skeleton and the body (hands, head) model.

    The result is cached, because the search reads every entity tag once.
    """
    cache = ent_cache_path(pm)
    if cache.is_file():
        tag = int(json.loads(cache.read_text())['entity'], 16)
        if pm.exists(tag):
            return tag
    from .tag import Reader
    log('  searching the player body entity (one time) ...')
    wanted = {fnv1('b_r_thumb_3'), fnv1('b_head'), PLAYER_BONE}
    finger = fnv1('b_r_index_2')
    best = (0, 0)
    for tag in pm.by_reference(ent.ENTITY):
        data = pm.read(tag, cache=False)
        if len(data) < 0x20 or Reader(data).u64(0x10) < 40:
            continue
        entity = ent.read_entity(pm, tag)
        skeleton, model = entity.first(ent.SKELETON), entity.first(ent.MODEL)
        if skeleton is None or model is None:
            continue
        hashes = ent.read_skeleton(skeleton).hashes
        if len(hashes) != 72 or not wanted <= set(hashes):
            continue
        # The body model is the one with the most geometry on the finger bones.
        model_tag = model.reader.u32(model.definition + 0x1DC)
        if not pm.exists(model_tag) or pm.reference(model_tag) != mdl.MODEL:
            continue
        variants = mdl.external_materials(model.data, model.definition)
        index = hashes.index(finger)
        score = 0
        for part in mdl.read_model(pm, model_tag, stages=(0,), variants=variants, external_id=0):
            score += int(((part.joints == index) & (part.weights > 0)).any(axis=1).sum())
        if score > best[1]:
            best = (tag, score)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({'entity': f'{best[0]:08X}'}))
    return best[0]


def ent_cache_path(pm):
    from .refs import CACHE
    return CACHE / f'player_body_{pm.version}.json'


def body_mesh_sets(workspace, rig_skeleton, feminine, log=print):
    """Hands of the player body, for the first-person rig."""
    pm = workspace.pm
    body_tag = find_player_body(pm, log)
    if not body_tag:
        return [], None
    entity = ent.read_entity(pm, body_tag)
    source = skeleton_data(entity.first(ent.SKELETON))
    resource = entity.first(ent.MODEL)
    model_tag = resource.reader.u32(resource.definition + 0x1DC)
    variants = mdl.external_materials(resource.data, resource.definition)
    parts = mdl.read_model(pm, model_tag, stages=(0,), variants=variants, external_id=1 if feminine else 0)
    head = {source.index_of(fnv1(name)) for name in HEAD_BONES}
    hands = [p for p in parts if not (set(np.unique(p.joints[p.weights > 0]).tolist()) & head)]
    material_plates = {}
    for part in hands:
        if part.material not in material_plates:
            textures = [t for _, t in mdl.material_textures(pm, part.material)]
            material_plates[part.material] = tex.material_images(pm, textures)
            for kind, pixels in material_plates[part.material].items():
                target = workspace.textures / f'{part.material:08X}_{kind}.png'
                if not target.is_file():
                    tex.save_png(pixels, target)
    record = {'entity': f'{body_tag:08X}', 'model': f'{model_tag:08X}', 'parts': len(hands),
              'triangles': int(sum(len(p.triangles) for p in hands))}
    log(f'  mesh body_hands: {len(hands)} parts, {record["triangles"]} triangles')
    return [MeshSet('body_hands', hands, source, {}, f'{model_tag:08X}', material_plates)], record


def _png(pixels, alpha=False):
    stream = io.BytesIO()
    Image.fromarray(pixels if alpha else np.ascontiguousarray(pixels[:, :, :3])).save(stream, 'PNG')
    return stream.getvalue()


def plate_images(plates):
    """glTF images from gear plates: base color, normal, occlusion/roughness/metal."""
    images = {}
    if 'albedo' in plates:
        images['base_color'] = plates['albedo']
    if 'normal' in plates:
        images['normal'] = plates['normal']
    if 'gstack' in plates:
        gstack = plates['gstack'].astype(np.float32)
        orm = np.zeros_like(plates['gstack'])
        orm[:, :, 0] = plates['gstack'][:, :, 0]                      # ambient occlusion
        orm[:, :, 1] = 255 - plates['gstack'][:, :, 1]                # smoothness -> roughness
        orm[:, :, 2] = np.clip(gstack[:, :, 3] * (255.0 / 32.0), 0, 255).astype(np.uint8)   # undyed metalness
        orm[:, :, 3] = 255
        images['orm'] = orm
        emission = np.clip((gstack[:, :, 2] - 40.0) * (255.0 / 215.0), 0, 255).astype(np.uint8)
        if emission.max() > 8 and 'albedo' in plates:
            glow = (plates['albedo'][:, :, :3].astype(np.float32) * (emission[:, :, None] / 255.0)).astype(np.uint8)
            images['emissive'] = np.dstack([glow, np.full(glow.shape[:2], 255, np.uint8)])
    return images


def clip_world(skeleton, clip, frame):
    """Object-space bone matrices of one clip frame."""
    world = [None] * len(skeleton)
    for i in range(len(skeleton)):
        local = np.eye(4)
        local[:3, :3] = quat_matrix(clip.rotations[i, frame]) * clip.scales[i, frame]
        local[:3, 3] = clip.translations[i, frame]
        parent = skeleton.parents[i]
        world[i] = local if parent < 0 else world[parent] @ local
    return world


def build_glb(path, skeleton, mesh_sets, clips, title, markers=()):
    """Writes one .glb: armature, skinned meshes, materials, and one animation per clip.

    `markers` are extra nodes below bones: (name, bone name, 4x4 local matrix or None, is_camera).
    """
    glb = GlbBuilder(generator='d2x (destiny-weapons)')
    root = glb.node(title)
    bone_nodes = []
    bind = []
    for i in range(len(skeleton)):
        translation, rotation, scale = decompose(skeleton.local[i])
        bind.append((translation, rotation, scale))
        parent = skeleton.parents[i]
        bone_nodes.append(glb.node(
            skeleton.names[i], bone_nodes[parent] if parent >= 0 else root,
            translation=[float(v) for v in translation], rotation=[float(v) for v in rotation],
            scale=[float(v) for v in scale]))
    inverse_bind = np.linalg.inv(skeleton.world)
    skin = glb.skin(f'{title}_skin', bone_nodes, inverse_bind, bone_nodes[0])
    for marker_name, bone_name, matrix, is_camera in markers:
        if bone_name not in skeleton.names:
            continue
        fields = {}
        if matrix is not None:
            translation, rotation, _ = decompose(np.asarray(matrix, dtype=np.float64))
            fields = {'translation': [float(v) for v in translation], 'rotation': [float(v) for v in rotation]}
        parent = bone_nodes[skeleton.names.index(bone_name)]
        if is_camera:
            # A glTF camera looks along its -Z axis; the marker looks along +Z.
            holder = glb.node(marker_name, parent, **fields)
            glb.node(f'{marker_name}_camera', holder, rotation=[0.0, 1.0, 0.0, 0.0], camera=glb.camera(marker_name))
        else:
            glb.node(marker_name, parent, **fields)

    materials = {}

    def material_for(mesh_set, part):
        transparent = part.stage != 0
        plates, label = mesh_set.plates, mesh_set.plate_key
        if part.material in mesh_set.material_plates:
            plates, label = mesh_set.material_plates[part.material], f'{part.material:08X}'
        key = (label, transparent)
        if key in materials:
            return materials[key]
        images = plate_images(plates)
        indices = {kind: glb.texture(_png(pixels), f'{label}_{kind}') for kind, pixels in images.items()}
        materials[key] = glb.material(
            f'{label}{"_transparent" if transparent else ""}',
            base_color=indices.get('base_color'), normal=indices.get('normal'), orm=indices.get('orm'),
            emissive=indices.get('emissive'), alpha_mode='BLEND' if transparent else 'OPAQUE')
        return materials[key]

    for mesh_set in mesh_sets:
        source = mesh_set.source
        # Joint index of the source skeleton -> joint index of this skeleton (by bone name hash).
        remap = np.array([max(skeleton.index_of(h), 0) for h in source.hashes], dtype=np.uint16)
        # Meshes are stored in the bind space of their own skeleton. When the
        # target skeleton holds the same bones at other places (weapon bones on
        # the hand of the player), move each vertex with its bones.
        rebind = np.stack([skeleton.world[remap[i]] @ np.linalg.inv(source.world[i]) for i in range(len(source))])
        moved = bool(np.abs(rebind - np.eye(4)).max() > 1e-5)
        primitives = []
        for part in mesh_set.parts:
            source_joints = np.clip(part.joints, 0, len(source) - 1)
            joints = np.where(part.weights > 0, remap[source_joints], 0)
            positions = to_export_axes(part.positions).astype(np.float64)
            normals = to_export_axes(part.normals).astype(np.float64) if part.normals is not None else None
            tangents = None
            if part.tangents is not None:
                tangents = np.concatenate([to_export_axes(part.tangents[:, :3]), part.tangents[:, 3:4]], axis=1).astype(np.float64)
            if moved:
                blend = np.einsum('vj,vjab->vab', part.weights.astype(np.float64), rebind[source_joints])
                positions = np.einsum('vab,vb->va', blend[:, :3, :3], positions) + blend[:, :3, 3]
                if normals is not None:
                    normals = np.einsum('vab,vb->va', blend[:, :3, :3], normals)
                if tangents is not None:
                    tangents[:, :3] = np.einsum('vab,vb->va', blend[:, :3, :3], tangents[:, :3])
            if normals is not None:
                length = np.linalg.norm(normals, axis=1, keepdims=True)
                normals = normals / np.where(length > 1e-6, length, 1)
            if tangents is not None:
                length = np.linalg.norm(tangents[:, :3], axis=1, keepdims=True)
                tangents[:, :3] /= np.where(length > 1e-6, length, 1)
                tangents[:, 3] = np.where(tangents[:, 3] < 0, -1.0, 1.0)
            primitives.append(glb.primitive(
                positions, part.triangles, material_for(mesh_set, part),
                normals=normals, tangents=tangents, uvs=part.uvs, joints=joints, weights=part.weights))
        if primitives:
            glb.node(mesh_set.name, root, mesh=glb.mesh(mesh_set.name, primitives), skin=skin)

    # Every clip keys every bone. A bone without keys keeps the pose of the clip
    # that the viewer showed before (Blender does this), which moves the weapon
    # away from the hand. Constant channels use one key, so the cost is small.
    bone_count = min([len(skeleton)] + [clip.rotations.shape[0] for clip in clips])
    scaled = {bone for clip in clips for bone in range(bone_count)
              if np.abs(clip.scales[bone] - bind[bone][2]).max() > 1e-4}
    for clip in clips:
        frames = clip.rotations.shape[1]
        times = np.arange(frames, dtype=np.float32) / anim.FRAME_RATE
        channels = []
        for bone in range(bone_count):
            rotations = clip.rotations[bone].astype(np.float64).copy()
            rotations /= np.linalg.norm(rotations, axis=1, keepdims=True)
            # Keep neighbour quaternions in the same hemisphere for clean interpolation.
            if np.dot(rotations[0], bind[bone][1]) < 0:
                rotations[0] = -rotations[0]
            for frame in range(1, frames):
                if np.dot(rotations[frame], rotations[frame - 1]) < 0:
                    rotations[frame] = -rotations[frame]
            tracks = [('rotation', rotations, 1e-6), ('translation', clip.translations[bone], 1e-7)]
            if bone in scaled:
                tracks.append(('scale', clip.scales[bone], 1e-6))
            for path_name, values, limit in tracks:
                constant = np.ptp(values, axis=0).max() <= limit
                # The first bone keeps all keys, so that the clip keeps its length.
                if constant and not (bone == 0 and path_name == 'translation'):
                    values = values[:1]
                channels.append((bone_nodes[bone], path_name, values))
        glb.animation(clip.name, times, channels)
    return glb.save(path)


def named_set(pm, rig_entity, clips, records, content_group):
    """The clips that the game uses for this weapon, with the names of the game states.

    Returns (clips with state names, state records for the manifest).
    """
    by_key = {(record['set'], record['order']): record['name'] for record in records if 'error' not in record}
    by_name = {clip.name: clip for clip in clips}
    named, used_names, state_records = [], set(), []
    for resource in rig_entity.by_kind(ent.ANIMATION):
        for set_tag in ent.animation_sets(pm, resource):
            for state in gr.resolve(pm, resource.data, set_tag, content_group):
                record = {'name': state['name'], 'game_names': state['game_names'], 'hashes': state['hashes'],
                          'choices': []}
                for position, choice in enumerate(state['choices']):
                    # The first choice of a state has the plain state name.
                    suffix = choice['condition'] or f'choice{position + 1}'
                    base = state['name'] if position == 0 else f"{state['name']}_{suffix}"
                    choice_record = {'condition': choice['condition'], 'condition_hashes': choice['condition_hashes'],
                                     'weapon_tag': choice['weapon_tag'], 'clips': []}
                    for number, (clip_index, weight) in enumerate(choice['clips']):
                        source = by_key.get((f'{set_tag:08X}', clip_index))
                        if source is None or source not in by_name:
                            continue
                        name = base if number == 0 else f'{base}_{number + 1}'
                        while name in used_names:
                            name += '_'
                        used_names.add(name)
                        named.append(dataclasses.replace(by_name[source], name=name))
                        choice_record['clips'].append({'name': name, 'clip': source, 'threshold': weight})
                    if choice_record['clips']:
                        record['choices'].append(choice_record)
                if record['choices']:
                    state_records.append(record)
    return named, state_records


def camera_markers(skeleton, named):
    """Camera at the camera bone, and the eye point of the aim pose in weapon space."""
    if CAMERA_BONE not in skeleton.names:
        return []
    markers = [('fp_view', CAMERA_BONE, None, True)]
    aim = next((clip for clip in named if clip.name == 'iron_sight_idle'), None)
    if aim is not None and WEAPON_ROOT in skeleton.names:
        world = clip_world(skeleton, aim, 0)
        eye = np.linalg.inv(world[skeleton.names.index(WEAPON_ROOT)]) @ world[skeleton.names.index(CAMERA_BONE)]
        markers.append(('ads_eye', WEAPON_ROOT, eye, False))
    return markers


def slug(text):
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')


def art_mesh_sets(workspace, inv, item, source_skeleton, stages, log=print, prefix='', variant=None):
    """Render meshes of an item's art arrangement, with their texture plates."""
    pm = workspace.pm
    mesh_sets, records = [], []
    for arrangement in item.art_arrangement_indices:
        entities = inv.art_entities(arrangement)
        # Armor has one entity per body type (masculine first, feminine second).
        singles = [row for row in entities if row[0] == -1]
        if variant is not None and len(singles) > 1:
            keep = singles[min(variant, len(singles) - 1)]
            entities = [row for row in entities if row[0] != -1 or row == keep]
        for region, entity_tag in entities:
            entity = ent.read_entity(pm, entity_tag)
            resource = entity.first(ent.MODEL)
            if resource is None:
                continue
            model_tag = resource.reader.u32(resource.definition + 0x1DC)
            if not pm.exists(model_tag) or pm.reference(model_tag) != mdl.MODEL:
                continue
            variants = mdl.external_materials(resource.data, resource.definition)
            parts = mdl.read_model(pm, model_tag, stages=stages, variants=variants)
            plate_set = tex.find_plate_set(pm, resource.data)
            plates = tex.read_plates(pm, plate_set) if plate_set else {}
            key = f'{plate_set:08X}' if plate_set else f'{model_tag:08X}'
            for kind, pixels in plates.items():
                target = workspace.textures / f'{key}_{kind}.png'
                if not target.is_file():
                    tex.save_png(pixels, target)
            name = f'{prefix}region{region:02d}_{entity_tag:08X}' if region >= 0 else f'{prefix}{entity_tag:08X}'
            mesh_sets.append(MeshSet(name, parts, source_skeleton, plates, key))
            records.append({'region': region, 'entity': f'{entity_tag:08X}', 'model': f'{model_tag:08X}',
                            'plate_set': key, 'parts': len(parts),
                            'vertices': int(sum(len(p.positions) for p in parts)),
                            'triangles': int(sum(len(p.triangles) for p in parts))})
            log(f'  mesh {name}: {len(parts)} parts, {records[-1]["triangles"]} triangles')
    return mesh_sets, records


def extract_weapon(pm, inv, item_hash, out_root, stages=(0,), arms=(), feminine=False, log=print):
    """Full extraction of one weapon. Returns the manifest dict."""
    item = inv.item(item_hash)
    pattern = inv.pattern(item.pattern_index)
    if pattern is None or not pattern.entity:
        raise LookupError(f'Item {item_hash} ({item.name!r}) has no weapon pattern entity')
    name = slug(item.name) or str(item_hash)
    workspace = Workspace(pm, Path(out_root) / name)
    log(f'{item.name}: item {item_hash}, pattern entity {pattern.entity:08X}')

    pattern_entity = ent.read_entity(pm, pattern.entity)
    weapon_skeleton_resource = pattern_entity.first(ent.SKELETON)
    if weapon_skeleton_resource is None:
        raise LookupError(f'Pattern entity {pattern.entity:08X} has no skeleton')
    weapon_skeleton = skeleton_data(weapon_skeleton_resource)
    manifest = {
        'name': item.name, 'item_hash': item_hash, 'game_version': pm.version,
        'pattern': {'index': pattern.index, 'entity': f'{pattern.entity:08X}',
                    'content_group': f'{pattern.content_group:08X}', 'weapon_type': f'{pattern.weapon_type:08X}'},
        'weapon_skeleton': {'tag': f'{weapon_skeleton.tag:08X}', 'bones': weapon_skeleton.names},
        'frame_rate': anim.FRAME_RATE,
        'axes': 'glTF: +Y up, +Z forward (game: +Z up, +X forward)',
        'files': {},
    }

    mesh_sets, manifest['meshes'] = art_mesh_sets(workspace, inv, item, weapon_skeleton, stages, log)

    # Weapon alone: 8-bone style rig with the weapon's own clips.
    weapon_rig = rig_for(workspace, pattern_entity)
    weapon_clips, manifest['weapon_clips'] = (collect_clips(workspace, pattern_entity, weapon_rig, 'weapon', log)
                                              if weapon_rig else ([], []))
    for record, clip in zip([r for r in manifest['weapon_clips'] if 'error' not in r], weapon_clips):
        record['moving_weapon_bones'] = [weapon_skeleton.names[i] for i in range(len(weapon_skeleton))
                                         if clip.animated[i]]
    target = workspace.root / f'{name}_weapon.glb'
    size = build_glb(target, weapon_skeleton, mesh_sets, weapon_clips, f'{name}_weapon')
    manifest['files']['weapon'] = target.name
    log(f'  wrote {target} ({size / 1e6:.1f} MB, {len(weapon_clips)} clips)')

    # First-person rigs: player body skeleton + weapon bones + the player's weapon clips.
    manifest['first_person'] = []
    for number, rig_tag in enumerate(linked_rigs(pm, pattern_entity, weapon_skeleton.hashes)):
        rig_entity = ent.read_entity(pm, rig_tag)
        rig_skeleton = skeleton_data(rig_entity.first(ent.SKELETON))
        rig = rig_for(workspace, rig_entity)
        prefix = 'fp' if number == 0 else f'fp{number + 1}'
        clips, records = collect_clips(workspace, rig_entity, rig, prefix, log)
        # Which weapon parts move tells a reload from a shot or from locomotion.
        weapon_bones = [rig_skeleton.index_of(h) for h in weapon_skeleton.hashes[1:]]
        by_name = {clip.name: clip for clip in clips}
        for record in records:
            clip = by_name.get(record['name'])
            if clip is not None:
                record['moving_weapon_bones'] = [rig_skeleton.names[i] for i in weapon_bones
                                                 if 0 <= i < len(clip.animated) and clip.animated[i]]
        suffix = 'first_person' if number == 0 else f'first_person_{number + 1}'
        target = workspace.root / f'{name}_{suffix}.glb'
        # Armor is skinned to the player body bones, which this rig holds with the same names.
        body_sets, hands_record = body_mesh_sets(workspace, rig_skeleton, feminine, log)
        body_records = [{'name': 'player body hands', **hands_record}] if hands_record else []
        for arm_hash in arms:
            arm_item = inv.item(arm_hash)
            sets, records_ = art_mesh_sets(workspace, inv, arm_item, rig_skeleton, (0,), log,
                                           prefix=f'{slug(arm_item.name)}_', variant=1 if feminine else 0)
            body_sets += sets
            body_records.append({'name': arm_item.name, 'item_hash': arm_hash, 'meshes': records_})
        named, states = named_set(pm, rig_entity, clips, records, pattern.content_group)
        markers = camera_markers(rig_skeleton, named)
        size = build_glb(target, rig_skeleton, mesh_sets + body_sets, clips, f'{name}_{suffix}', markers)
        set_file = None
        if named:
            set_target = workspace.root / f'{name}_{suffix}_set.glb'
            set_size = build_glb(set_target, rig_skeleton, mesh_sets + body_sets, named, f'{name}_{suffix}_set', markers)
            set_file = set_target.name
            manifest['files'][f'{suffix}_set'] = set_file
            log(f'  wrote {set_target} ({set_size / 1e6:.1f} MB, {len(named)} named clips of {len(states)} game states)')
        manifest['files'][suffix] = target.name
        manifest['first_person'].append({
            'entity': f'{rig_tag:08X}', 'skeleton': f'{rig_skeleton.tag:08X}',
            'bones': rig_skeleton.names, 'file': target.name, 'set_file': set_file,
            'camera_bone': CAMERA_BONE if CAMERA_BONE in rig_skeleton.names else None,
            'body': body_records, 'states': states, 'clips': records,
        })
        log(f'  wrote {target} ({size / 1e6:.1f} MB, {len(rig_skeleton)} bones, {len(clips)} clips)')

    (workspace.root / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return manifest
