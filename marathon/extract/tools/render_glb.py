"""Blender: make pictures of a model file (glTF 2.0) from some directions.

    ./port marathon render FILE.glb OUT.png [--views side,top,front,quarter] [--size 960x540]
        [--frame N] [--action NAME] [--frames FIRST:LAST]
    python3 marathon/extract/tools/render_glb.py FILE.glb OUT.png [...]

The program starts Blender (the setting `blender`: BLENDER, data/config.toml, or the PATH) with
no window, and runs itself there. Blender can also start it:

    blender --background --factory-startup --python marathon/extract/tools/render_glb.py -- FILE.glb OUT.png [...]

With --frames the program makes one picture for each frame of the action, for each view:
OUT_VIEW_0000.png, OUT_VIEW_0001.png, ... The bounds are those of the first frame.

Each view is one picture OUT_VIEW.png. The camera looks at the center of the meshes, with an
orthographic projection. glTF axes: +Y up; Blender turns the file to +Z up. The views are
side, left, top, front, back, quarter and quarter2. Put the pictures below
data/marathon/extract/work/ or data/marathon/extract/validation/.
"""
import math
import os
import sys

try:
    import bpy
except ImportError:
    bpy = None

if bpy is None:
    # Not in Blender: start Blender with this file and the same arguments.
    import subprocess
    sys.dont_write_bytecode = True
    _r = os.path.dirname(os.path.abspath(__file__))
    while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
        _r = os.path.dirname(_r)
    sys.path.insert(0, _r)
    from portkit import paths
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if args[:1] in (['-h'], ['--help']) else 2)
    blender = paths.program('blender')
    if not blender or not os.path.isfile(blender):
        raise SystemExit('Blender is not there%s. Give it in the setting `blender` (BLENDER, or blender = "..." in data/config.toml), '
                         'or put `blender` in the PATH.' % (' (%s)' % blender if blender else ''))
    user = paths.data('marathon', 'extract', 'work', 'blender-user')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', BLENDER_USER_CONFIG=user + '/config', BLENDER_USER_SCRIPTS=user + '/scripts',
               BLENDER_USER_DATAFILES=user + '/datafiles', BLENDER_USER_RESOURCES=user)
    args[0], args[1] = os.path.abspath(args[0]), os.path.abspath(args[1])
    sys.exit(subprocess.call([blender, '--background', '--factory-startup', '--python-exit-code', '1',
                              '--python', os.path.abspath(__file__), '--'] + args, env=env))

from mathutils import Vector  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
source, out = args[0], args[1]
views = (args[args.index('--views') + 1] if '--views' in args else 'side,top,front,quarter').split(',')
width, height = [int(x) for x in (args[args.index('--size') + 1] if '--size' in args else '960x540').split('x')]
frame = int(args[args.index('--frame') + 1]) if '--frame' in args else None
action_name = args[args.index('--action') + 1] if '--action' in args else None
sequence = [int(x) for x in args[args.index('--frames') + 1].split(':')] if '--frames' in args else None
if sequence and frame is None:
    frame = sequence[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=source)
scene = bpy.context.scene
if action_name:
    for obj in scene.objects:
        if obj.type == 'ARMATURE':
            action = bpy.data.actions.get(action_name)
            if action is None:
                raise SystemExit('no action %s; the file has: %s' % (action_name, ', '.join(a.name for a in bpy.data.actions)))
            obj.animation_data_create()
            obj.animation_data.action = action
if frame is not None:
    scene.frame_set(frame)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
print('[render] objects:', ', '.join('%s (%s)' % (o.name, o.type) for o in scene.objects))
points = []
for obj in list(scene.objects):
    # the importer makes a small mesh for the shape of the bones: it is not a part of the model
    if obj.type == 'MESH' and (obj.name.startswith('Icosphere') or not obj.data.materials):
        bpy.data.objects.remove(obj)
        continue
    if obj.type == 'MESH':
        mesh = obj.evaluated_get(deps).to_mesh()
        points += [obj.matrix_world @ mesh.vertices[i].co for i in range(0, len(mesh.vertices), 7)]
if not points:
    raise SystemExit('the file has no mesh')
low = Vector([min(p[i] for p in points) for i in range(3)])
high = Vector([max(p[i] for p in points) for i in range(3)])
center, size = (low + high) / 2, max(high - low)

world = bpy.data.worlds.new('w')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.22, 0.24, 0.27, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
scene.world = world
for direction, energy in (((0.5, -0.6, 0.8), 4.0), ((-0.7, 0.4, 0.3), 1.5)):
    light = bpy.data.lights.new('l', 'SUN')
    light.energy = energy
    obj = bpy.data.objects.new('l', light)
    obj.rotation_euler = Vector(direction).to_track_quat('Z', 'Y').to_euler()
    scene.collection.objects.link(obj)
camera = bpy.data.cameras.new('c')
camera.type = 'ORTHO'
cam = bpy.data.objects.new('c', camera)
scene.collection.objects.link(cam)
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x, scene.render.resolution_y = width, height
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
# Blender space after the import: the glTF +Z (forward) is -Y, the glTF +X is +X, up is +Z.
DIRECTIONS = {'side': (1, 0, 0), 'left': (-1, 0, 0), 'top': (0, 0, 1), 'front': (0, -1, 0), 'back': (0, 1, 0), 'quarter': (0.8, -0.9, 0.5), 'quarter2': (-0.8, 0.9, 0.5)}
for view in views:
    direction = Vector(DIRECTIONS[view]).normalized()
    cam.location = center + direction * (size * 3 + 1)
    cam.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    if view == 'top':
        cam.rotation_euler = (math.radians(0), 0, math.radians(90))      # looks down, the forward axis of the model to the right
    camera.ortho_scale = size * (1.35 if sequence else 1.15)
    camera.clip_start, camera.clip_end = 0.01, size * 8 + 10
    if sequence:
        for n in range(sequence[0], sequence[1] + 1):
            scene.frame_set(n)
            scene.render.filepath = out.replace('.png', '_%s_%04d.png' % (view, n))
            bpy.ops.render.render(write_still=True)
        print('[render] %s: frames %d to %d' % (view, sequence[0], sequence[1]))
        continue
    scene.render.filepath = out.replace('.png', '_%s.png' % view)
    bpy.ops.render.render(write_still=True)
    print('[render]', scene.render.filepath)
