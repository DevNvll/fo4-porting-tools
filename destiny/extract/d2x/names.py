"""Bone names. The game stores only the FNV-1 hash of each bone name."""
from . import anim  # noqa: F401  (puts the vendored parser on sys.path)
from .tag import fnv1

from fnv_hashes.bones_names import hash_to_bungie_name  # player skeleton names

# Weapon bone names, found with a word list against the hashes in the game
# data. Add words here when a new weapon shows a `bone_XXXXXXXX` name.
WEAPON_BONE_WORDS = (
    'b_handle', 'b_trigger', 'b_hammer', 'b_chamber', 'b_ammo', 'b_barrel', 'b_magazine', 'b_slide',
    'b_release_1', 'b_release_2', 'b_release_button', 'b_fin', 'b_fin_end',
    'b_l_fin', 'b_r_fin', 'b_l_vent', 'b_r_vent', 'b_bolt', 'b_lever', 'b_pump', 'b_stock',
    'b_sight', 'b_scope', 'b_cylinder', 'b_muzzle', 'b_grip', 'b_foregrip', 'b_safety',
    'b_charging_handle', 'b_ejection_port', 'b_shell', 'b_cover', 'b_latch', 'b_bipod',
)

KNOWN = dict(hash_to_bungie_name)
KNOWN.update({fnv1(word): word for word in WEAPON_BONE_WORDS})


def bone_name(name_hash):
    return KNOWN.get(name_hash, f'bone_{name_hash:08X}')
