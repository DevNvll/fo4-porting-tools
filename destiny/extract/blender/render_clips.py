"""Renders animation clips of an exported .glb to numbered PNG frames (for a video or a sheet).

Usage:
  blender --background --python blender/render_clips.py -- <file.glb> <frames dir> <plan.json>

plan.json:
  {"view": "fp", "resolution": [1280, 720], "hold": 8, "step": 1,
   "clips": [{"clip": "fp_001_80BC8660", "label": "reload", "repeat": 1}, ...]}

The script writes frame_00000.png, frame_00001.png, ... and frames.json (which clip each frame shows).
With the "fp" view the camera is at the camera bone (b_utility) and only arms and weapon are shown.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

BODY_BONES = ('b_pedestal', 'b_pelvis', 'b_utility', 'b_spine', 'b_neck', 'b_head', 'b_jaw', 'b_l_clav', 'b_r_clav',
              'b_l_thigh', 'b_r_thigh', 'b_l_calf', 'b_r_calf', 'b_l_foot', 'b_r_foot', 'b_l_toe', 'b_r_toe',
              'b_l_brow', 'b_r_brow', 'b_l_eye', 'b_r_eye', 'b_l_upper', 'b_r_upper', 'b_l_lower', 'b_r_lower',
              'b_l_shoulder_twist', 'b_r_shoulder_twist')


def arms_only(meshes):
    """Hides geometry on body bones: first-person clips give useful poses to arms and weapon only."""
    for obj in meshes:
        hidden = {g.index for g in obj.vertex_groups if g.name.startswith(BODY_BONES)}
        if not hidden:
            continue
        keep = obj.vertex_groups.new(name='fp_visible')
        for vertex in obj.data.vertices:
            body = sum(g.weight for g in vertex.groups if g.group in hidden)
            if body < 0.5:
                keep.add([vertex.index], 1.0, 'REPLACE')
        mask = obj.modifiers.new('fp_mask', 'MASK')
        mask.vertex_group = 'fp_visible'


def setup_scene(resolution):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.image_settings.file_format = 'PNG'
    engines = [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
    world = bpy.data.worlds.new('preview')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.20, 0.22, 0.25, 1)
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
    # Burn the clip label and the clip frame into the picture.
    render = scene.render
    render.use_stamp = True
    for flag in ('use_stamp_date', 'use_stamp_time', 'use_stamp_render_time', 'use_stamp_frame', 'use_stamp_scene',
                 'use_stamp_camera', 'use_stamp_lens', 'use_stamp_filename', 'use_stamp_marker',
                 'use_stamp_sequencer_strip', 'use_stamp_memory', 'use_stamp_hostname', 'use_stamp_frame_range'):
        if hasattr(render, flag):
            setattr(render, flag, False)
    render.use_stamp_note = True
    render.stamp_font_size = max(14, resolution[1] // 30)
    render.stamp_background = (0, 0, 0, 0.55)
    render.stamp_foreground = (1, 1, 1, 1)
    return camera


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    source, out_dir, plan = Path(argv[0]), Path(argv[1]), json.loads(Path(argv[2]).read_text())
    out_dir.mkdir(parents=True, exist_ok=True)
    view = plan.get('view', 'fp')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=str(source))
    for obj in scene.objects:
        if obj.type == 'MESH' and not obj.vertex_groups:
            obj.hide_render = True
    meshes = [o for o in scene.objects if o.type == 'MESH' and o.vertex_groups]
    armature = [o for o in scene.objects if o.type == 'ARMATURE'][0]
    if view == 'fp':
        arms_only(meshes)
    camera = setup_scene(plan.get('resolution', [1280, 720]))
    scene.render.use_stamp = plan.get('stamp', True)
    actions = {a.name: a for a in bpy.data.actions}
    head = armature.pose.bones.get('b_utility')   # the game camera: eye point, view along glTF +Z

    def aim():
        if view == 'fp' and head is not None:
            camera.data.lens = plan.get('lens', 24)
            camera.data.clip_start = 0.01
            camera.location = armature.matrix_world @ head.head
            camera.rotation_euler = (math.radians(90), 0, math.radians(180))
            return
        depsgraph = bpy.context.evaluated_depsgraph_get()
        low, high = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        for obj in meshes:
            if not obj.name.startswith('region'):
                continue
            evaluated = obj.evaluated_get(depsgraph)
            for corner in evaluated.bound_box:
                point = evaluated.matrix_world @ Vector(corner)
                low, high = Vector(map(min, low, point)), Vector(map(max, high, point))
        center, size = (low + high) / 2, max((high - low).length, 1e-3)
        direction = Vector((1, 0, 0.08)).normalized() if view == 'side' else Vector((0.8, -1, 0.35)).normalized()
        camera.data.lens = 60
        camera.location = center + direction * size * 1.7
        camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()

    index = 0
    frames = []
    for entry in plan['clips']:
        matches = [name for name in sorted(actions) if name == entry['clip']] or \
            [name for name in sorted(actions) if name.startswith(entry['clip'])]
        if not matches:
            print('MISSING', entry['clip'])
            continue
        action = actions[matches[0]]
        for bone in armature.pose.bones:
            bone.matrix_basis.identity()
        armature.animation_data.action = action
        if hasattr(armature.animation_data, 'action_slot') and action.slots:
            armature.animation_data.action_slot = action.slots[0]
        start, end = int(round(action.frame_range[0])), int(round(action.frame_range[1]))
        label = entry.get('label') or action.name
        numbers = list(range(start, end + 1, plan.get('step', 1)))
        repeat = max(1, int(entry.get('repeat', 1)))
        rendered = {}
        for turn in range(repeat):
            for position, frame in enumerate(numbers):
                target = out_dir / f'frame_{index:05d}.png'
                if frame in rendered:          # a repeat of the clip: copy the picture
                    target.write_bytes(rendered[frame].read_bytes())
                else:
                    scene.frame_set(frame)
                    bpy.context.view_layer.update()
                    aim()
                    scene.render.stamp_note_text = f'{label}   [{action.name}]   {end + 1} frames'
                    scene.render.filepath = str(target)
                    bpy.ops.render.render(write_still=True)
                    rendered[frame] = target
                frames.append({'file': target.name, 'clip': action.name, 'label': label, 'frame': frame})
                index += 1
                last = turn == repeat - 1 and position == len(numbers) - 1
                for _ in range(plan.get('hold', 0) if last else 0):   # hold the last frame of a clip
                    copy = out_dir / f'frame_{index:05d}.png'
                    copy.write_bytes(target.read_bytes())
                    frames.append({'file': copy.name, 'clip': action.name, 'label': label, 'frame': frame})
                    index += 1
    (out_dir / 'frames.json').write_text(json.dumps(frames))
    print('RENDERED', index)


main()
