"""Blender check of an exported .glb: import, validate, and render previews.

Usage:
  blender --background --python blender/check_glb.py -- <file.glb> <output dir>
      [--clips N]      render the middle frame of the first N clips (default 0)
      [--clip NAME]    render a strip of frames of one clip (can repeat)
      [--view side|right|front|back|fp]   fp puts the camera at the camera bone (b_utility)
      [--sheet]        render the middle frame of every clip at low resolution
      [--hide TEXT]    do not render mesh objects whose name contains TEXT
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments():
    argv = sys.argv[sys.argv.index('--') + 1:]
    options = {'clips': 0, 'clip': [], 'view': 'side', 'frames': 6, 'hide': [], 'sheet': False}
    positional = []
    i = 0
    while i < len(argv):
        if argv[i] == '--clips':
            options['clips'] = int(argv[i + 1]); i += 2
        elif argv[i] == '--clip':
            options['clip'].append(argv[i + 1]); i += 2
        elif argv[i] == '--view':
            options['view'] = argv[i + 1]; i += 2
        elif argv[i] == '--frames':
            options['frames'] = int(argv[i + 1]); i += 2
        elif argv[i] == '--hide':
            options['hide'].append(argv[i + 1]); i += 2
        elif argv[i] == '--sheet':
            options['sheet'] = True; i += 1
        else:
            positional.append(argv[i]); i += 1
    return Path(positional[0]), Path(positional[1]), options


def world_bounds(objects):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    low, high = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        for vertex in mesh.vertices:
            point = evaluated.matrix_world @ vertex.co
            low = Vector(map(min, low, point))
            high = Vector(map(max, high, point))
        evaluated.to_mesh_clear()
    return low, high


def setup_render(resolution=(960, 540)):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    engines = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
    world = bpy.data.worlds.new('preview')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.22, 0.24, 0.27, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = 1.2
    scene.world = world
    for name, rotation, energy in (('key', (math.radians(50), 0, math.radians(35)), 4.0),
                                   ('fill', (math.radians(70), 0, math.radians(-140)), 2.0)):
        light = bpy.data.lights.new(name, 'SUN')
        light.energy = energy
        obj = bpy.data.objects.new(name, light)
        obj.rotation_euler = rotation
        scene.collection.objects.link(obj)
    camera = bpy.data.objects.new('preview_camera', bpy.data.cameras.new('preview_camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    return camera


HEAD = None   # (armature object, camera bone b_utility) for the first-person view


def aim_camera(camera, low, high, view):
    if view == 'fp' and HEAD is not None:
        armature, bone = HEAD
        # The game camera is the bone b_utility: eye point and view axes.
        # After import, the view direction (glTF +Z) is the bone -Y... of the armature space.
        camera.data.lens = 24
        camera.data.clip_start = 0.01
        camera.location = armature.matrix_world @ bone.head
        camera.rotation_euler = (math.radians(90), 0, math.radians(180))
        return
    center = (low + high) / 2
    size = max((high - low).length, 1e-3)
    # After import the weapon points along -Y and +Z is up.
    directions = {'side': Vector((1, 0, 0.08)), 'right': Vector((-1, 0, 0.08)),
                  'front': Vector((0.8, -1, 0.35)), 'back': Vector((0.7, 1, 0.45)),
                  'fp': Vector((-0.25, 1, 0.35))}
    direction = directions.get(view, directions['side']).normalized()
    camera.data.lens = 60
    camera.data.clip_start = 0.005
    camera.location = center + direction * size * 1.55
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()


def render(path):
    bpy.context.scene.render.filepath = str(path)
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError as error:
        # No GPU context for EEVEE: use Cycles on the CPU.
        print('EEVEE failed, using Cycles:', error)
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = 24
        bpy.ops.render.render(write_still=True)


def main():
    source, out_dir, options = arguments()
    out_dir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30   # clips are 30 frames per second
    bpy.ops.import_scene.gltf(filepath=str(source))

    # The importer adds an unskinned helper mesh for bone shapes; ignore it.
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.vertex_groups]
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and not obj.vertex_groups:
            obj.hide_render = True
    armatures = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    report = {'file': source.name, 'blender': bpy.app.version_string, 'problems': []}
    report['meshes'] = [{'name': o.name, 'vertices': len(o.data.vertices), 'polygons': len(o.data.polygons),
                         'materials': [m.name for m in o.data.materials if m],
                         'vertex_groups': len(o.vertex_groups)} for o in meshes]
    report['images'] = [{'name': i.name, 'size': list(i.size)} for i in bpy.data.images if i.size[0]]
    if not meshes:
        report['problems'].append('no mesh objects')
    if len(armatures) != 1:
        report['problems'].append(f'{len(armatures)} armatures (1 expected)')
    armature = armatures[0] if armatures else None
    if armature:
        bones = {b.name for b in armature.data.bones}
        report['bones'] = len(bones)
        report['bone_names'] = sorted(bones)
        for obj in meshes:
            missing = [g.name for g in obj.vertex_groups if g.name not in bones]
            if missing:
                report['problems'].append(f'{obj.name}: vertex groups without bone: {missing[:5]}')
            if not any(m.type == 'ARMATURE' and m.object == armature for m in obj.modifiers):
                report['problems'].append(f'{obj.name}: no armature modifier')
            unweighted = sum(1 for v in obj.data.vertices if not v.groups)
            if unweighted:
                report['problems'].append(f'{obj.name}: {unweighted} vertices without weights')
    actions = sorted(bpy.data.actions, key=lambda a: a.name)
    report['actions'] = [{'name': a.name, 'frames': [round(a.frame_range[0], 2), round(a.frame_range[1], 2)],
                          'fcurves': len(a.fcurves)} for a in actions]
    for action in actions:
        for curve in action.fcurves:
            if any(math.isnan(p.co[1]) or math.isinf(p.co[1]) for p in curve.keyframe_points):
                report['problems'].append(f'{action.name}: non-finite key in {curve.data_path}')
                break
        if armature:
            keyed = {curve.data_path.split('"')[1] for curve in action.fcurves if '"' in curve.data_path}
            missing = sorted(bones - keyed)
            if missing:
                report['problems'].append(f'{action.name}: {len(missing)} bones without keys, for example {missing[:3]}')

    for name in options['hide']:
        for obj in meshes:
            if name in obj.name:
                obj.hide_render = True
    visible = [o for o in meshes if not o.hide_render]
    global HEAD
    if armature and 'b_utility' in armature.pose.bones:
        HEAD = (armature, armature.pose.bones['b_utility'])
    camera = setup_render()
    scene = bpy.context.scene
    scene.render.fps = 30

    def use_action(action):
        if armature.animation_data is None:
            armature.animation_data_create()
        # Start from the rest pose: bones without keys must not keep the last clip's pose.
        for bone in armature.pose.bones:
            bone.matrix_basis.identity()
        armature.animation_data.action = action
        if hasattr(armature.animation_data, 'action_slot') and action is not None and action.slots:
            armature.animation_data.action_slot = action.slots[0]

    # Rest pose.
    if armature and armature.animation_data:
        use_action(None)
        for bone in armature.pose.bones:
            bone.matrix_basis.identity()
    bpy.context.view_layer.update()
    low, high = world_bounds(visible)
    report['bounds'] = {'min': [round(v, 4) for v in low], 'max': [round(v, 4) for v in high]}
    aim_camera(camera, low, high, options['view'])
    render(out_dir / f'{source.stem}_rest.png')
    report['renders'] = [f'{source.stem}_rest.png']

    def render_action(action, frames):
        use_action(action)
        start, end = action.frame_range
        for index in range(frames):
            frame = start if frames == 1 else start + (end - start) * index / (frames - 1)
            scene.frame_set(int(round(frame)))
            bpy.context.view_layer.update()
            box_low, box_high = world_bounds(visible)
            aim_camera(camera, box_low, box_high, options['view'])
            name = f'{source.stem}_{action.name}_f{int(round(frame)):04d}.png'
            render(out_dir / name)
            report['renders'].append(name)

    if armature:
        for action in actions[:options['clips']]:
            use_action(action)
            middle = (action.frame_range[0] + action.frame_range[1]) / 2
            scene.frame_set(int(round(middle)))
            bpy.context.view_layer.update()
            box_low, box_high = world_bounds(visible)
            aim_camera(camera, box_low, box_high, options['view'])
            name = f'{source.stem}_{action.name}_mid.png'
            render(out_dir / name)
            report['renders'].append(name)
        if options['sheet']:
            scene.render.resolution_x, scene.render.resolution_y = 384, 216
            sheet_dir = out_dir / f'{source.stem}_sheet'
            sheet_dir.mkdir(exist_ok=True)
            for action in actions:
                use_action(action)
                scene.frame_set(int(round((action.frame_range[0] + action.frame_range[1]) / 2)))
                bpy.context.view_layer.update()
                box_low, box_high = world_bounds(visible)
                aim_camera(camera, box_low, box_high, options['view'])
                render(sheet_dir / f'{action.name}.png')
            report['sheet'] = sheet_dir.name
            scene.render.resolution_x, scene.render.resolution_y = 960, 540
        for wanted in options['clip']:
            for action in actions:
                if wanted in action.name:
                    render_action(action, options['frames'])

    (out_dir / f'{source.stem}_report.json').write_text(json.dumps(report, indent=2))
    summary = {k: report[k] for k in ('file', 'bones', 'problems') if k in report}
    summary.update(meshes=len(report['meshes']), actions=len(report['actions']), renders=len(report['renders']))
    print('CHECK', json.dumps(summary))
    if report['problems']:
        sys.exit(2)


main()
