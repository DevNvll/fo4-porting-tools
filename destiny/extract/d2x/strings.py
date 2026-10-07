"""Localized string containers (pre-Beyond Light layout, from Charm)."""
from .tag import Reader

# Class hashes for Destiny 2 pre-Beyond Light ("d2_sk").
LOCALIZED_STRINGS = 0x80809A88
LOCALIZED_STRINGS_DATA = 0x80809A8A


def _decode_part(data, start, byte_length, shift):
    if shift == 0:
        return data[start:start + byte_length].decode('utf-8', 'replace')
    out = []
    position = start
    end = start + byte_length
    while position < end:
        value = data[position]
        if 0xC0 <= value <= 0xDF:
            out.append(data[position:position + 2].decode('utf-8', 'replace'))
            position += 2
        elif 0xE0 <= value <= 0xEF:
            char = data[position:position + 3].decode('utf-8', 'replace')
            out.append(chr((ord(char) + shift) & 0xFFFF))
            position += 3
        else:
            out.append(chr((value + shift) & 0xFF))
            position += 1
    return ''.join(out)


def read_string_data(data):
    """All strings of one string data tag, in index order."""
    r = Reader(data)
    part_count, parts_start, _ = r.array(0x08)
    combo_count, combos_start, _ = r.array(0x48)
    strings = []
    for i in range(combo_count):
        offset = combos_start + i * 0x10
        first_part = r.rel(offset)
        count = r.i64(offset + 8)
        text = []
        for j in range(count):
            part = first_part + j * 0x20
            pointer = r.rel(part + 0x8)
            byte_length = r.u16(part + 0x14)
            shift = r.u16(part + 0x18)
            if pointer:
                text.append(_decode_part(data, pointer, byte_length, shift))
        strings.append(''.join(text))
    return strings


def read_container(pm, tag):
    """Dict of string hash -> English text for one localized strings tag."""
    data = pm.read(tag)
    r = Reader(data)
    hashes = r.np_array(0x08, '<u4')
    data_tag = r.u32(0x18)
    if not pm.exists(data_tag):
        return {}
    strings = read_string_data(pm.read(data_tag, cache=False))
    return {int(h): strings[i] for i, h in enumerate(hashes) if i < len(strings)}


def all_containers(pm):
    return pm.by_reference(LOCALIZED_STRINGS)
