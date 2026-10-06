"""The defaults of a configuration file.

tools/port.py writes a configuration file for a source folder, and a file of your own gives
only what the tools cannot find. Two keys are sufficient:

    name = "PPK"
    template = "pistol10mm"

resolve() adds each other value to the data of the file, and each tool then reads the
complete data. A value of the file always replaces a default.
`python3 tools/port.py CONFIG show` prints the complete data.

What the defaults are:

    work          /tmp/NAME-port (the name in lower case)
    source        the folder `source` beside the file: the extracted mod
    output        the folder NAME-fo4 beside the file: the HKX clips
    model         the model (.nif) of the source with the fewest shapes; then the shortest name
    animations    the folder `_1stperson` of the source that has the most .kf files
    [weapon] trigger   the center of the shape whose name has "trigger"
    [parts]       each node `##NAME` of the model that has a shape, by a word in its name:
                  bar, bolt, slide, lever, charg -> the bolt bone; clip, mag -> the magazine bone;
                  shell, bullet, round, cartridge -> the cartridge bone; trigger; hammer.
                  The template says which bone each of these is ([roles]). A node with no such
                  word gets a spare bone of the template.
    [fingers]     min_bend = 0.3, skin_center = true
    [collision]   the shapes on the cartridge bone are not colliders (they are in the magazine)
    [synth] ready      the first frame of the clip of WPNIdleReady, else of the reload
    [synth] sighted    the aim pose, moved until the node ##SightingNode is on the view axis
    [clips]       each animation of the source, by its New Vegas name (see clip_of), and each
                  other clip of the standard set from the weapon motion of the template

The events of a reload come from the motion: the magazine sounds when the magazine leaves its
place and when it is back, the bolt sounds when the bolt moves, and `reloadEnd` when the left
hand is back. The tool prints them. `events` in [clips.NAME] replaces them.
"""
import json
import os
import re
import sys
import numpy as np

# the first-person clips of a gun
STANDARD = ['WPNIdleReady', 'WPNIdleReadyA', 'WPNIdleReadyB', 'WPNIdleReadyC', 'WPNIdleReadyD',
            'WPNIdleSighted', 'WPNIdleGunDown',
            'WPNFireSingleReady', 'WPNFireSingleReadyA', 'WPNFireSingleReadyB', 'WPNFireSingleSighted',
            'WPNFireAutoReadyForward', 'WPNFireAutoReadyBack', 'WPNFireAutoSighted',
            'WPNEquip', 'WPNEquipFast', 'WPNUnEquip', 'WPNReload',
            'WPNWalkForwardReady', 'WPNWalkForwardSighted', 'WPNRunForwardReady', 'WPNRunLeftReady',
            'WPNRunRightReady', 'WPNRunGunDown', 'WPNSprint', 'WPNJumpImpactLand']

# a word in the name of a gun node -> the role of the node. The first role with a word wins.
ROLE_WORDS = [('trigger', ('trigger',)), ('hammer', ('hammer',)),
              ('cartridges', ('shell', 'bullet', 'round', 'cartridge')),
              ('magazine', ('clip', 'mag')),
              ('bolt', ('bar', 'bolt', 'slide', 'lever', 'charg'))]

GRIP = re.compile(r'^(1hp|2ha|2hr|2hh|2hl|1hm|2hm|1md|1gt|1lm|h2h)', re.I)


def clip_of(stem):
    """The Fallout 4 clip of a New Vegas animation name (the file name with no .kf), or None.

    aim -> WPNIdleReady, aimis -> WPNIdleSighted, attackright (attackleft, attack3 ...) ->
    WPNFireSingleReady, attackright_a -> WPNFireSingleReadyA, attack...is ->
    WPNFireSingleSighted, equip -> WPNEquip, unequip -> WPNUnEquip, reload... -> reload.
    The grip code at the start (1hp, 2ha ...) is not a part of the name. A sneak animation,
    a jam, and a variant for the empty gun or the last shot have no clip."""
    s = stem.lower()
    if s.startswith('sneak'):
        return None
    s = GRIP.sub('', s)
    if 'empty' in s or 'lastshot' in s or 'jam' in s:
        return None
    if s == 'aim':
        return 'WPNIdleReady'
    if s == 'aimis':
        return 'WPNIdleSighted'
    if s == 'equip':
        return 'WPNEquip'
    if s == 'unequip':
        return 'WPNUnEquip'
    if s.startswith('reload'):
        return 'reload'
    if s.startswith('attack'):
        if s.endswith('is'):
            return 'WPNFireSingleSighted'
        return 'WPNFireSingleReadyA' if s.endswith('_a') else 'WPNFireSingleReady'
    return None


def shape_name(name):
    """The name of a shape in the parts file."""
    return name.replace('##', '').replace(':', '_')


def find_model(folder):
    import fnvnif
    found = []
    for base, _, files in os.walk(folder):
        if 'character' in base.lower():
            continue
        for f in files:
            if f.lower().endswith('.nif'):
                p = os.path.join(base, f)
                try:
                    nif = fnvnif.Nif(p)
                except Exception:
                    continue
                shapes = sum(1 for b, _, _, _, _ in nif.walk() if 'data' in b)
                if shapes:
                    found.append((shapes, len(f), p))
    if not found:
        raise SystemExit('no model (.nif) with a shape below %s: give `model`' % folder)
    return sorted(found)[0][2]


def find_animations(folder):
    found = []
    for base, _, files in os.walk(folder):
        if os.path.basename(base).lower() == '_1stperson':
            kf = [f for f in files if f.lower().endswith('.kf')]
            if kf:
                found.append((-len(kf), base))
    return sorted(found)[0][1] if found else None


def auto_parts(nif, template):
    """FO4 bone -> node, for each gun node that has a shape below it."""
    roles = template.get('roles')
    if roles is None:
        raise SystemExit('the template has no [roles] table: give [parts]')
    root = nif.root()
    parent = {}
    with_shape = set()
    order = []
    for b, p, _, _, _ in nif.walk():
        parent[b['name']] = p['name'] if p is not None else None
        if 'data' in b:
            n = parent[b['name']]
            while n is not None:
                with_shape.add(n)
                n = parent[n]
        elif b is not root and b['name'].startswith('##'):
            order.append(b['name'])
    spare = list(roles.get('spare', []))
    used, out = set(), {}
    for node in order:
        if node not in with_shape:
            continue
        low = node.lower()
        bone = None
        for role, words in ROLE_WORDS:
            if any(w in low for w in words):
                bone = roles.get(role)
                break
        if bone is None or bone in used:
            bone = spare.pop(0) if spare else None
        if bone is None:
            print('[port] the node %s has no weapon bone: its shapes do not move' % node)
            continue
        used.add(bone)
        out[bone] = node
    # a bone needs its parent bone
    for bone in list(out):
        p = template['parents'].get(bone, 'Weapon')
        if p != 'Weapon' and p not in out:
            node = out.pop(bone)
            if spare:
                out[spare.pop(0)] = node
    return {b: out[b] for b in template['pivots'] if b in out}


class Motion:
    """The node places of a bake file, in the space of the weapon bone."""

    def __init__(self, path):
        d = json.load(open(path))
        self.nodes = d['nodes']
        self.count = len(d['times'])

    def matrix(self, name, f):
        return np.array(self.nodes[name]['world'][f], float).reshape(4, 3)

    def place(self, name, f):
        w = self.matrix('Weapon', f)
        p = self.matrix(name, f)[3] - w[3]
        return np.array([p @ w[0], p @ w[1], p @ w[2]])

    def away(self, name, limit):
        """The frames where a node is not at its place of the last frame."""
        last = self.place(name, self.count - 1)
        return [f for f in range(self.count) if np.linalg.norm(self.place(name, f) - last) > limit]


def reload_events(path, parts, template):
    """The annotations of a reload clip, from the motion of the magazine, the bolt and the left hand."""
    m = Motion(path)
    roles = template.get('roles', {})
    sounds = template.get('reload_sounds', ['MagOut', 'MagIn', 'BoltOpen', 'BoltClose'])
    events = []
    last_part = 0
    mag = parts.get(roles.get('magazine'))
    if mag in m.nodes:
        away = m.away(mag, 0.3)
        if away:
            if 'MagOut' in sounds:
                events.append([away[0], 'SoundPlay.{sound}ReloadMagOut'])
            if 'MagIn' in sounds:
                events.append([away[-1], 'SoundPlay.{sound}ReloadMagIn'])
            events.append([away[-1] + 2, 'reloadComplete'])
            last_part = away[-1] + 2
    else:
        events.append([m.count // 2, 'reloadComplete'])
    bolt = parts.get(roles.get('bolt'))
    if bolt in m.nodes:
        away = m.away(bolt, 0.1)
        if away:
            if away[0] > 0 and 'BoltOpen' in sounds:
                events.append([away[0], 'SoundPlay.{sound}ReloadBoltOpen'])
            if 'BoltClose' in sounds:
                events.append([away[-1], 'SoundPlay.{sound}ReloadBoltClose'])
            last_part = max(last_part, away[-1])
    # the reload ends when the left hand is near its place of the last frame, and stays there
    end = m.count - 3
    far = m.away('Bip01 L Hand', 6.0) if 'Bip01 L Hand' in m.nodes else []
    if far:
        end = min(end, far[-1] + 1)
    end = max(end, last_part + 2)
    end = min(end, m.count - 2)
    events += [[end - 1, 'initiateStart'], [end, 'reloadEnd']]
    return sorted(events, key=lambda e: e[0])


def auto_clips(D, template, out, rig, model_nodes):
    """Add the clip tables and the synth tables that the file does not give."""
    src = D['source']
    anims = src.get('animations', {})
    counts = {}
    for name in anims:
        p = os.path.join(out, 'anim', name + '.json')
        if os.path.exists(p):
            try:
                counts[name] = len(json.load(open(p))['times'])
            except Exception:
                pass
    # the clip of each animation
    given = {}
    reloads = []
    for name in sorted(anims):
        c = clip_of(os.path.splitext(os.path.basename(anims[name]))[0])
        if c == 'reload':
            reloads.append(name)
        elif c and c not in given:
            given[c] = name
        elif c == 'WPNFireSingleReady' and 'WPNFireSingleReadyB' not in given:
            given['WPNFireSingleReadyB'] = name
    partial = [n for n in reloads if 'partial' in n.lower()]
    other = [n for n in reloads if n not in partial]
    if partial and other:
        given['WPNReload'], given['WPNReloadEmpty'] = partial[0], other[0]
    elif reloads:
        given['WPNReload'] = reloads[0]
    D['assumed_clips'] = dict(given)

    synth = D.setdefault('synth', {})
    if 'ready' not in synth:
        first = given.get('WPNIdleReady') or given.get('WPNReload') or (sorted(anims)[0] if anims else None)
        if first is None:
            raise SystemExit('the source has no animation: give [synth] ready')
        synth['ready'] = {'bake': first, 'frame': 0}
    if 'sighted' not in synth:
        if '##SightingNode' not in model_nodes:
            raise SystemExit('the model has no node ##SightingNode: give [synth] sighted')
        sighted = {'bake': given.get('WPNIdleSighted') or synth['ready']['bake'], 'frame': 0,
                   'sight_node': '##SightingNode', 'align': True}
        if 'sighted_distance' in template:
            sighted['distance'] = template['sighted_distance']
        synth['sighted'] = sighted
    sclips = synth.setdefault('clips', {})
    static = synth.setdefault('static', {})
    clips = D.setdefault('clips', {})
    vanilla = os.path.join(rig, template['clips'])
    shifted = 'sight_node' in synth['sighted'] or 'sight' in synth['sighted']

    def events_of(name, source):
        if name.startswith('WPNFire'):
            return [[0, 'weaponFire']]
        if name.startswith('WPNReload'):
            p = os.path.join(out, 'anim', source + '.json')
            if os.path.exists(p):
                return reload_events(p, D.get('parts', {}), template)
        return None

    def add(name):
        if name in clips or name in sclips or name in static:
            return
        source = given.get(name)
        if source is None:
            # a variant with no source of its own is the clip that it is a variant of
            for base, variants in (('WPNIdleReady', 'ABCD'), ('WPNFireSingleReady', 'AB')):
                if name[:-1] == base and name[-1] in variants:
                    source = given.get(base)
                    if source is None and base == 'WPNIdleReady':
                        clips[name] = {'source': 'synth_WPNIdleReady'}
                        return
            if name == 'WPNEquipFast':
                source = given.get('WPNEquip')
        if source is not None:
            single = counts.get(source, 3) <= 2
            if 'Sighted' in name and shifted:
                # a source clip in the sights gets the move of the sighted pose
                st = {'base': 'sighted', 'frames': 30} if single else {'base': 'sighted', 'bake': source}
                ev = events_of(name, source)
                if ev and not single:
                    st['events'] = ev
                static[name] = st
                clips[name] = {'synth': True}
                return
            c = {'source': source}
            if single:
                c['hold'] = 30
            ev = events_of(name, source)
            if ev:
                c['events'] = ev
            clips[name] = c
            return
        # no source: the weapon motion of the template
        if name == 'WPNIdleReady':
            static[name] = {'base': 'ready', 'frames': 30}
        elif name == 'WPNIdleSighted':
            static[name] = {'base': 'sighted', 'frames': 30}
        elif name == 'WPNIdleGunDown':
            if not os.path.exists(os.path.join(vanilla, 'wpnrungundown.hkx')):
                return
            static[name] = {'base': 'ready', 'vanilla': 'wpnrungundown', 'frame': 0, 'frames': 30}
        elif os.path.exists(os.path.join(vanilla, name.lower() + '.hkx')):
            sclips[name] = 'sighted' if 'Sighted' in name else 'ready'
        else:
            return
        clips[name] = {'synth': True}

    for name in STANDARD:
        add(name)
    if 'WPNReloadEmpty' in given:
        add('WPNReloadEmpty')
    for name in list(clips):
        if clips[name].get('skip'):
            del clips[name]
            sclips.pop(name, None)
            static.pop(name, None)


KEYS = ('name', 'template', 'work', 'source', 'output', 'model', 'animations', 'weapon', 'parts', 'fingers',
        'collision', 'synth', 'clips')


def resolve(D, project, template, out, rig):
    """Complete the data of a configuration file. Returns the model of the source."""
    import fnvnif
    name = D['name']
    if not os.environ.get('PORT_CHILD'):
        for key in D:
            if key not in KEYS:
                print('[port] the configuration file has `%s`, which the tools do not use' % key, file=sys.stderr)

    def full(p, base):
        p = os.path.expanduser(str(p))
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))
    src = D.get('source')
    if isinstance(src, dict):
        table = dict(src)
        folder = full(table.get('folder', 'source'), project)
    else:
        table = {}
        folder = full(src or 'source', project)
    table['folder'] = folder
    # `model` and `animations` can be at the top of the file
    for key in ('model', 'animations'):
        if key in D and key not in table:
            table[key] = D.pop(key)
    if not os.path.isdir(folder) and not os.path.isabs(str(table.get('model', ''))):
        raise SystemExit('the source folder %s is not there: extract the mod into it, or give `source`' % folder)
    table['model'] = full(table['model'], folder) if table.get('model') else find_model(folder)
    anims = table.get('animations')
    if anims is None:
        anims = find_animations(folder)
        if anims is None:
            raise SystemExit('the folder %s has no _1stperson folder with .kf files: give `animations`' % folder)
    if isinstance(anims, str):
        # each animation of the folder that has a clip (not a sneak copy, a jam or an empty-gun variant)
        base = full(anims, folder)
        anims = {os.path.splitext(f)[0]: os.path.join(base, f) for f in sorted(os.listdir(base))
                 if f.lower().endswith('.kf') and clip_of(os.path.splitext(f)[0])}
    else:
        anims = {k: full(v, folder) for k, v in (anims or {}).items()}
    table['animations'] = anims
    D['source'] = table
    D.setdefault('output', name + '-fo4')

    nif = fnvnif.Nif(table['model'])
    nodes, shapes = set(), []
    parent = {}
    for b, p, wr, wt, ws in nif.walk():
        parent[b['name']] = p['name'] if p is not None else None
        if 'data' in b:
            g = nif.blocks[b['data']]
            v = g['vertices'] @ wr.T * ws + wt
            shapes.append((b['name'], v))
        else:
            nodes.add(b['name'])
    weapon = D.setdefault('weapon', {})
    if 'trigger' not in weapon:
        hit = [v for n, v in shapes if 'trigger' in n.lower()]
        if not hit:
            raise SystemExit('no shape of the model has "trigger" in its name: give [weapon] trigger')
        weapon['trigger'] = [round(float(x), 3) for x in (hit[0].min(0) + hit[0].max(0)) / 2]
    if 'parts' not in D:
        D['parts'] = auto_parts(nif, template)
    D.setdefault('fingers', {}).setdefault('min_bend', 0.3)
    D['fingers'].setdefault('skin_center', True)
    # the shapes on the cartridge bone are inside the magazine
    inner = []
    node = D['parts'].get(template.get('roles', {}).get('cartridges'))
    if node:
        for n, _ in shapes:
            p = parent[n]
            while p is not None and p != node:
                p = parent[p]
            if p == node:
                inner.append(n)
    D.setdefault('collision', {}).setdefault('skip', [shape_name(n) for n in inner])
    auto_clips(D, template, out, rig, nodes)
    return nif


def dump(D):
    """The data as text in the form of a configuration file."""
    lines = []

    def value(v):
        if isinstance(v, bool):
            return 'true' if v else 'false'
        if isinstance(v, (int, float)):
            return repr(v)
        if isinstance(v, str):
            return json.dumps(v)
        if isinstance(v, (list, tuple)):
            return '[' + ', '.join(value(x) for x in v) + ']'
        if isinstance(v, dict):
            return '{ ' + ', '.join('%s = %s' % (key(k), value(x)) for k, x in v.items()) + ' }'
        return json.dumps(str(v))

    def key(k):
        return k if re.fullmatch(r'[A-Za-z0-9_-]+', k) else json.dumps(k)

    def table(path, d):
        plain = {k: v for k, v in d.items() if not isinstance(v, dict) and not (isinstance(v, list) and v and isinstance(v[0], dict))}
        if path and plain:
            lines.append('')
            lines.append('[%s]' % path)
        for k, v in plain.items():
            lines.append('%s = %s' % (key(k), value(v)))
        for k, v in d.items():
            p = (path + '.' if path else '') + key(k)
            if isinstance(v, dict):
                if v and all(isinstance(x, dict) for x in v.values()) and path in ('', 'synth') and k in ('clips', 'static'):
                    lines.append('')
                    lines.append('[%s]' % p)
                    for kk, x in v.items():
                        lines.append('%s = %s' % (key(kk), value(x)))
                else:
                    table(p, v)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                for x in v:
                    lines.append('')
                    lines.append('[[%s]]' % p)
                    for kk, y in x.items():
                        lines.append('%s = %s' % (key(kk), value(y)))
    table('', D)
    return '\n'.join(lines) + '\n'
