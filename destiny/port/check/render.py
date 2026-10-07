"""Render the source (Destiny hands and gun) and the result (Fallout 4 hands and gun) of a clip.

./port destiny check render --glb FILE.glb --clip CLIP --poses OUT/WPNReload.hkx --parts WORK/parts.json \
    --out DIR --frames 0,30,60 [--views fp,r_thumb,...] [--kinds src,fo4]
sh destiny/port/check/bl.sh destiny/port/check/render.py -- ...     (the same program with no ./port)

The program runs in Blender. WORK is the work folder of the weapon
(data/destiny/port/work/NAME) and OUT is the folder of its clips (data/destiny/port/out/NAME,
or the animation folder of the mod project).

The scene is in Fallout 4 world space (game units). The source is the file as Blender reads
it, with its own skin and its clip, below an object that has the change of axes, the scale
and the place of tools/d2rig.py. The result is the vanilla first-person arm meshes of
Fallout 4 with the poses of the clip (an HKX file, or a pose file of the retarget), and the gun
shapes of the parts file on the Fallout 4 weapon bones. The two pictures of a frame have the
same camera.

Views: fp is the camera bone of the result (the first-person camera). The other views look
at one hand: r_thumb, r_back, r_front, r_under, r_palm, l_thumb, l_back, l_front, l_under,
l_palm (the camera turns with the hand). gun_left, gun_right, gun_top, gun_back and gun_under
look at the grip from a side of the gun (the camera turns with the gun).
A picture is DIR/CLIP_fFRAME_VIEW_KIND.png; KIND is src, fo4 or mix (the two at one place).

A set file can have rules for the clips of the file (the tables [gun] and [compose];
tools/d2bake.py). d2fo4.py writes them to clips.json beside the parts file. With that file
the source has the pose that tools/d2bake.py calculates for each frame, not the action of
the file.
"""
import argparse
import json
import math
import os
import sys
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), 'tools')
sys.path.insert(0, TOOLS)
import fo4clip  # noqa: E402
import d2rig  # noqa: E402
import d2bake  # noqa: E402
from fo4mesh import SkinnedMesh, Helpers  # noqa: E402

BODY_BONES = ('b_pedestal', 'b_pelvis', 'b_utility', 'b_spine', 'b_neck', 'b_head', 'b_jaw', 'b_l_clav', 'b_r_clav',
              'b_l_thigh', 'b_r_thigh', 'b_l_calf', 'b_r_calf', 'b_l_foot', 'b_r_foot', 'b_l_toe', 'b_r_toe',
              'b_l_brow', 'b_r_brow', 'b_l_eye', 'b_r_eye', 'b_l_upper', 'b_r_upper', 'b_l_lower', 'b_r_lower',
              'b_l_shoulder_twist', 'b_r_shoulder_twist')

# view -> (hand, the point that the camera looks at, the direction to the camera, the up direction), in
# the axes of the Fallout 4 hand bone (+X to the fingers, -Y the palm side; the thumb is at -Z of
# the right hand and at +Z of the left hand), and the distance
VIEWS = {
    'r_thumb': ('R', (6.0, -1.0, 0.0), (0.15, 0.45, -1.0), (0.0, 1.0, 0.0), 26.0),
    'r_back': ('R', (6.0, -1.0, 0.0), (0.1, 1.0, -0.25), (1.0, 0.0, 0.0), 26.0),
    'r_front': ('R', (7.0, -1.5, 0.0), (1.0, 0.25, -0.35), (0.0, 1.0, 0.0), 26.0),
    'r_under': ('R', (7.0, -1.5, 0.0), (0.35, -0.6, 1.0), (0.0, 1.0, 0.0), 26.0),
    'l_thumb': ('L', (6.0, -1.0, 0.0), (0.15, 0.45, 1.0), (0.0, 1.0, 0.0), 26.0),
    'l_back': ('L', (6.0, -1.0, 0.0), (0.1, 1.0, 0.25), (1.0, 0.0, 0.0), 26.0),
    'l_front': ('L', (7.0, -1.5, 0.0), (1.0, 0.25, 0.35), (0.0, 1.0, 0.0), 26.0),
    'l_under': ('L', (7.0, -1.5, 0.0), (0.35, -0.6, -1.0), (0.0, 1.0, 0.0), 26.0),
    'l_palm': ('L', (6.0, -1.0, 0.0), (0.2, -1.0, 0.3), (1.0, 0.0, 0.0), 26.0),
    'r_palm': ('R', (6.0, -1.0, 0.0), (0.2, -1.0, -0.3), (1.0, 0.0, 0.0), 26.0),
}


# view -> (the point that the camera looks at, the place of the camera, the up direction), in Fallout 4
# weapon space (+Y to the muzzle, +Z up, +X to the right of the gun)
GUN_VIEWS = {
    'gun_left': ((0.0, 0.0, -3.0), (-34.0, -6.0, 6.0), (0.0, 0.0, 1.0)),
    'gun_right': ((0.0, 0.0, -3.0), (34.0, -6.0, 6.0), (0.0, 0.0, 1.0)),
    'gun_top': ((0.0, 0.0, -3.0), (-3.0, -8.0, 36.0), (0.0, 1.0, 0.0)),
    'gun_back': ((0.0, 0.0, -3.0), (-5.0, -36.0, 8.0), (0.0, 0.0, 1.0)),
    'gun_under': ((0.0, 0.0, -3.0), (4.0, -8.0, -36.0), (0.0, 1.0, 0.0)),
}


def to_matrix(m):
    return Matrix([list(r) for r in m])


def look_at(camera, eye, target, up):
    z = (Vector(eye) - Vector(target)).normalized()
    x = Vector(up).cross(z)
    if x.length < 1e-6:
        x = Vector((1.0, 0.0, 0.0)).cross(z)
    x.normalize()
    y = z.cross(x)
    m = Matrix.Identity(4)
    for i in range(3):
        m[i][0], m[i][1], m[i][2], m[i][3] = x[i], y[i], z[i], eye[i]
    camera.matrix_world = m


def setup_scene(resolution):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.image_settings.file_format = 'PNG'
    engines = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
    world = bpy.data.worlds.new('check')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.36, 0.39, 0.44, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = 0.55
    scene.world = world
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    for name, value in (('use_raytracing', True), ('use_shadows', True), ('use_gtao', True), ('taa_render_samples', 32)):
        if hasattr(scene.eevee, name):
            setattr(scene.eevee, name, value)
    camera = bpy.data.objects.new('check_camera', bpy.data.cameras.new('check_camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.sensor_width = 36.0
    camera.data.clip_start = 0.5
    camera.data.clip_end = 5000.0
    # two lights that turn with the camera, so each view has light on the side that it shows
    for name, rotation, energy in (('key', (math.radians(-35), math.radians(40), 0.0), 2.6),
                                   ('fill', (math.radians(25), math.radians(-50), 0.0), 0.7)):
        light = bpy.data.lights.new(name, 'SUN')
        light.energy = energy
        light.angle = math.radians(3)
        obj = bpy.data.objects.new(name, light)
        obj.parent = camera
        obj.rotation_euler = rotation
        scene.collection.objects.link(obj)
    render = scene.render
    render.use_stamp = True
    for flag in ('use_stamp_date', 'use_stamp_time', 'use_stamp_render_time', 'use_stamp_frame', 'use_stamp_scene',
                 'use_stamp_camera', 'use_stamp_lens', 'use_stamp_filename', 'use_stamp_marker',
                 'use_stamp_sequencer_strip', 'use_stamp_memory', 'use_stamp_hostname', 'use_stamp_frame_range'):
        if hasattr(render, flag):
            setattr(render, flag, False)
    render.use_stamp_note = True
    render.stamp_font_size = max(13, resolution[1] // 34)
    render.stamp_background = (0, 0, 0, 0.6)
    render.stamp_foreground = (1, 1, 1, 1)
    return scene, camera


def flat_material(name, color, alpha=1.0, roughness=0.6):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        mat.surface_render_method = 'BLENDED' if hasattr(mat, 'surface_render_method') else mat.surface_render_method
    return mat


class Source:
    """The file as Blender reads it, in Fallout 4 world space."""

    def __init__(self, path, clip, camera_place, hide=(), rules=None):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        self.objects = [o for o in bpy.data.objects if o not in before]
        self.armature = [o for o in self.objects if o.type == 'ARMATURE'][0]
        self.meshes = [o for o in self.objects if o.type == 'MESH' and o.vertex_groups]
        for o in self.objects:
            if o.type == 'MESH' and (not o.vertex_groups or any(h in o.name for h in hide)):
                o.hide_render = True
        self.meshes = [o for o in self.meshes if not o.hide_render]
        for obj in self.meshes:
            hidden = {g.index for g in obj.vertex_groups if g.name.startswith(BODY_BONES)}
            if not hidden:
                continue
            keep = obj.vertex_groups.new(name='fp_visible')
            for vertex in obj.data.vertices:
                if sum(g.weight for g in vertex.groups if g.group in hidden) < 0.5:
                    keep.add([vertex.index], 1.0, 'REPLACE')
            mask = obj.modifiers.new('fp_mask', 'MASK')
            mask.vertex_group = 'fp_visible'
        # Blender has the file with +Z up and -Y forward: a half turn about Z gives the Fallout 4 axes
        root = bpy.data.objects.new('source_root', None)
        bpy.context.scene.collection.objects.link(root)
        offset = Vector(camera_place) - Vector(d2rig.AXES @ np.array(d2rig.EYE)) * d2rig.SCALE
        root.matrix_world = Matrix.Translation(offset) @ Matrix.Rotation(math.pi, 4, 'Z') @ Matrix.Scale(d2rig.SCALE, 4)
        for o in self.objects:
            if o.parent is None:
                o.parent = root
        for bone in self.armature.pose.bones:
            bone.matrix_basis.identity()
        self.baked = None
        if rules:
            # the pose of each frame from tools/d2bake.py, with the rules of the set file
            from glb import Glb
            rig = d2bake.Rig(Glb(path), rules)
            self.baked = rig.bake(clip)[0]
            rest = rig.world(*[x[None] for x in rig.rest_local()])[0]
            self.rest_inverse = np.linalg.inv(rest)
            self.slots = rig.index
            if self.armature.animation_data is not None:
                self.armature.animation_data.action = None
            self.first = 0
            return
        action = bpy.data.actions[clip]
        if self.armature.animation_data is None:
            self.armature.animation_data_create()
        self.armature.animation_data.action = action
        if hasattr(self.armature.animation_data, 'action_slot') and action.slots:
            self.armature.animation_data.action_slot = action.slots[0]
        self.first = int(round(action.frame_range[0]))

    def set_frame(self, frame):
        """With rules: the pose of a frame. Blender has the file with +Z up (x, y, z of the file are
        x, -z, y here), so the matrix that moves a bone from its rest place is C D C^-1."""
        if self.baked is None:
            return
        world = self.baked[min(frame, len(self.baked) - 1)]
        c = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        posed = {}
        for bone in self.armature.pose.bones:                         # a parent comes before its children
            k = self.slots.get(bone.name)
            rest = bone.bone.matrix_local
            if k is None:
                posed[bone.name] = (posed[bone.parent.name] @ bone.parent.bone.matrix_local.inverted() @ rest) if bone.parent else rest.copy()
            else:
                posed[bone.name] = c @ to_matrix(world[k] @ self.rest_inverse[k]) @ c.inverted() @ rest
            if bone.parent:
                rest_local = bone.parent.bone.matrix_local.inverted() @ rest
                bone.matrix_basis = rest_local.inverted() @ posed[bone.parent.name].inverted() @ posed[bone.name]
            else:
                bone.matrix_basis = rest.inverted() @ posed[bone.name]

    def show(self, on):
        for o in self.meshes:
            o.hide_render = not on

    def bone_world(self, name):
        """World matrix of a bone of the source for the current frame (Fallout 4 world space, Blender bone axes)."""
        return self.armature.matrix_world @ self.armature.pose.bones[name].matrix


class Result:
    """The Fallout 4 arm meshes and the gun shapes of the parts file."""

    def __init__(self, poses_path, parts_path, rig, textured=True):
        self.poses, self.names = fo4clip.load_poses(poses_path)
        self.idx = {n: i for i, n in enumerate(self.names)}
        helpers = Helpers(rig, self.names)
        self.arms = []
        self.objects = []
        for f, color in (('1stpersonmalebody.glb', (0.20, 0.26, 0.42)), ('1stpersonmalehands.glb', (0.78, 0.56, 0.45))):
            sm = SkinnedMesh(os.path.join(rig, f))
            mesh = bpy.data.meshes.new(sm.name)
            # The skin bone Chest_Rear_Skin is not a bone of the animation, so the part of the sleeve
            # at the shoulder has no correct place here (it is a spike with a vanilla clip too): not drawn.
            tris = sm.tris
            if 'Chest_Rear_Skin' in sm.joint_names:
                j = sm.joint_names.index('Chest_Rear_Skin')
                loose = ((sm.joints == j) & (sm.weights > 0.02)).any(1)
                tris = tris[~loose[tris].any(1)]
            mesh.from_pydata([tuple(v) for v in sm.verts], [], [tuple(t) for t in tris])
            mesh.update()
            ob = bpy.data.objects.new(sm.name, mesh)
            bpy.context.scene.collection.objects.link(ob)
            mesh.materials.append(flat_material('fo4_' + sm.name, color))
            for p in mesh.polygons:
                p.use_smooth = True
            self.arms.append((sm, ob, sm.rules(self.names, helpers)))
            self.objects.append(ob)
        parts = json.load(open(parts_path))
        self.gun = []
        for s in parts['shapes']:
            p = np.array(s['positions'])
            mesh = bpy.data.meshes.new(s['name'])
            mesh.from_pydata([tuple(v) for v in p], [], [tuple(t) for t in s['triangles']])
            mesh.update()
            mat = bpy.data.materials.get(s.get('material') or '') if textured else None
            if mat is not None and 'uvs' in s:
                uv = np.array(s['uvs'])
                layer = mesh.uv_layers.new(name='UVMap')
                loops = np.zeros(len(mesh.loops), np.int32)
                mesh.loops.foreach_get('vertex_index', loops)
                co = np.stack([uv[loops, 0], 1.0 - uv[loops, 1]], axis=1)
                layer.data.foreach_set('uv', co.reshape(-1))
            else:
                mat = flat_material('gun_' + s['name'], (0.30, 0.31, 0.33))
            mesh.materials.append(mat)
            for poly in mesh.polygons:
                poly.use_smooth = True
            ob = bpy.data.objects.new('fo4_' + s['name'], mesh)
            bpy.context.scene.collection.objects.link(ob)
            self.gun.append((p, ob, self.idx[s['bone']]))
            self.objects.append(ob)

    def set_frame(self, f):
        pw = self.poses[f]
        for sm, ob, rules in self.arms:
            ob.data.vertices.foreach_set('co', sm.skinned(pw, rules).reshape(-1))
            ob.data.update()
        for p, ob, bi in self.gun:
            m = pw[bi]
            ob.data.vertices.foreach_set('co', (p @ m[:3, :3].T + m[:3, 3]).reshape(-1))
            ob.data.update()
        return pw

    def show(self, on):
        for o in self.objects:
            o.hide_render = not on


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--glb', required=True)
    ap.add_argument('--clip', required=True)
    ap.add_argument('--poses', required=True)
    ap.add_argument('--parts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--frames', default='0')
    ap.add_argument('--views', default='fp')
    ap.add_argument('--kinds', default='src,fo4')
    ap.add_argument('--lens', type=float, default=21.0, help='the lens of the first-person view on a 36 mm sensor (21: 81 degrees)')
    ap.add_argument('--close-lens', type=float, default=50.0)
    ap.add_argument('--size', default='960x540')
    ap.add_argument('--close-size', default='720x720')
    ap.add_argument('--rig', default=fo4clip.PORT_RIG, help='the rig folder of fnv (default: data/fnv/rig)')
    ap.add_argument('--template', default='revolver44')
    ap.add_argument('--template-rig', default=paths.data('destiny', 'port', 'rig'),
                    help='the folder with the clips of the template weapon (default: data/destiny/port/rig)')
    ap.add_argument('--hide', action='append', default=[], help='text in the name of a mesh of the source that is not shown')
    ap.add_argument('--plain-gun', action='store_true', help='the gun of the result with no texture')
    ap.add_argument('--tag')
    a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
    os.makedirs(a.out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30
    size = tuple(int(v) for v in a.size.split('x'))
    close = tuple(int(v) for v in a.close_size.split('x'))
    scene, camera = setup_scene(size)
    # the eye point of the source is at the place of the camera bone of the template weapon (tools/d2bake.py).
    # The source comes first: the gun of the result uses the materials of the file.
    rules = d2bake.load_rules(os.path.join(os.path.dirname(os.path.abspath(a.parts)), 'clips.json'))
    source = Source(a.glb, a.clip, d2bake.camera_place(a.template, a.template_rig), a.hide, rules)
    result = Result(a.poses, a.parts, a.rig, not a.plain_gun)
    n = result.poses.shape[0]
    frames = list(range(n)) if a.frames == 'all' else [min(int(x), n - 1) for x in a.frames.split(',')]
    tag = a.tag or a.clip
    kinds = a.kinds.split(',')
    count = 0
    for f in frames:
        scene.frame_set(source.first + f)
        source.set_frame(f)
        pw = result.set_frame(f)
        bpy.context.view_layer.update()
        for view in a.views.split(','):
            if view == 'fp':
                scene.render.resolution_x, scene.render.resolution_y = size
                camera.data.lens = a.lens
                camera.matrix_world = to_matrix(pw[result.idx['Camera']])
            elif view in GUN_VIEWS:
                target, place, up = GUN_VIEWS[view]
                scene.render.resolution_x, scene.render.resolution_y = close
                camera.data.lens = a.close_lens
                gun = to_matrix(pw[result.idx['Weapon']])
                look_at(camera, gun @ Vector(place), gun @ Vector(target), gun.to_3x3() @ Vector(up))
            else:
                side, target, direction, up, distance = VIEWS[view]
                scene.render.resolution_x, scene.render.resolution_y = close
                camera.data.lens = a.close_lens
                hand = to_matrix(pw[result.idx[side + 'Arm_Hand']])
                rot = hand.to_3x3()
                at = hand @ Vector(target)
                look_at(camera, at + rot @ (Vector(direction).normalized() * distance), at, rot @ Vector(up))
            for kind in kinds:
                source.show(kind in ('src', 'mix'))
                result.show(kind in ('fo4', 'mix'))
                label = {'src': 'SOURCE (Destiny 2)', 'fo4': 'RESULT (Fallout 4)', 'mix': 'SOURCE + RESULT'}[kind]
                scene.render.stamp_note_text = '%s   frame %d/%d   %s' % (label, f, n - 1, view)
                scene.render.filepath = os.path.join(a.out, '%s_f%03d_%s_%s.png' % (tag, f, view, kind))
                bpy.ops.render.render(write_still=True)
                count += 1
    print('RENDERED', count, 'pictures')


if __name__ == '__main__':
    main()
