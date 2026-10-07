#!/usr/bin/env bash
# Prepares what m2x needs. Each file that this script makes is below data/marathon/extract/
# (the data folder is not in git):
#   runtime/liboodle-data-shared.so   the Oodle 9 shim (oodle9/oodle9.c), built with the C compiler
#   runtime/oo2core_9_win64.dll       a link to the Oodle library of the game (bin/x64/ of the game folder)
#   runtime/tag64                     the program of tag64/, built with cargo
#   target/                           the cargo build folder of tag64 (about 700 MB; you can delete it after the build)
#   notes/tag64.tsv                   the table of the 64-bit tag hashes of the game (the output of tag64, sorted)
#   out/, work/, validation/          the folders of the results
# Run it again at any time: a step that is complete is skipped. A step that cannot run (a
# tool, a folder or a setting is missing) does not stop the other steps. The end of the output
# names each missing thing and what to do, and the exit code is then 1.
#
# The game folder is the setting `marathon_game` (data/config.toml, or MARATHON_GAME).
# MARATHON_PACKAGES names another packages folder for the table. The clone of tiger-pkg and
# the Python environment are those of d2x: `./port destiny setup` makes them.
#
# Usage: ./port marathon setup [--table] [--force]   or   marathon/extract/setup.sh [--table] [--force]
#   --table   make notes/tag64.tsv again (do this after an update of the game)
#   --force   build the shim and tag64 again
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"      # marathon/extract
root="$(cd "${here}/../.." && pwd)"                       # the root of the repository
data="${FO4PORTS_DATA:-${root}/data}"                     # the same rule as portkit/paths.py
mkdir -p "${data}/marathon/extract"
area="$(cd "${data}/marathon/extract" && pwd)"
d2x="$(cd "${data}" && pwd)/destiny/extract"              # the data folder of d2x

make_table=0
force=0
for argument in "$@"; do
    case "${argument}" in
        --table) make_table=1 ;;
        --force) force=1 ;;
        -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "setup: unknown argument ${argument}. Usage: setup.sh [--table] [--force]" >&2; exit 2 ;;
    esac
done

missing=()
miss() {
    missing+=("$1")
    echo "setup: MISSING: $1" >&2
}

# A TOML basic string, for a cargo --config value.
toml_string() {
    local text="${1//\\/\\\\}"
    printf '"%s"' "${text//\"/\\\"}"
}

mkdir -p "${area}/runtime" "${area}/notes" "${area}/out" "${area}/work" "${area}/validation"

# 1. The Oodle 9 shim. It loads the Windows library into a Linux process (x86-64 only).
shim="${area}/runtime/liboodle-data-shared.so"
if [[ "$(uname -s) $(uname -m)" != "Linux x86_64" ]]; then
    miss "the Oodle 9 shim is for Linux on x86-64 only; this computer is $(uname -s) $(uname -m)."
elif [[ ${force} -eq 0 && -f "${shim}" && "${shim}" -nt "${here}/oodle9/oodle9.c" ]]; then
    echo "setup: the Oodle 9 shim is there."
else
    compiler="${CC:-}"
    if [[ -z "${compiler}" ]]; then
        for candidate in cc gcc clang; do
            if command -v "${candidate}" >/dev/null 2>&1; then compiler="${candidate}"; break; fi
        done
    fi
    if [[ -z "${compiler}" ]] || ! command -v "${compiler}" >/dev/null 2>&1; then
        miss "a C compiler (cc, gcc or clang; CC names another one). Install one and run setup again."
    else
        echo "setup: building the Oodle 9 shim with ${compiler} ..."
        "${compiler}" -O2 -fPIC -shared -o "${shim}.new" "${here}/oodle9/oodle9.c" -lpthread
        mv -f "${shim}.new" "${shim}"
    fi
fi

# 2. The link to the Oodle library of the game.
game=""
if command -v python3 >/dev/null 2>&1; then
    game="$(python3 "${root}/portkit/paths.py" get marathon_game 2>/dev/null || true)"
fi
game="${game:-${MARATHON_GAME:-}}"
if [[ -z "${game}" ]]; then
    miss "the setting marathon_game has no value. Give the game folder of Marathon in data/config.toml (marathon_game = \"...\") or in MARATHON_GAME, and run setup again."
elif [[ ! -f "${game}/bin/x64/oo2core_9_win64.dll" ]]; then
    miss "${game}/bin/x64/oo2core_9_win64.dll is not there. The setting marathon_game (MARATHON_GAME) must be the game folder that has packages/ and bin/x64/."
else
    ln -sfn "${game}/bin/x64/oo2core_9_win64.dll" "${area}/runtime/oo2core_9_win64.dll"
    echo "setup: the link to the Oodle library of the game is there."
fi

# 3. tag64. The manifest names tiger-pkg by its git commit. The patch gives cargo the clone of
# d2x, so cargo does not fetch tiger-pkg, and --locked keeps Cargo.lock in the source tree as it is.
tool="${area}/runtime/tag64"
clone="${d2x}/vendor/tiger-pkg"
if [[ ${force} -eq 0 && -x "${tool}" && "${tool}" -nt "${here}/tag64/src/main.rs" && "${tool}" -nt "${here}/tag64/Cargo.toml" && "${tool}" -nt "${here}/tag64/Cargo.lock" ]]; then
    echo "setup: tag64 is there."
elif ! command -v cargo >/dev/null 2>&1; then
    miss "cargo (the build tool of Rust; https://rustup.rs). Install it and run setup again."
elif [[ ! -f "${clone}/Cargo.toml" ]]; then
    miss "the clone of tiger-pkg (${clone}). Run ./port destiny setup (destiny/extract/setup.sh), then run this setup again."
else
    echo "setup: building tag64 into ${area}/target (some minutes the first time) ..."
    cargo build --release --locked --quiet \
        --manifest-path "${here}/tag64/Cargo.toml" \
        --target-dir "${area}/target" \
        --config "patch.'https://github.com/v4nguard/tiger-pkg.git'.tiger-pkg.path=$(toml_string "${clone}")"
    cp -f "${area}/target/release/tag64" "${tool}.new"
    mv -f "${tool}.new" "${tool}"
fi

# 4. The table of the 64-bit tag hashes. It is in the headers of the packages, so tag64 needs
# no Oodle library. The lines are sorted, so the same game build gives the same file.
table="${area}/notes/tag64.tsv"
packages="${MARATHON_PACKAGES:-}"
if [[ -z "${packages}" && -n "${game}" ]]; then packages="${game}/packages"; fi
if [[ ${make_table} -eq 0 && -s "${table}" ]]; then
    echo "setup: the table of the 64-bit tag hashes is there ($(wc -l < "${table}") hashes). --table makes it again."
elif [[ ! -x "${tool}" ]]; then
    miss "notes/tag64.tsv: tag64 is not built, so the table is not made."
elif [[ -z "${packages}" || ! -d "${packages}" ]]; then
    miss "notes/tag64.tsv: the packages folder (${packages:-the folder packages of the game folder}) is not there, so the table is not made."
else
    echo "setup: reading the 64-bit tag hashes of ${packages} ..."
    "${tool}" "${packages}" goliath | LC_ALL=C sort > "${table}.new"
    mv -f "${table}.new" "${table}"
    echo "setup: the table has $(wc -l < "${table}") hashes."
fi

# 5. The things of d2x that m2x uses. This script does not make them.
python="${d2x}/venv/bin/python"
d2x_ready=1
for needed in "${python}" "${d2x}/target/release/libtigerpkg_ffi.so" "${d2x}/vendor/tiger-animation-parser/tag_readers/read_rig.py"; do
    if [[ ! -e "${needed}" ]]; then
        miss "${needed} (a part of d2x). Run ./port destiny setup (destiny/extract/setup.sh)."
        d2x_ready=0
    fi
done

# 6. The test: open the packages and read 50 entries (this needs the shim and the library of the game).
if [[ ${#missing[@]} -eq 0 && ${d2x_ready} -eq 1 ]]; then
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${root}/destiny/extract" FO4PORTS_DATA="${data}" "${python}" - "${here}" <<'EOF'
import sys
sys.path.insert(0, sys.argv[1])
import m2x
pm = m2x.open_packages()
entries = pm.entries
tags = [int(t) for t in entries['tag'][(entries['type'] == 8) & (entries['size'] > 0x40)][::997][:50]]
for tag in tags:
    pm.read(tag, cache=False)
print('setup: the packages open: %d entries; %d entries read with no error; %d hashes in the table.' % (len(entries), len(tags), len(m2x.tag64_table())))
EOF
fi

if [[ ${#missing[@]} -gt 0 ]]; then
    echo "setup: NOT complete. Missing:" >&2
    for item in "${missing[@]}"; do echo "  - ${item}" >&2; done
    exit 1
fi
echo "setup: complete. Try: ./port marathon find \"M77\""
