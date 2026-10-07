"""Animation clip decoding through tiger-animation-parser (data/destiny/extract/vendor/).

The parser reads tag binaries from real files, so callers pass file paths of
tags that `d2x` unpacked before. Output tracks use the parser's export frame:
Y up, Z forward, X right ([x, y, z] in Tiger becomes [y, z, x]).
"""
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .pkg import SETUP_HINT, VENDOR

PARSER = VENDOR / 'tiger-animation-parser'
if not (PARSER / 'tag_readers').is_dir():
    raise ImportError(f'{PARSER} is missing. {SETUP_HINT}')
if str(PARSER) not in sys.path:
    sys.path.insert(0, str(PARSER))

from tag.game_version import Game_Version                              # noqa: E402
from tag_readers.read_animation import read_animation                  # noqa: E402
from tag_readers.read_skeleton import read_skeleton                    # noqa: E402
from tag_readers.read_rig import read_runtime_rig                      # noqa: E402
from animation_decoding.decode_animation import decode_animation       # noqa: E402
from runtime_rig.rig_retarget import rig_retarget                      # noqa: E402
from animation_export.convert_animation_object_to_local import convert_obj_to_local  # noqa: E402

for name in ('runtime_rig.rig_retarget', 'animation_export.convert_animation_object_to_local',
             'tag.tag_array'):
    logging.getLogger(name).setLevel(logging.ERROR)

FRAME_RATE = 30.0


@dataclass
class Clip:
    name: str
    frame_count: int
    animation_hash: int
    node_count: int
    control_count: int
    codecs: tuple
    # Per skeleton bone, local (parent) space: (frames, 3), (frames, 4 xyzw), (frames, 3)
    scales: np.ndarray
    rotations: np.ndarray
    translations: np.ndarray
    animated: np.ndarray     # bool per bone: the pose changes during the clip
    additive: bool = False   # the clip stores offsets; the export adds them to a base pose


class Rig:
    """Skeleton plus runtime rig of one entity, as the parser reads them."""

    def __init__(self, skeleton_path, rig_path, version='d2_sk'):
        self.version = Game_Version(version)
        with open(skeleton_path, 'rb') as stream:
            self.skeleton = read_skeleton(stream, self.version)
        with open(rig_path, 'rb') as stream:
            self.rig = read_runtime_rig(stream, self.version)

    @property
    def bone_count(self):
        return self.skeleton.node_defs.length

    def controls(self, clip_path):
        """Raw rig control tracks of a clip (before the rig solve), with the parsed tag."""
        with open(clip_path, 'rb') as stream:
            data = read_animation(stream, self.version)
        return data, decode_animation(data)

    def bind_translation_scale(self):
        """Mean bone offset length of the skeleton; the size reference for `is_additive`."""
        lengths = [float(np.linalg.norm([m[3][0], m[3][1], m[3][2]])) for m in self.skeleton.bone_to_parent_offset]
        return float(np.mean(lengths[1:])) if len(lengths) > 1 else 0.0

    def is_additive(self, tracks):
        """Additive clips hold near-zero offsets and near-identity rotations for all controls."""
        offsets = [np.linalg.norm(t.translations, axis=-1).mean() for t in tracks if t.translations is not None]
        turns = [np.abs(np.asarray(t.rotations)[..., 3]).mean() for t in tracks if t.rotations is not None]
        if not offsets or not turns:
            return False
        return bool(np.mean(turns) > 0.9 and np.mean(offsets) < 0.4 * self.bind_translation_scale())

    def decode(self, clip_path, name=None, base=None):
        """Decodes a clip to local bone tracks.

        `base` is the control track list of a full-pose clip. When this clip is
        additive, its offsets are applied to the first frame of `base`
        (rotation: base * offset, translation: base + offset, scale: base * offset).
        """
        data, tracks = self.controls(clip_path)
        additive = self.is_additive(tracks)
        if additive and base is not None:
            for index, track in enumerate(tracks):
                if index >= len(base):
                    break
                reference = base[index]
                if reference.rotations is not None:
                    first = np.asarray(reference.rotations, dtype=np.float64).reshape(-1, 4)[0]
                    if track.rotations is None:
                        track.rotations = first[None].astype(np.float32)
                    else:
                        track.rotations = _quat_multiply(first, np.asarray(track.rotations, dtype=np.float64)).astype(np.float32)
                if reference.translations is not None:
                    first = np.asarray(reference.translations, dtype=np.float64).reshape(-1, 3)[0]
                    if track.translations is None:
                        track.translations = first[None].astype(np.float32)
                    else:
                        track.translations = (np.asarray(track.translations, dtype=np.float64)[..., :3] + first).astype(np.float32)
                if reference.scales is not None:
                    first = float(np.asarray(reference.scales, dtype=np.float64).reshape(-1)[0])
                    if track.scales is None:
                        track.scales = np.array([first], dtype=np.float32)
                    else:
                        track.scales = (np.asarray(track.scales, dtype=np.float64) * first).astype(np.float32)
        header = data.animation_header
        retargeted = rig_retarget(data, tracks, self.skeleton, self.rig)
        local = convert_obj_to_local(data, retargeted, self.skeleton)
        scales = np.stack([t.scales for t in local])
        rotations = np.stack([t.rotations for t in local])
        translations = np.stack([t.translations for t in local])
        animated = np.array([
            # Limits above the quantization noise of the clip codecs.
            bool(np.ptp(rotations[i], axis=0).max() > 2e-3 or np.ptp(translations[i], axis=0).max() > 2e-4
                 or np.ptp(scales[i], axis=0).max() > 1e-3)
            for i in range(len(local))
        ])
        codecs = (
            data.static_bones_header.codec_type if data.static_bones_header is not None else -1,
            data.animated_bones_header.codec_type if data.animated_bones_header is not None else -1,
        )
        return Clip(name or Path(clip_path).stem, header.frame_count, header.animation_hash,
                    header.node_count, header.rig_control_count, codecs,
                    scales, rotations, translations, animated, additive)


def _quat_multiply(a, b):
    """Hamilton product a * b for xyzw quaternions; `b` can hold many rows."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ], axis=-1)


def clip_header(data):
    """Quick header facts of a clip tag without a full decode."""
    import struct
    animation_hash, = struct.unpack_from('<I', data, 0x120)
    frames, nodes, controls = struct.unpack_from('<3H', data, 0x13C)
    return {'hash': animation_hash, 'frames': frames, 'nodes': nodes, 'controls': controls}
