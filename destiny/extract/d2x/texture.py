"""Texture headers, block-compressed pixel data and gear texture plates."""
import struct
from dataclasses import dataclass

import numpy as np
import texture2ddecoder
from PIL import Image

from .tag import Reader

PLATE_SET = 0x808072D2
PLATE_NAMES = ('albedo', 'normal', 'gstack')

# DXGI_FORMAT values that occur in the game.
_BLOCK = {
    71: ('bc1', False), 72: ('bc1', True),
    74: ('bc2', False), 75: ('bc2', True),
    77: ('bc3', False), 78: ('bc3', True),
    80: ('bc4', False), 81: ('bc4', False),
    83: ('bc5', False), 84: ('bc5', False),
    95: ('bc6', False), 96: ('bc6', False),
    98: ('bc7', False), 99: ('bc7', True),
}
_RAW = {
    28: ('RGBA', False), 29: ('RGBA', True),
    87: ('BGRA', False), 91: ('BGRA', True),
    61: ('L', False), 65: ('A', False),
}


@dataclass
class TextureInfo:
    tag: int
    width: int
    height: int
    depth: int
    array_size: int
    dxgi_format: int
    srgb: bool


def read_info(pm, tag):
    header = pm.read(tag)
    _, dxgi = struct.unpack_from('<II', header, 0)
    width, height, depth, array_size = struct.unpack_from('<4H', header, 0x0E)
    srgb = (_BLOCK.get(dxgi) or _RAW.get(dxgi) or ('', False))[1]
    return TextureInfo(tag, width, height, depth, array_size, dxgi, srgb)


def read_pixels(pm, tag):
    """Top mip level of a 2D texture as an (h, w, 4) uint8 RGBA array."""
    info = read_info(pm, tag)
    header = pm.read(tag)
    large, = struct.unpack_from('<I', header, 0x24)
    source = large if pm.exists(large) else pm.reference(tag)
    data = pm.read(source, cache=False)
    w, h = info.width, info.height
    if info.dxgi_format in _BLOCK:
        kind = _BLOCK[info.dxgi_format][0]
        decoder = getattr(texture2ddecoder, f'decode_{kind}')
        raw = decoder(data, w, h)                      # BGRA
        pixels = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 4)[:, :, [2, 1, 0, 3]]
        if kind == 'bc4':
            pixels = pixels.copy()
            pixels[:, :, 1] = pixels[:, :, 0]
            pixels[:, :, 2] = pixels[:, :, 0]
        return np.ascontiguousarray(pixels), info
    if info.dxgi_format in _RAW:
        order = _RAW[info.dxgi_format][0]
        if order in ('RGBA', 'BGRA'):
            pixels = np.frombuffer(data, dtype=np.uint8, count=w * h * 4).reshape(h, w, 4)
            if order == 'BGRA':
                pixels = pixels[:, :, [2, 1, 0, 3]]
            return np.ascontiguousarray(pixels), info
        gray = np.frombuffer(data, dtype=np.uint8, count=w * h).reshape(h, w)
        return np.dstack([gray, gray, gray, np.full_like(gray, 255)]), info
    raise NotImplementedError(f'DXGI format {info.dxgi_format} of texture {tag:08X}')


def find_plate_set(pm, resource_data):
    """Texture plate set tag referenced by a model resource (0 if none)."""
    words = np.frombuffer(resource_data[:len(resource_data) & ~3], dtype='<u4')
    for value in words.tolist():
        if 0x80800000 < value <= 0x81FFFFFF and pm.exists(value) and pm.reference(value) == PLATE_SET:
            return value
    return 0


def read_plates(pm, plate_set_tag):
    """Composed plate images of a plate set: dict name -> (h, w, 4) uint8 array."""
    r = Reader(pm.read(plate_set_tag))
    images = {}
    for name, offset in zip(PLATE_NAMES, (0x24, 0x28, 0x2C)):
        plate_tag = r.u32(offset)
        if not pm.exists(plate_tag):
            continue
        pr = Reader(pm.read(plate_tag))
        placements = []
        for item in pr.array_items(0x10, 0x14):
            texture = pr.u32(item)
            x, y, w, h = struct.unpack_from('<4i', pr.data, item + 4)
            if pm.exists(texture):
                placements.append((texture, x, y, w, h))
        if not placements:
            continue
        # The plate is a power-of-two canvas around all placements; when one
        # texture covers everything, keep its own size.
        width = max(x + w for _, x, y, w, h in placements)
        height = max(y + h for _, x, y, w, h in placements)
        canvas = np.zeros((height, width, 4), dtype=np.uint8)
        for texture, x, y, w, h in placements:
            pixels, _ = read_pixels(pm, texture)
            if pixels.shape[1] != w or pixels.shape[0] != h:
                pixels = np.asarray(Image.fromarray(pixels).resize((w, h), Image.LANCZOS))
            canvas[y:y + h, x:x + w] = pixels
        images[name] = canvas
    return images


def save_png(pixels, path, alpha=True):
    image = Image.fromarray(pixels if alpha else pixels[:, :, :3])
    image.save(path)


def material_images(pm, texture_tags):
    """Base color and normal images guessed from the pixel shader textures of a material."""
    images = {}
    for tag in texture_tags:
        if not pm.exists(tag):
            continue
        try:
            pixels, info = read_pixels(pm, tag)
        except (NotImplementedError, KeyError, ValueError):
            continue
        if info.depth > 1 or info.array_size > 1:
            continue
        if info.srgb and 'albedo' not in images:
            images['albedo'] = pixels
        elif not info.srgb and 'normal' not in images:
            mean = pixels[::8, ::8, :3].reshape(-1, 3).mean(axis=0)
            if abs(mean[0] - 128) < 24 and abs(mean[1] - 128) < 24 and mean[2] > 170:
                images['normal'] = pixels
    return images
