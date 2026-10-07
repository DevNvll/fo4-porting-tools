"""Make the Fallout 4 model of the gun for an esx project: the model file, the textures and the materials.

    ./port destiny model FILE.glb --set destiny/port/sets/WEAPON.toml [--mod NAME] [--textures DIR]
    python3 destiny/port/tools/d2model.py FILE.glb --set SET.toml [--parts WORK/parts.json]
        [--mod NAME | --project FOLDER] [--data "/path/Fallout 4/Data"] [--textures DIR]

The project is the esx project of the mod in the data folder: data/mods/NAME (--mod NAME;
default: `name` of [model] in the set file), or the folder of --project. `./port mod sync NAME`
puts the hand-written files of mods/NAME there, and `./port mod build NAME` builds it. The
default of --parts is the parts file of the work folder of the weapon
(data/destiny/port/work/WEAPON/parts.json; WEAPON is the file name with no `_first_person`).
The default of --data is the setting `fo4_data` (FO4_DATA, or data/config.toml).

The program writes into the project folder:

    meshes/Weapons/NAME/NAME.glb         the model file (glTF 2.0) that `esx build` makes the mesh from
    meshes/Weapons/NAME/NAME.mesh.toml   its job file: the material paths and the connect point
    assets/Textures/Weapons/NAME/        MATERIAL_d.dds, _n.dds and _s.dds for each texture set
    assets/Materials/Weapons/NAME/       MATERIAL.bgsm: the material of the template weapon with these textures

The model has the shapes of the parts file (tools/d2parts.py), each below the node of its
Fallout 4 weapon bone, so the clips move them. Each weapon bone of the template is a node, at
its rest place. The model is in game units (the job file has scale = 1.0): the game point
(x, y, z) is the model point (x, z, -y). The node ProjectileNode is at `muzzle` of [model] in
the set file. The layout is that of tools/port_glb.py of the repository fnv-fo4-port (tag
before-animation-only), which made the models of the three New Vegas ports.

A texture set of Destiny has three files (DIR/SET_albedo.png, _normal.png, _gstack.png;
default DIR: the folder `textures` beside the file), and the gun has its dyes (`dyes` of
[model]: the file of tools/d2dyes.py beside the file of the gun). tools/d2shade.py does the
gear shader of Destiny for each pixel (the dyes, the wear, the metal value) and makes the
Fallout 4 textures from the result:

    _d   the base color, darker where the occlusion is low (Fallout 4 has no occlusion texture)
    _n   the normal map, with the detail normal of the dyes
    _s   red: specular, from the reflectance of the surface; green: glossiness, the smoothness

`occlusion` (default 0.5) and `specular` (default 0.9) of [model] are the weight of the
occlusion in the base color and the scale of the specular value.

A size that is not a power of two becomes the next power of two (2048 at most). The program
`esx` writes the DDS files and the material files: the setting `esx` names it (ESX_BIN, then
data/config.toml, then esx in the PATH).

The sight ([model.sight] of the set file, with the file of tools/d2reticle.py). The glass of the
sight and the reticle are a second part of the weapon:

    meshes/Weapons/NAME/NAMESight.glb    the glass (one shape) and the reticle (one quad)
    assets/Textures/Weapons/NAME/        SightGlass_d.dds and Reticle_d.dds, each with alpha
    assets/Materials/Weapons/NAME/       SightGlass.bgem and Reticle.bgem: effect materials

    meshes/Weapons/NAME/NAMESight.template.nif   the template mesh of that model

`esx` makes no new effect shader, so the job file of this model names a template: a vanilla
mesh (`template` of [model.sight], from the archives of --data) with the names and the texture
paths of this weapon. Two of its shapes with an effect shader get the geometry. The
model of the gun gets the connect point P-Scope on the bone of the glass, and the sight has
the point C-Scope: the game puts the sight on that bone, and a clip that moves the bone moves
the sight. The reticle is a quad at a right angle to the weapon axis, at the place on the
glass that `center` gives. The aim point of [sight] must be that place: the program prints it.
"""
import argparse
import json
import os
import shutil
import struct
import subprocess
import sys
import tomllib
import numpy as np

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fo4clip  # noqa: E402  (adds fnv/tools to the path)
from d2template import Template  # noqa: E402


def esx_program():
    return paths.require('esx')


def esx(*args):
    r = subprocess.run([esx_program(), *args, '--format', 'json'], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('esx %s failed: %s' % (' '.join(args[:2]), (r.stdout or r.stderr)[:800]))
    return json.loads(r.stdout) if r.stdout.strip().startswith('{') else {}


def g2m(p):
    """Game point (x, y, z) -> model point (x, z, -y)."""
    p = np.asarray(p, np.float64)
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1)


class Model:
    """A small writer of a glTF binary file: nodes, and meshes with one primitive."""

    def __init__(self):
        self.bin = bytearray()
        self.views, self.accessors, self.meshes, self.nodes, self.materials = [], [], [], [], []
        self.material_index = {}

    def _accessor(self, arr, component, kind, target, bounds=False):
        while len(self.bin) % 4:
            self.bin.append(0)
        self.views.append({'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': arr.nbytes, 'target': target})
        self.bin.extend(arr.tobytes())
        a = {'bufferView': len(self.views) - 1, 'componentType': component, 'count': int(arr.shape[0]), 'type': kind}
        if bounds:
            a['min'] = [float(x) for x in arr.min(0)]
            a['max'] = [float(x) for x in arr.max(0)]
        self.accessors.append(a)
        return len(self.accessors) - 1

    def material(self, name):
        if name not in self.material_index:
            self.material_index[name] = len(self.materials)
            self.materials.append({'name': name, 'pbrMetallicRoughness': {'baseColorFactor': [0.3, 0.3, 0.32, 1.0],
                                                                         'metallicFactor': 0.4, 'roughnessFactor': 0.6}})
        return self.material_index[name]

    def mesh(self, name, positions, normals, uvs, triangles, material):
        pos = g2m(positions).astype(np.float32)
        idx = np.asarray(triangles).reshape(-1).astype(np.uint16 if len(pos) < 65536 else np.uint32)
        prim = {'attributes': {'POSITION': self._accessor(pos, 5126, 'VEC3', 34962, True),
                               'NORMAL': self._accessor(g2m(normals).astype(np.float32), 5126, 'VEC3', 34962),
                               'TEXCOORD_0': self._accessor(np.asarray(uvs, np.float32), 5126, 'VEC2', 34962)},
                'indices': self._accessor(idx, 5123 if idx.dtype == np.uint16 else 5125, 'SCALAR', 34963),
                'material': self.material(material), 'mode': 4}
        self.meshes.append({'name': name, 'primitives': [prim]})
        return len(self.meshes) - 1

    def node(self, name, translation=None, mesh=None, parent=None, rotation=None):
        n = {'name': name}
        if translation is not None and np.any(np.abs(translation) > 0):
            n['translation'] = [float(x) for x in g2m(translation)]
        if rotation is not None:
            # a game rotation (x, y, z, w) in the axes of the model: the axis turns as a point
            x, y, z, w = [float(v) for v in rotation]
            n['rotation'] = [x, z, -y, w]
        if mesh is not None:
            n['mesh'] = mesh
        self.nodes.append(n)
        if parent is not None:
            self.nodes[parent].setdefault('children', []).append(len(self.nodes) - 1)
        return len(self.nodes) - 1

    def write(self, path, root):
        js = {'asset': {'version': '2.0', 'generator': 'd2model.py'}, 'scene': 0, 'scenes': [{'nodes': [root]}],
              'nodes': self.nodes, 'meshes': self.meshes, 'materials': self.materials, 'accessors': self.accessors,
              'bufferViews': self.views, 'buffers': [{'byteLength': len(self.bin)}]}
        jb = json.dumps(js, separators=(',', ':')).encode()
        jb += b' ' * (-len(jb) % 4)
        bb = bytes(self.bin) + b'\0' * (-len(self.bin) % 4)
        with open(path, 'wb') as f:
            f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(bb)))
            f.write(struct.pack('<II', len(jb), 0x4E4F534A) + jb)
            f.write(struct.pack('<II', len(bb), 0x004E4942) + bb)


def write_model(parts, template, name, names, muzzle, out, suffix='', scope=None):
    """names: material of the file -> name of the Fallout 4 material. `suffix` is at the end of
    the name of each material file (the model of a second shader of the gun). `scope` is the
    weapon bone with the parent connect point P-Scope (the sight part)."""
    g = Model()
    root = g.node('WEAPON')
    nodes = {'Weapon': root}
    # each weapon bone of the template, so a vanilla clip finds each node that it moves
    todo = list(template.pivots)
    while todo:
        b = todo.pop(0)
        parent = template.parents[b]
        if parent not in nodes:
            todo.append(b)
            continue
        nodes[b] = g.node(b, template.pivots[b], parent=nodes[parent], rotation=template.rotations.get(b))
    static = g.node(name + 'Receiver', parent=root)
    used = []
    for s in parts['shapes']:
        if 'normals' not in s or 'uvs' not in s:
            raise SystemExit('the shape %s of the parts file has no normals or no texture coordinates' % s['name'])
        material = names.get(s['material'], s['material'])
        if material not in used:
            used.append(material)
        m = g.mesh(s['name'], s['positions'], s['normals'], s['uvs'], s['triangles'], material)
        g.node(s['name'], mesh=m, parent=static if s['bone'] == 'Weapon' else nodes[s['bone']])
    g.node('ProjectileNode', np.array(muzzle, float), parent=static)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    g.write(out, root)
    job = ['# The job file of the model of %s. The model is in game units.' % name, 'scale = 1.0', '', '[materials]']
    job += ['%s = "Materials/Weapons/%s/%s%s.bgsm"' % (m, name, m, suffix) for m in used]
    job += ['', '[connect]', 'children = ["C-Receiver"]', '']
    if scope:
        # a shape on the bone `Weapon` is below the node NAME + Receiver
        job += ['# The sight part (the glass and the reticle) is on this node.', '[[connect.parent]]', 'name = "P-Scope"',
                'parent = "%s"' % (name + 'Receiver' if scope == 'Weapon' else scope),
                'translation = [0.0, 0.0, 0.0]', 'rotation = [1.0, 0.0, 0.0, 0.0]', 'scale = 1.0', '']
    with open(os.path.splitext(out)[0] + '.mesh.toml', 'w') as f:
        f.write('\n'.join(job) + '\n')
    return g, used


def power_of_two(n, limit=2048):
    p = 1
    while p < n and p < limit:
        p *= 2
    return p


def write_textures(folder, names, name, project, work, material_template, options, parts=None, dyes=None, suffix=''):
    """The textures and the material of each texture set. `dyes` is the dyes file of
    tools/d2dyes.py as tools/d2shade.py loads it (None: no pixel gets a dye). `suffix` is in the
    name of each file (the textures of a second shader of the same gun)."""
    from PIL import Image
    import d2shade
    Image.MAX_IMAGE_PIXELS = None
    tex_out = os.path.join(project, 'assets', 'Textures', 'Weapons', name)
    mat_out = os.path.join(project, 'assets', 'Materials', 'Weapons', name)
    for d in (work, tex_out, mat_out):
        os.makedirs(d, exist_ok=True)
    ao = float(options.get('occlusion', 0.5))
    specular_scale = float(options.get('specular', 0.9))
    for source, material in names.items():
        material = material + suffix
        files = {k: os.path.join(folder, '%s_%s.png' % (source, k)) for k in ('albedo', 'normal', 'gstack')}
        for k, p in files.items():
            if not os.path.exists(p):
                raise SystemExit('the texture file %s is not there' % p)
        albedo = Image.open(files['albedo']).convert('RGBA')
        size = (power_of_two(albedo.size[0]), power_of_two(albedo.size[1]))

        def fit(im):
            im = im.convert('RGBA')
            return np.asarray(im if im.size == size else im.resize(size, Image.LANCZOS), np.float32) / 255.0
        slots, covered = None, 0.0
        if dyes is not None and parts is not None:
            shapes = [s for s in parts['shapes'] if s['material'] == source and 'uvs' in s]
            # the name of a shape is REGION_PART_BONE: the part gives the dye slot
            slot_of = [dyes['part_slots'][s['source']][int(s['name'].split('_')[1])] for s in shapes]
            slots, covered = d2shade.slot_map(shapes, size, slot_of)
        result = d2shade.shade(fit(albedo), fit(Image.open(files['gstack'])), fit(Image.open(files['normal'])), slots, dyes)
        diffuse, specular, gloss, normal = d2shade.fallout4(result, ao, specular_scale)
        Image.fromarray(diffuse, 'RGB').save(os.path.join(work, material + '_d.png'))
        Image.fromarray(normal, 'RGB').save(os.path.join(work, material + '_n.png'))
        Image.fromarray(specular, 'L').save(os.path.join(work, material + '_spec.png'))
        Image.fromarray(gloss, 'L').save(os.path.join(work, material + '_gloss.png'))
        esx('texture', 'convert', os.path.join(work, material + '_d.png'), '--role', 'diffuse', '-o', os.path.join(tex_out, material + '_d.dds'), '--overwrite')
        esx('texture', 'convert', os.path.join(work, material + '_n.png'), '--role', 'normal', '-o', os.path.join(tex_out, material + '_n.dds'), '--overwrite')
        esx('texture', 'pack-channels', '--red', os.path.join(work, material + '_spec.png'), '--green', os.path.join(work, material + '_gloss.png'),
            '-o', os.path.join(tex_out, material + '_s.dds'), '--overwrite')
        tmp, nxt = os.path.join(work, material + '.bgsm'), os.path.join(work, material + '.next.bgsm')
        shutil.copyfile(material_template, tmp)
        for field, end in (('textures/diffuse', '_d'), ('textures/normal', '_n'), ('textures/smooth_specular', '_s')):
            esx('material', 'set', tmp, field, 'Weapons/%s/%s%s.dds' % (name, material, end), '-o', nxt, '--overwrite')
            os.replace(nxt, tmp)
        shutil.copyfile(tmp, os.path.join(mat_out, material + '.bgsm'))
        metal = result['metal']
        print('[model] %-12s <- %s  %dx%d (source %dx%d)  metal %.0f %% of the pixels, dye %.0f %%, specular mean %.2f, diffuse mean %s' % (
            material, source, size[0], size[1], albedo.size[0], albedo.size[1], 100.0 * float((metal > 0.5).mean()),
            100.0 * result['dyed'], float(specular.mean()) / 255.0, np.round(diffuse.reshape(-1, 3).mean(axis=0)).astype(int).tolist()))
        for slot, info in sorted(result['slots'].items()):
            print('[model]     slot %d (%s of the dye %d): %.0f %% of the pixels, base color %s, metal %.2f%s' % (
                slot, 'primary' if slot % 2 == 0 else 'secondary', slot // 2, 100.0 * info['pixels'],
                np.round(info['mean_base'], 3).tolist(), info['mean_metal'],
                '' if info['iridescence'] < 0 else '  (iridescence %d of the dye is not done)' % info['iridescence']))


def sight_fit(sight, parts):
    """{bone of the file: (Fallout 4 bone, M, largest error, vertices)}. M (3 x 4) puts a point of
    the space of the Destiny model (meters) into the local space of the Fallout 4 bone:
    local = M @ (x, y, z, 1). It is the least-squares fit of the opaque vertices of the bone
    (`reference` of the sight file) to the same vertices of the parts file."""
    shapes = {(s['source'], int(s['name'].split('_')[1]), s['source_bone']): s for s in parts['shapes']}
    pairs = {}
    for r in sight['reference']:
        s = shapes.get((r['source'], r['part'], r['bone']))
        if s is None or len(s['positions']) != len(r['positions']):
            continue
        a, b, _ = pairs.setdefault(r['bone'], ([], [], s['bone']))
        a.append(np.array(r['positions'], float))
        b.append(np.array(s['positions'], float))
    out = {}
    for bone, (a, b, target) in pairs.items():
        a, b = np.vstack(a), np.vstack(b)
        x = np.hstack([a, np.ones((len(a), 1))])
        m = np.linalg.lstsq(x, b, rcond=None)[0]
        error = float(np.abs(x @ m - b).max())
        if error > 0.01:
            raise SystemExit('the vertices of the bone %s in the sight file do not fit the parts file (%.3f units)' % (bone, error))
        out[bone] = (target, m.T, error, len(a))
    return out


def uv_point(shape, uv):
    """The point of a shape (positions, uvs, triangles) at a texture coordinate, or None."""
    p, t = np.array(shape['positions'], float), np.array(shape['uvs'], float)
    for a, b, c in shape['triangles']:
        m = np.array([t[b] - t[a], t[c] - t[a]]).T
        if abs(np.linalg.det(m)) < 1e-12:
            continue
        v, w = np.linalg.solve(m, np.array(uv, float) - t[a])
        if v >= -1e-9 and w >= -1e-9 and v + w <= 1 + 1e-9:
            return p[a] + v * (p[b] - p[a]) + w * (p[c] - p[a])
    return None


def effect_material(path, work, texture, scale, two_sided):
    """An effect material: one texture with alpha, no light of the scene, alpha blending."""
    tmp = os.path.join(work, os.path.basename(path))
    nxt = os.path.splitext(tmp)[0] + '.next.bgem'
    esx('material', 'create', 'bgem', '-o', tmp, '--overwrite')
    fields = (('textures/base', texture),
              # blending on, source alpha, 1 - source alpha
              ('alpha_blend_mode_0', '1'), ('alpha_blend_mode_1', '6'), ('alpha_blend_mode_2', '7'),
              ('z_buffer_write', 'false'), ('two_sided', 'true' if two_sided else 'false'), ('non_occluder', 'true'),
              ('effect_lighting_enabled', 'false'), ('base_color_scale', repr(float(scale))))
    for field, value in fields:
        esx('material', 'set', tmp, field, value, '-o', nxt, '--overwrite')
        os.replace(nxt, tmp)
    shutil.copyfile(tmp, path)


def sight_template(options, name, data, work, out, origins):
    """The template mesh of the sight: the vanilla mesh of `template` with the names and the
    texture paths of this weapon. `esx nif import` keeps each block of a template that it does
    not fill, so the output mesh has these names and no path of a vanilla texture. A template
    shape also keeps its place and its 16-bit vertex values, so each of the two shapes gets
    the center of its new geometry as its place (`origins`): a vertex is then near 0, where
    such a value has a small step (the step is 1/64 unit at 20 units from the place)."""
    if not data:
        raise SystemExit('the sight needs --data: the template mesh %s is in the archives of the game' % options['template'])
    source = os.path.join(work, 'sight_template_source.nif')
    esx('--data', data, 'resource', 'extract', options['template'].replace('/', '\\'), '-o', source, '--overwrite')
    report = esx('nif', 'shapes', source)['data']
    edits = ['blocks/%d/NiNode/Name=%sSight' % (report['root'], name)]
    for shape, new, texture, origin in zip(options['template_shapes'], ('Glass', 'Reticle'), ('SightGlass_d', 'Reticle_d'), origins):
        found = [x for x in report['shapes'] if x['name'] == shape]
        if len(found) != 1 or found[0]['shader']['kind'] != 'BSEffectShaderProperty':
            raise SystemExit('the template mesh %s has no shape %s with an effect shader' % (options['template'], shape))
        shader = 'blocks/%d/BSEffectShaderProperty/' % found[0]['shader']['block']
        edits += ['blocks/%d/BSTriShape/Name=%s' % (found[0]['block'], new),
                  'blocks/%d/BSTriShape/Transform/Translation=%s' % (found[0]['block'], json.dumps([round(float(x), 4) for x in origin])),
                  'blocks/%d/BSTriShape/Transform/Rotation=[1,0,0,0,1,0,0,0,1]' % found[0]['block'],
                  shader + 'Source Texture=textures\\Weapons\\%s\\%s.dds' % (name, texture),
                  shader + 'Env Map Texture=', shader + 'Normal Texture=', shader + 'Env Mask Texture=']
    args = []
    for e in edits:
        args += ['--edit', e]
    esx('nif', 'set', source, *args, '-o', out, '--overwrite')


def write_sight(options, sight, parts, template, name, project, work, folder, base, aim=None, data=None):
    """The sight part of the weapon: the model, the two textures and the two materials. Returns
    the Fallout 4 bone of the part. `folder` has the texture plates, and `base` is the folder of
    the sight file."""
    from PIL import Image, ImageDraw
    import d2shade
    entity = next((e for e in sight['sights'] if e['source'] == options['source']), None)
    if entity is None:
        raise SystemExit('the sight file has no entity %s' % options['source'])
    fit = sight_fit(sight, parts)
    scale = float(parts['scale'])
    tex_out = os.path.join(project, 'assets', 'Textures', 'Weapons', name)
    mat_out = os.path.join(project, 'assets', 'Materials', 'Weapons', name)
    for d in (work, tex_out, mat_out):
        os.makedirs(d, exist_ok=True)

    # the glass: each layer is a material of the entity, and the layers are one shape
    layers, glass, bone = [], {'positions': [], 'normals': [], 'uvs': [], 'triangles': []}, None
    for layer in options['glass']:
        found = [s for s in entity['shapes'] if s['material'] == layer['material'] and s['stage'] == 'transparent']
        if not found:
            raise SystemExit('the entity %s has no glass part with the material %s' % (options['source'], layer['material']))
        for s in found:
            if s['bone'] not in fit:
                raise SystemExit('no opaque part of the gun is on the bone %s of the glass' % s['bone'])
            target, m, error, count = fit[s['bone']]
            if bone not in (None, target):
                raise SystemExit('the glass is on two bones (%s and %s)' % (bone, target))
            bone = target
            turn = m[:, :3] / np.linalg.norm(m[:, :3], axis=0)
            first = len(glass['positions'])
            local = np.hstack([np.array(s['positions'], float), np.ones((len(s['positions']), 1))]) @ m.T
            glass['positions'] += local.tolist()
            glass['normals'] += (np.array(s['normals'], float) @ turn.T).tolist()
            glass['uvs'] += s['uvs']
            glass['triangles'] += [[i + first for i in t] for t in s['triangles']]
            layers.append((layer, s))
            print('[model] sight: the glass part with the material %s is on %s (%d vertices; the fit of %d vertices has an error of %.5f units)' % (
                s['material'], target, len(s['positions']), count, error))
    rest = template.rest_in_weapon(bone)
    axes = rest[:3, :3]                                   # weapon direction = axes @ bone direction

    def weapon(points):
        return np.asarray(points, float) @ axes.T + rest[:3, 3]

    # the reticle: the quad of the stage `reticle`, at the place of the glass that `center` gives
    ro = options['reticle']
    quad = next((s for s in entity['shapes'] if s['stage'] == 'reticle' and s['material'] == ro['material']), None)
    if quad is None:
        raise SystemExit('the entity %s has no part of the stage reticle with the material %s' % (options['source'], ro['material']))
    first_layer = {'positions': glass['positions'][:len(layers[0][1]['positions'])], 'uvs': layers[0][1]['uvs'], 'triangles': layers[0][1]['triangles']}
    center = uv_point(first_layer, ro.get('center', [0.5, 0.5]))
    if center is None:
        raise SystemExit('the glass has no point at the texture coordinate %s' % ro.get('center'))
    center_w = weapon(center)
    # the plane of the glass in weapon space, to put the quad a little before it (to the eye, -Y)
    gw = weapon(first_layer['positions'])
    normal = np.linalg.svd(gw - gw.mean(axis=0))[2][2]
    # The size. The vertex shader of the reticle puts the quad at `distance` meters before the
    # camera, so the player sees it at a fixed angle. The quad on the glass has the same angle
    # from the eye point of the clip in the sights (`eye`, weapon space). With no `distance` the
    # quad has its own size, as a part of the gun.
    meters = np.array(quad['positions'], float)[:, :2]      # x to the right, y up
    grow = float(ro.get('scale', 1.0))
    if ro.get('distance') and ro.get('eye'):
        far = float(center_w[1] - ro['eye'][1])             # along the weapon axis, the view direction in the sights
        note = 'the angle of the quad at %.2f m (%.2f x %.2f degrees), seen from the eye point at %.2f units' % (
            float(ro['distance']), *np.degrees(2.0 * np.arctan(np.ptp(meters, axis=0) / 2.0 / float(ro['distance']))), far)
    else:
        far, note = None, 'the size of the quad of the file'
    for _ in range(2):                                      # the second time with the distance of the quad, not of the glass
        corners = meters * (far / float(ro['distance']) if far else scale) * grow
        quad_w = center_w + np.stack([corners[:, 0], np.zeros(len(corners)), corners[:, 1]], axis=1)
        on_glass = gw.mean(axis=0)[1] - ((quad_w[:, 0] - gw.mean(axis=0)[0]) * normal[0] + (quad_w[:, 2] - gw.mean(axis=0)[2]) * normal[2]) / normal[1]
        quad_w[:, 1] = float(on_glass.min()) - float(ro.get('gap', 0.02))
        if far:
            far = float(quad_w[0, 1] - ro['eye'][1])
    quad_local = (quad_w - rest[:3, 3]) @ axes
    quad_normals = np.tile(np.array([0.0, -1.0, 0.0]) @ axes, (len(corners), 1))
    print('[model] sight: the reticle is %.3f x %.3f units (%s), its center is at %s of weapon space (on the glass at the texture coordinate %s)' % (
        np.ptp(corners[:, 0]), np.ptp(corners[:, 1]), note, np.round(center_w, 3).tolist(), list(ro.get('center', [0.5, 0.5]))))
    if aim is not None:
        off = float(np.hypot(aim[0] - center_w[0], aim[2] - center_w[2]))
        print('[model] sight: the aim point of [sight] is %s: %.3f units from the center of the reticle%s' % (
            list(aim), off, '' if off <= 0.02 else '. THE CLIPS IN THE SIGHTS DO NOT AIM THROUGH THE RETICLE: give point = [%.2f, %.2f, %.2f]' % tuple(center_w)))

    g = Model()
    root = g.node(name + 'Sight')
    g.node('Glass', mesh=g.mesh('Glass', np.array(glass['positions']), np.array(glass['normals']), glass['uvs'], glass['triangles'], 'SightGlass'), parent=root)
    g.node('Reticle', mesh=g.mesh('Reticle', quad_local, quad_normals, quad['uvs'], quad['triangles'], 'Reticle'), parent=root)
    out = os.path.join(project, 'meshes', 'Weapons', name, name + 'Sight.glb')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    g.write(out, root)
    sight_template(options, name, data, work, os.path.splitext(out)[0] + '.template.nif',
                   (np.array(glass['positions']).mean(axis=0), quad_local.mean(axis=0)))
    job = ['# The job file of the sight of %s: the glass and the reticle. The model is in game units.' % name,
           '# The template is the vanilla mesh %s' % options['template'],
           '# with the names and the texture paths of this weapon (tools/d2model.py makes it). Two of',
           '# its shapes have an effect shader with alpha blending, and esx makes no new effect',
           '# shader: they get the geometry of the model. Each other shape of it goes away.',
           'scale = 1.0', 'template_file = "%sSight.template.nif"' % name, 'unmatched = "remove"', '', '[materials]',
           'SightGlass = "Materials/Weapons/%s/SightGlass.bgem"' % name, 'Reticle = "Materials/Weapons/%s/Reticle.bgem"' % name, '',
           '[connect]', 'children = ["C-Scope"]', '']
    with open(os.path.splitext(out)[0] + '.mesh.toml', 'w') as f:
        f.write('\n'.join(job) + '\n')

    # the texture of the glass: the color of each layer where its triangles are
    plate = entity['plate_set']
    albedo = np.asarray(Image.open(os.path.join(folder, plate + '_albedo.png')).convert('RGBA'), np.float32) / 255.0
    gstack = np.asarray(Image.open(os.path.join(folder, plate + '_gstack.png')).convert('RGBA').resize(albedo.shape[1::-1]), np.float32) / 255.0
    h, w = albedo.shape[:2]
    linear = d2shade.srgb_to_linear(albedo[..., :3])
    color, alpha = np.zeros((h, w, 3), np.float32), np.zeros((h, w), np.float32)
    for layer, s in layers:
        mask = Image.new('L', (w, h), 0)
        draw = ImageDraw.Draw(mask)
        uv = np.array(s['uvs'], float) * [w, h]
        for t in s['triangles']:
            draw.polygon([tuple(uv[i]) for i in t], fill=255, outline=255, width=3)
        inside = np.asarray(mask) > 0
        value = sum(linear[..., i:i + 1] * np.array(layer[key], np.float32) for i, key in enumerate(('red', 'green', 'blue')) if key in layer)
        # `alpha` of a layer (default 1): the picture is color x a + scene x (1 - alpha x a), with a
        # = the green value of the gstack plate. Fallout 4 blends texture x scale x A + scene x
        # (1 - A): A = alpha x a, and the color is color / alpha.
        k = float(layer.get('alpha', 1.0))
        color[inside] = (value / k)[inside]
        alpha[inside] = (k * gstack[..., 1])[inside]
    peak = max(1.0, float(color.max()))                 # a color above 1 goes into the scale of the material
    glass_scale = peak * float(options.get('glass_scale', 1.0))
    image = np.dstack([d2shade.linear_to_srgb(np.clip(color / peak, 0.0, 1.0)), np.clip(alpha, 0.0, 1.0)])
    Image.fromarray((image * 255.0 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(work, 'SightGlass_d.png'))
    esx('texture', 'convert', os.path.join(work, 'SightGlass_d.png'), '--role', 'diffuse', '--texture-format', options.get('texture_format', 'bc7'),
        '-o', os.path.join(tex_out, 'SightGlass_d.dds'), '--overwrite')
    effect_material(os.path.join(mat_out, 'SightGlass.bgem'), work, 'Weapons/%s/SightGlass_d.dds' % name, glass_scale, True)
    print('[model] sight: SightGlass_d %dx%d, %.1f %% of the pixels have alpha above 0.02, the largest color value is %.2f, color scale %.2f' % (
        w, h, 100.0 * float((alpha > 0.02).mean()), peak, glass_scale))

    # the texture of the reticle. Destiny: picture = blue x color + scene x (1 - alpha x blue), with
    # color = red x RED + green x GREEN. Fallout 4 blends texture x scale x a + scene x (1 - a):
    # a = alpha x blue, texture = color / peak, scale = peak / alpha.
    file = next(t['file'] for t in sight['materials'][ro['material']]['ps_textures'] if t['tag'] == ro['texture'])
    pixels = np.asarray(Image.open(os.path.join(base, file)).convert('RGBA'), np.float32) / 255.0
    linear = d2shade.srgb_to_linear(pixels[..., :3])
    color = sum(linear[..., i:i + 1] * np.array(ro[key], np.float32) for i, key in enumerate(('red', 'green', 'blue')) if key in ro)
    if ro.get('limit'):
        # no value above this one: a value above white makes bloom around the reticle
        color = np.minimum(color, float(ro['limit']))
    peak = max(1.0, float(color.max()))
    k = float(ro.get('alpha', 1.0))
    image = np.dstack([d2shade.linear_to_srgb(np.clip(color / peak, 0.0, 1.0)), np.clip(k * linear[..., 2], 0.0, 1.0)])
    Image.fromarray((image * 255.0 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(work, 'Reticle_d.png'))
    esx('texture', 'convert', os.path.join(work, 'Reticle_d.png'), '--role', 'diffuse', '--texture-format', options.get('texture_format', 'bc7'),
        '-o', os.path.join(tex_out, 'Reticle_d.dds'), '--overwrite')
    reticle_scale = peak / k * float(ro.get('brightness', 1.0))
    effect_material(os.path.join(mat_out, 'Reticle.bgem'), work, 'Weapons/%s/Reticle_d.dds' % name, reticle_scale, False)
    print('[model] sight: Reticle_d %dx%d, the largest color value is %.2f, color scale %.2f' % (pixels.shape[1], pixels.shape[0], peak, reticle_scale))
    print('[model] %s: the sight on %s, template %s' % (os.path.relpath(out, project), bone, options['template']))
    return bone


def main():
    import ba2
    ap = argparse.ArgumentParser(description='Make the Fallout 4 model, the textures, the materials and the sight of a gun in an esx project.')
    ap.add_argument('file', help='the first-person file (.glb) of d2x or m2x')
    ap.add_argument('--set', required=True, help='the set file of the weapon: its table [model]')
    ap.add_argument('--parts', help='the parts file of the converter (default: data/destiny/port/work/WEAPON/parts.json)')
    ap.add_argument('--mod', help='the name of the mod: the project is data/mods/NAME (default: `name` of [model])')
    ap.add_argument('--project', help='the folder of the esx project, in place of --mod')
    ap.add_argument('--data', help='the Data folder of Fallout 4, for the material file of the template weapon and the '
                                   'template mesh of the sight (default: the setting fo4_data)')
    ap.add_argument('--material', help='the material file of the template weapon, in place of --data')
    ap.add_argument('--textures', help='the folder with the texture sets (default: the folder `textures` beside the file)')
    ap.add_argument('--work', help='the folder for the work files (default: the folder `model` beside the parts file)')
    a = ap.parse_args()
    with open(a.set, 'rb') as f:
        data = tomllib.load(f)
    model = data['model']
    name = model['name']
    if a.mod and a.project:
        raise SystemExit('give --mod NAME or --project FOLDER, not the two')
    a.project = a.project or paths.data('mods', a.mod or name)
    a.parts = a.parts or paths.data('destiny', 'port', 'work', os.path.splitext(os.path.basename(a.file))[0].replace('_first_person', ''), 'parts.json')
    if not os.path.isfile(a.parts):
        raise SystemExit('the parts file %s is not there (the step `parts` of d2fo4.py makes it)' % a.parts)
    a.data = a.data or paths.setting('fo4_data')
    template = Template(data.get('template', 'revolver44'))
    parts = json.load(open(a.parts))
    names = dict(model.get('materials', {}))
    for s in parts['shapes']:
        names.setdefault(s['material'], s['material'])
    work = a.work or os.path.join(os.path.dirname(os.path.abspath(a.parts)), 'model')
    os.makedirs(work, exist_ok=True)
    material = a.material
    if material is None:
        if not a.data:
            raise SystemExit('give --data (the Data folder of Fallout 4; or the setting fo4_data) or --material FILE.bgsm')
        material = os.path.join(work, 'template.bgsm')
        with open(material, 'wb') as f:
            f.write(ba2.Ba2(os.path.join(a.data, 'Fallout4 - Materials.ba2')).read(template.data['material']))
    folder = a.textures or os.path.join(os.path.dirname(os.path.abspath(a.file)), 'textures')
    scope = None
    if model.get('sight'):
        # the glass of the sight and the reticle: the file of tools/d2reticle.py, beside the file of the gun
        base = os.path.dirname(os.path.abspath(a.file))
        sight = json.load(open(os.path.join(base, model['sight']['file'])))
        scope = write_sight(model['sight'], sight, parts, template, name, a.project, work, folder, base, data.get('sight', {}).get('point'), a.data)
    out = os.path.join(a.project, 'meshes', 'Weapons', name, name + '.glb')
    g, used = write_model(parts, template, name, names, model['muzzle'], out, scope=scope)
    print('[model] %s: %d nodes, %d shapes, %d vertices, materials %s' % (
        os.path.relpath(out, a.project), len(g.nodes), len(g.meshes), sum(len(s['positions']) for s in parts['shapes']), ', '.join(used)))
    import d2shade
    dyes = None
    if model.get('dyes'):
        # the dyes file of tools/d2dyes.py, beside the file of the gun
        dyes = d2shade.load_dyes(os.path.join(os.path.dirname(os.path.abspath(a.file)), model['dyes']))
        print('[model] dyes: %s' % ', '.join('%s "%s" (dye %d)' % (d['channel'], d['name'], d['dye_index']) for d in dyes['dyes'] if d))
    write_textures(folder, {k: v for k, v in names.items() if v in used}, name, a.project, work, material, model, parts, dyes)
    # More shaders of the gun ([model.shaders]: NAME = the dyes file of tools/d2dyes.py with
    # --shader). Each one has its own textures and materials (the suffix _NAME) and its own
    # model file (the name of the gun and NAME), so it can be a part of the weapon.
    for key, file in model.get('shaders', {}).items():
        shader = d2shade.load_dyes(os.path.join(os.path.dirname(os.path.abspath(a.file)), file))
        out = os.path.join(a.project, 'meshes', 'Weapons', name, name + key + '.glb')
        write_model(parts, template, name, names, model['muzzle'], out, '_' + key, scope)
        print('[model] %s: the shader %s' % (os.path.relpath(out, a.project), shader.get('shader')))
        write_textures(folder, {k: v for k, v in names.items() if v in used}, name, a.project, work, material, model, parts, shader, '_' + key)


if __name__ == '__main__':
    main()
