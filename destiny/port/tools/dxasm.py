#!/usr/bin/env python3
"""A small disassembler for the bytecode of a Direct3D 11 shader (the chunk SHEX or SHDR of a DXBC file).

    python3 destiny/port/tools/dxasm.py FILE.dxbc

It prints one line for each instruction, in the notation of the Microsoft disassembler. It is
for the analysis of a material of Destiny 2 (tools/d2reticle.py saves the shaders of the
parts of a sight). It knows the instructions of a simple vertex or pixel shader; for an
instruction that it does not know it prints the number of the operation and its tokens.
"""
import struct
import sys

OPS = """add and break breakc call callc case continue continuec cut default deriv_rtx deriv_rty discard div dp2 dp3 dp4
else emit emitthencut endif endloop endswitch eq exp frc ftoi ftou ge iadd if ieq ige ilt imad imax imin imul ine ineg ishl ishr
itof label ld ld_ms log loop lt mad min max customdata mov movc mul ne nop not or resinfo ret retc round_ne round_ni round_pi
round_z rsq sample sample_c sample_c_lz sample_l sample_d sample_b sqrt switch sincos udiv ult uge umul umad umax umin ushr utof
xor dcl_resource dcl_constant_buffer dcl_sampler dcl_index_range dcl_gs_output_primitive_topology dcl_gs_input_primitive
dcl_max_output_vertex_count dcl_input dcl_input_sgv dcl_input_siv dcl_input_ps dcl_input_ps_sgv dcl_input_ps_siv dcl_output
dcl_output_sgv dcl_output_siv dcl_temps dcl_indexable_temp dcl_global_flags reserved0 lod gather4 sample_pos sample_info""".split()
OPERAND = {0: 'r', 1: 'v', 2: 'o', 3: 'x', 6: 's', 7: 't', 8: 'cb', 9: 'icb', 12: 'oDepth', 13: 'null'}
XYZW = 'xyzw'
TESTED = {'if', 'breakc', 'callc', 'continuec', 'discard', 'retc'}


def chunks(data):
    if data[:4] != b'DXBC':
        raise ValueError('not a DXBC file')
    count, = struct.unpack_from('<I', data, 0x1C)
    for i in range(count):
        offset, = struct.unpack_from('<I', data, 0x20 + i * 4)
        size, = struct.unpack_from('<I', data, offset + 4)
        yield data[offset:offset + 4].decode('latin1'), data[offset + 8:offset + 8 + size]


class Tokens:
    def __init__(self, words, at):
        self.words, self.at = words, at

    def take(self):
        self.at += 1
        return self.words[self.at - 1]


def operand(t):
    token = t.take()
    modifier = ''
    extended = token >> 31
    while extended:
        more = t.take()
        if more & 0x3F == 1:
            modifier = ('', '-', 'abs', '-abs')[(more >> 6) & 0xFF if (more >> 6) & 0xFF < 4 else 0]
        extended = more >> 31
    components, kind, dimension = token & 3, (token >> 12) & 0xFF, (token >> 20) & 3
    if kind == 4:
        values = [t.take() for _ in range(4 if components == 2 else 1)]
        text = []
        for value in values:
            number, = struct.unpack('<f', struct.pack('<I', value))
            # a small whole number is an integer in most places
            text.append('%d' % value if value < 0x10000 else '%.6g' % number)
        return 'l(%s)' % ', '.join(text)
    indices = []
    for i in range(dimension):
        representation = (token >> (22 + i * 3)) & 7
        if representation == 0:
            indices.append('%d' % t.take())
        elif representation == 2:
            indices.append(operand(t))
        elif representation == 3:
            base = t.take()
            indices.append('%s + %d' % (operand(t), base))
        else:
            indices.append('?')
    name = OPERAND.get(kind, 'type%d_' % kind)
    if indices:
        name += indices[0] + ''.join('[%s]' % x for x in indices[1:])
    if components == 2:
        mode = (token >> 2) & 3
        if mode == 0:
            mask = (token >> 4) & 0xF
            name += '.' + ''.join(XYZW[i] for i in range(4) if mask >> i & 1) if mask else ''
        elif mode == 1:
            name += '.' + ''.join(XYZW[(token >> (4 + i * 2)) & 3] for i in range(4))
        else:
            name += '.' + XYZW[(token >> 4) & 3]
    if modifier == 'abs':
        return 'abs(%s)' % name
    if modifier == '-abs':
        return '-abs(%s)' % name
    return modifier + name


def disassemble(code):
    words = struct.unpack('<%dI' % (len(code) // 4), code[:len(code) // 4 * 4])
    kind = {0: 'ps', 1: 'vs', 2: 'gs', 3: 'hs', 4: 'ds', 5: 'cs'}.get(words[0] >> 16, '?')
    lines = ['%s_%d_%d' % (kind, (words[0] >> 4) & 0xF, words[0] & 0xF)]
    at, end, depth = 2, words[1], 0
    while at < end:
        token = words[at]
        op = token & 0x7FF
        name = OPS[op] if op < len(OPS) else 'op%d' % op
        if name == 'customdata':
            length = words[at + 1]
            lines.append('  customdata, %d tokens (the immediate constant buffer)' % length)
            for i in range(at + 2, at + length, 4):
                lines.append('    ' + ', '.join('%.6g' % struct.unpack('<f', struct.pack('<I', w))[0] for w in words[i:i + 4]))
            at += length
            continue
        length = (token >> 24) & 0x7F
        if length == 0:
            lines.append('  %s: no length' % name)
            break
        t = Tokens(words, at + 1)
        extended = token >> 31
        while extended:
            extended = t.take() >> 31
        text = name
        if name.startswith('dcl_'):
            if name == 'dcl_temps':
                text += ' %d' % t.take()
            elif name == 'dcl_global_flags':
                text += ' 0x%X' % (token >> 11 & 0x1FFF)
            elif name in ('dcl_input_ps', 'dcl_input_ps_siv', 'dcl_input_ps_sgv'):
                mode = ('', 'constant', 'linear', 'linear centroid', 'linear noperspective')[min((token >> 11) & 0xF, 4)]
                text += ' %s %s' % (mode, operand(t))
            else:
                try:
                    text += ' ' + operand(t)
                except Exception:
                    pass
            rest = words[t.at:at + length]
            if rest:
                text += '  ; ' + ' '.join('%d' % w for w in rest)
        else:
            if (token >> 13) & 1 and name not in TESTED:
                text += '_sat'
            if name in TESTED:
                text += '_nz' if (token >> 18) & 1 else '_z'
            parts = []
            try:
                while t.at < at + length:
                    parts.append(operand(t))
            except Exception as error:
                parts.append('? (%s)' % error)
            text += ' ' + ', '.join(parts)
        if name in ('else', 'endif', 'endloop', 'endswitch'):
            depth = max(depth - 1, 0)
        lines.append('  ' + '  ' * depth + text.rstrip())
        if name in ('if', 'else', 'loop', 'switch'):
            depth += 1
        at += length
    return lines


def signature(data):
    count, = struct.unpack_from('<I', data, 0)
    out = []
    for j in range(count):
        name_offset, index, system_value, _, register, mask = struct.unpack_from('<5IB', data, 8 + j * 24)
        end = data.index(b'\0', name_offset)
        out.append('%s%d (register %d, mask %s)' % (data[name_offset:end].decode(), index, register,
                                                    ''.join(XYZW[i] for i in range(4) if mask >> i & 1)))
    return out


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) > 1 else 2)
    data = open(sys.argv[1], 'rb').read()
    for name, body in chunks(data):
        if name in ('ISGN', 'OSGN'):
            print('%s: %s' % ('input' if name == 'ISGN' else 'output', '; '.join(signature(body))))
        if name in ('SHEX', 'SHDR'):
            print('\n'.join(disassemble(body)))


if __name__ == '__main__':
    main()
