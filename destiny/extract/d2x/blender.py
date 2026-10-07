"""Runs the Blender validation script and builds a contact sheet of the clips."""
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .pkg import ROOT, paths

SCRIPT = ROOT / 'blender/check_glb.py'
CLIP_SCRIPT = ROOT / 'blender/render_clips.py'


def find_blender():
    """The Blender program: the setting `blender` (BLENDER, then data/config.toml, then the PATH)."""
    path = paths.program('blender')
    if not path:
        raise FileNotFoundError('Blender was not found. Give it in the setting `blender` '
                                '(data/config.toml or the environment variable BLENDER).')
    path = shutil.which(path) or path
    if not Path(path).is_file():
        raise FileNotFoundError(f'The setting `blender` does not point to a file: {path}')
    return path


def check(glb, out_dir=None, clips=0, view='side', clip_names=(), frames=6, hide=(), sheet=False):
    """Imports a .glb in Blender, validates it, renders previews. Returns the report dict."""
    glb = Path(glb)
    out_dir = Path(out_dir) if out_dir else glb.parent / 'preview'
    command = [find_blender(), '--background', '--python', str(SCRIPT), '--', str(glb), str(out_dir),
               '--clips', str(clips), '--view', view, '--frames', str(frames)]
    for name in clip_names:
        command += ['--clip', name]
    for name in hide:
        command += ['--hide', name]
    if sheet:
        command.append('--sheet')
    result = subprocess.run(command, capture_output=True, text=True)
    report_path = out_dir / f'{glb.stem}_report.json'
    if not report_path.is_file():
        raise RuntimeError(f'Blender did not write a report.\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}')
    report = json.loads(report_path.read_text())
    report['returncode'] = result.returncode
    if sheet and report.get('sheet'):
        report['sheet_image'] = str(contact_sheet(out_dir / report['sheet'], out_dir / f'{glb.stem}_clips.png'))
    return report


def contact_sheet(frames_dir, target, columns=8):
    """One image with the middle frame of every clip and its name."""
    files = sorted(Path(frames_dir).glob('*.png'))
    if not files:
        return None
    first = Image.open(files[0])
    width, height = first.size
    label = 16
    rows = (len(files) + columns - 1) // columns
    sheet = Image.new('RGB', (columns * width, rows * (height + label)), (24, 26, 30))
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(files):
        x, y = (index % columns) * width, (index // columns) * (height + label)
        sheet.paste(Image.open(path).convert('RGB'), (x, y))
        draw.text((x + 4, y + height + 2), path.stem, fill=(230, 230, 230))
    sheet.save(target)
    return target


def render_clips(glb, clips, frames_dir, view='fp', resolution=(1280, 720), hold=8, step=1, stamp=True):
    """Renders clips to numbered PNG frames. `clips` is a list of (clip name, label[, repeat])."""
    frames_dir = Path(frames_dir)
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)
    plan = frames_dir / 'plan.json'
    plan.write_text(json.dumps({
        'view': view, 'resolution': list(resolution), 'hold': hold, 'step': step, 'stamp': stamp,
        'clips': [{'clip': clip[0], 'label': clip[1], 'repeat': clip[2] if len(clip) > 2 else 1} for clip in clips],
    }))
    command = [find_blender(), '--background', '--python', str(CLIP_SCRIPT), '--', str(glb), str(frames_dir), str(plan)]
    result = subprocess.run(command, capture_output=True, text=True)
    index = frames_dir / 'frames.json'
    if not index.is_file():
        raise RuntimeError(f'Blender did not render the clips.\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}')
    missing = [line for line in result.stdout.splitlines() if line.startswith('MISSING')]
    return json.loads(index.read_text()), missing


def video(glb, clips, target, view='fp', resolution=(1280, 720), hold=8, keep_frames=False):
    """Renders clips and encodes one H.264 .mp4 (30 frames per second) with ffmpeg."""
    target = Path(target)
    frames_dir = target.with_suffix('').parent / f'{target.stem}_frames'
    frames, missing = render_clips(glb, clips, frames_dir, view, resolution, hold)
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', str(frames_dir / 'frame_%05d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-movflags', '+faststart', str(target)],
                   check=True)
    if not keep_frames:
        shutil.rmtree(frames_dir)
    return {'file': str(target), 'frames': len(frames), 'missing': missing}


def strip_sheet(glb, clips, target, view='fp', columns=8, resolution=(480, 270)):
    """One row per clip: a caption line, then `columns` frames spread over the clip."""
    target = Path(target)
    frames_dir = target.with_suffix('').parent / f'{target.stem}_frames'
    frames, missing = render_clips(glb, clips, frames_dir, view, resolution, hold=0, stamp=False)
    by_clip = {}
    for frame in frames:
        rows = by_clip.setdefault((frame['clip'], frame['label']), [])
        if not rows or frame['frame'] > rows[-1]['frame']:     # a repeat of a clip adds no row
            rows.append(frame)
    width, height = resolution
    caption = 34
    try:
        font, small = ImageFont.load_default(size=22), ImageFont.load_default(size=14)
    except TypeError:   # old Pillow
        font = small = ImageFont.load_default()
    sheet = Image.new('RGB', (columns * width, len(by_clip) * (height + caption)), (18, 20, 24))
    draw = ImageDraw.Draw(sheet)
    for row, ((clip, label), rows) in enumerate(by_clip.items()):
        top = row * (height + caption)
        seconds = len(rows) / 30
        text = label if label == clip else f'{label}   ({clip})'
        draw.text((10, top + 5), f'{text}   {len(rows)} frames, {seconds:.2f} s', fill=(255, 214, 102), font=font)
        picks = [rows[round(i * (len(rows) - 1) / max(columns - 1, 1))] for i in range(columns)]
        for column, frame in enumerate(picks):
            x, y = column * width, top + caption
            sheet.paste(Image.open(frames_dir / frame['file']).convert('RGB'), (x, y))
            draw.text((x + 6, y + height - 20), f"frame {frame['frame']}", fill=(235, 235, 235), font=small)
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target)
    shutil.rmtree(frames_dir)
    return {'file': str(target), 'rows': len(by_clip), 'missing': missing}
