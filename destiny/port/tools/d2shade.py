"""The Destiny 2 gear shader in texture space, and the conversion of its result to Fallout 4 textures.

Destiny draws a gun with three textures and the dyes of the item (its "shader"):

    albedo   the color (sRGB). A part that takes a dye has a gray albedo.
    gstack   red: occlusion; green: smoothness; blue: emission (above 40);
             alpha: 0 to 32 is the metal value of a pixel with no dye, 40 to 255 is the wear
             mask of a pixel with a dye
    normal   red and green: the normal

A gun has three dyes, and each dye has a primary and a secondary material: six slots. Each
mesh part has one slot (tools/d2dyes.py), so the slot of a pixel comes from the triangles of
the part in the texture.

`shade` does what the pixel shader of the game does, for each pixel of the textures. The
formula is that of the public shader sbox_destiny_2_gear_shader (DeltaDesigns), which is a
copy of the shader of the game for a different engine:

    remap(v, r)   = clamp(v * r.y + r.x, r.z, r.z + r.w)
    wear          = remap(wear mask, wear remap of the slot)
    color         = worn tint + (tint - worn tint) * wear
    base          = color * saturate(albedo * 4) + saturate(albedo - 0.25)          (overlay)
    base          = base * saturate(detail * 4) + saturate(detail - 0.25), with the detail blend (hard light)
    smoothness    = (worn remap + (remap - worn remap) * wear) of the gstack green, * 0.86
    metal         = worn metal + (metal - worn metal) * wear

A pixel with no dye keeps its albedo, the gstack green and the metal value of the gstack alpha.
The detail texture of a dye has the place (uv * 5) * transform.xy + transform.zw, as in that
shader (the game has a second set of texture coordinates for it, which the extraction does
not have). Not done: iridescence, fuzz, transmission and emission.

Fallout 4 has no metal value. `fallout4` makes its three textures from the result:

    _d   the base color (sRGB), darker where the occlusion is low
    _s   red: specular, from the reflectance at normal incidence; green: glossiness
    _n   the normal map with the detail normal of the dyes
"""
import json
import os

import numpy as np


def srgb_to_linear(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, np.float32), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1.0 / 2.4) - 0.055).astype(np.float32)


def saturate(x):
    return np.clip(x, 0.0, 1.0)


def remap(value, r):
    return np.clip(value * r[1] + r[0], r[2], r[2] + r[3])


def load_dyes(path):
    """The dyes file of tools/d2dyes.py, with each detail texture as an array (0 to 1)."""
    from PIL import Image
    with open(path) as f:
        data = json.load(f)
    folder = os.path.dirname(os.path.abspath(path))
    for dye in data['dyes']:
        if dye is None:
            continue
        for kind in ('detail_diffuse', 'detail_normal'):
            if kind in dye:
                pixels = np.asarray(Image.open(os.path.join(folder, dye[kind]['file'])).convert('RGBA'), np.float32) / 255.0
                if kind == 'detail_diffuse' and dye[kind].get('srgb'):
                    pixels[..., :3] = srgb_to_linear(pixels[..., :3])
                dye[kind]['pixels'] = pixels
    return data


def slot_map(shapes, size, slots):
    """The dye slot of each pixel of a texture (0 to 5), from the triangles of the shapes that
    have the texture. `slots` gives the slot of each shape. A pixel in no triangle gets the
    slot of the nearest triangle (16 pixels at most), else the slot 0."""
    from PIL import Image, ImageDraw
    width, height = size
    image = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(image)
    for shape, slot in zip(shapes, slots):
        uv = np.asarray(shape['uvs'], np.float64)
        uv = uv - np.floor(uv.min(axis=0))                       # a shape outside 0 to 1 is in the texture again
        for a, b, c in shape['triangles']:
            draw.polygon([(uv[a][0] * width, uv[a][1] * height), (uv[b][0] * width, uv[b][1] * height),
                          (uv[c][0] * width, uv[c][1] * height)], fill=slot + 1, outline=slot + 1)
    out = np.asarray(image, np.uint8).copy()
    for _ in range(16):
        empty = out == 0
        if not empty.any():
            break
        grown = out.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            near = np.roll(out, (dy, dx), axis=(0, 1))
            grown = np.where((grown == 0) & (near > 0), near, grown)
        out = grown
    return np.where(out == 0, 0, out.astype(np.int16) - 1).astype(np.int8), float((np.asarray(image) > 0).mean())


def sample(pixels, u, v):
    """Nearest texel of a tiled texture."""
    h, w = pixels.shape[:2]
    return pixels[np.mod(np.floor(v * h), h).astype(np.int64), np.mod(np.floor(u * w), w).astype(np.int64)]


def shade(albedo, gstack, normal, slots=None, dyes=None):
    """albedo, gstack, normal: (h, w, 4) arrays, 0 to 1, as the files have them.
    Returns a dictionary: base (linear color), metal, smooth, occlusion, emission (the mask),
    normal (red and green, 0 to 1), dyed (the part of the pixels with a dye)."""
    h, w = albedo.shape[:2]
    base = srgb_to_linear(albedo[..., :3])
    smooth = gstack[..., 1].astype(np.float32).copy()
    alpha = gstack[..., 3].astype(np.float32)
    metal = saturate(alpha * 7.96875)
    dyed = alpha >= 40.0 / 255.0
    wear_mask = saturate(alpha * 1.186 - 0.186)
    normal_rg = normal[..., :2].astype(np.float32).copy()
    out = {'occlusion': gstack[..., 0].astype(np.float32), 'emission': saturate((gstack[..., 2] - 40.0 / 255.0) * 1.18604651163),
           'dyed': float(dyed.mean()), 'slots': {}}
    if dyes is not None and slots is not None and dyed.any():
        v, u = np.mgrid[0:h, 0:w].astype(np.float32)
        u, v = (u + 0.5) / w, (v + 0.5) / h
        for slot in range(6):
            sel = dyed & (slots == slot)
            if not sel.any():
                continue
            dye = dyes['dyes'][slot // 2]
            if dye is None:
                continue
            side = 'primary' if slot % 2 == 0 else 'secondary'
            params, worn_params = dye[side + '_material_params'], dye[side + '_worn_material_params']
            advanced = dye[side + '_material_advanced_params']
            wear = remap(wear_mask[sel], dye[side + '_wear_remap'])[:, None]
            tint = np.array(dye[side + '_albedo_tint'][:3], np.float32)
            worn = np.array(dye[side + '_worn_albedo_tint'][:3], np.float32)
            color = worn + (tint - worn) * wear
            a = base[sel]
            c = color * saturate(a * 4.0) + saturate(a - 0.25)                                   # overlay
            g = smooth[sel]
            w1 = wear[:, 0]
            if 'detail_diffuse' in dye:
                t = dye['detail_diffuse_transform']
                d = sample(dye['detail_diffuse']['pixels'], u[sel] * 5.0 * t[0] + t[2], v[sel] * 5.0 * t[1] + t[3])
                blend = (worn_params[0] + (params[0] - worn_params[0]) * w1)[:, None]
                c = c + (c * saturate(d[:, :3] * 4.0) + saturate(d[:, :3] - 0.25) - c) * blend    # hard light
                rough_blend = worn_params[2] + (params[2] - worn_params[2]) * w1
                g = g + (d[:, 3] * saturate(g * 4.0) + saturate(g - 0.25) - g) * rough_blend
            main = remap(g, dye[side + '_roughness_remap'])
            worn_rough = remap(g, dye[side + '_worn_roughness_remap'])
            s = worn_rough + (main - worn_rough) * w1
            s = s * np.where(s <= 0.0, advanced[1] * 2.0, 0.86)
            base[sel] = saturate(c)
            smooth[sel] = saturate(s)
            metal[sel] = saturate(worn_params[3] + (params[3] - worn_params[3]) * w1)
            if 'detail_normal' in dye:
                t = dye['detail_normal_transform']
                d = sample(dye['detail_normal']['pixels'], u[sel] * 5.0 * t[0] + t[2], v[sel] * 5.0 * t[1] + t[3])[:, :2]
                blend = (worn_params[1] + (params[1] - worn_params[1]) * w1)[:, None]
                n = normal_rg[sel]
                over = np.where(n < 0.5, 2.0 * n * d, 1.0 - 2.0 * (1.0 - n) * (1.0 - d))
                normal_rg[sel] = saturate(n + (over - n) * blend)
            out['slots'][slot] = {'pixels': float(sel.mean()), 'iridescence': advanced[0],
                                  'mean_base': [float(x) for x in base[sel].mean(axis=0)], 'mean_metal': float(metal[sel].mean())}
    out.update(base=base, metal=metal, smooth=smooth, normal=normal_rg)
    return out


def fallout4(result, occlusion=0.5, specular=0.9):
    """(diffuse (h, w, 3) sRGB 0 to 255, specular (h, w), gloss (h, w), normal (h, w, 3)) as uint8.

    The reflectance of a surface at normal incidence is 0.04 for a surface that is not a metal
    and the base color for a metal. Fallout 4 has one specular value for each pixel, so it is
    `specular` * the square root of the luminance of that reflectance (the square root, because
    a specular texture is not linear), and more for a smooth surface. A metal keeps its base
    color in the diffuse texture: Fallout 4 has no value that removes the diffuse light of a
    metal, and a rough metal in the light of the sky has about the look of a surface with
    that color."""
    base, metal, smooth, ao = result['base'], result['metal'], result['smooth'], result['occlusion']
    shade_ao = (1.0 - occlusion) + occlusion * ao
    diffuse = linear_to_srgb(base * shade_ao[..., None])
    f0 = 0.04 + (base - 0.04) * metal[..., None]
    luminance = f0[..., 0] * 0.2126 + f0[..., 1] * 0.7152 + f0[..., 2] * 0.0722
    spec = saturate(specular * np.sqrt(saturate(luminance)) * (0.5 + 0.5 * smooth) * (0.6 + 0.4 * ao))
    rg = result['normal']
    nx, ny = rg[..., 0] * 2.0 - 1.0, rg[..., 1] * 2.0 - 1.0
    nz = np.sqrt(saturate(1.0 - nx * nx - ny * ny))
    normal = np.dstack([rg[..., 0], rg[..., 1], nz * 0.5 + 0.5])

    def byte(x):
        return np.clip(np.asarray(x, np.float32) * 255.0 + 0.5, 0, 255).astype(np.uint8)
    return byte(diffuse), byte(spec), byte(smooth), byte(normal)
