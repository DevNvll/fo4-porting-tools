#!/usr/bin/env bash
# Prepares the tools that d2x uses. Each file that this script makes is below
# data/destiny/extract/ (the data folder is not in git):
#   vendor/tiger-pkg               (v4nguard): package reader, with the linoodle shim for Oodle 3
#   vendor/tiger-animation-parser  (SolUnshadowed): animation clip decoder, plus the d2_sk patch
#   target/                        cargo build of tigerpkg-ffi: the C wrapper around tiger-pkg for Python
#   venv/                          Python environment
#   runtime/                       the linoodle shim and a link to the Oodle DLL of the game
#   out/                           default output folder of d2x
# Run it again at any time; steps that are complete are skipped.
# The game folder is the setting `destiny_game` (data/config.toml, or D2X_GAME). Only the
# last step needs it.
# Usage: ./port destiny setup     or     destiny/extract/setup.sh     (from any working folder)
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./port destiny setup          (or: destiny/extract/setup.sh, from any working folder)

Prepares the tools that d2x uses. It has no arguments. It writes only below
data/destiny/extract/ (or below destiny/extract/ of FO4PORTS_DATA):
  vendor/    the clones of tiger-pkg and tiger-animation-parser at fixed commits, with the d2_sk patch
  target/    the cargo build of tigerpkg-ffi (libtigerpkg_ffi.so, tigerx)
  venv/      the Python environment (requirements.txt)
  runtime/   the linoodle shim and a link to the Oodle DLL of the game
  out/       the default output folder of d2x

Run it again at any time; it skips each step that is complete.
It needs git, cargo and python3 (3.11 or later). It uses uv if uv is there.
The game folder is the setting destiny_game (data/config.toml, or D2X_GAME). Only the last
step (the Oodle link) needs it; with no game folder the exit code is 1 and the other steps are complete.
  -h, --help   show this text and do nothing
EOF
}
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "") ;;
    *) echo "setup: unknown argument: $1" >&2; usage >&2; exit 2 ;;
esac

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"      # destiny/extract
root="$(cd "${here}/../.." && pwd)"                       # the root of the repository
data="${FO4PORTS_DATA:-${root}/data}"                     # the same rule as portkit/paths.py
mkdir -p "${data}/destiny/extract"
area="$(cd "${data}/destiny/extract" && pwd)"

tiger_pkg_url="https://github.com/v4nguard/tiger-pkg.git"
tiger_pkg_commit="657f41c0851001b2d371592b2f7a5cb9c686ddb4"    # also in tigerpkg-ffi/Cargo.toml
parser_url="https://github.com/SolUnshadowed/tiger-animation-parser.git"
parser_commit="b9fdc3a43dd28118113275624fcc9054b75855f4"

clone_at() {
    local url="$1" dir="$2" commit="$3"
    if [[ ! -d "${dir}/.git" ]]; then
        echo "setup: cloning ${url} ..."
        git clone --quiet "${url}" "${dir}"
    fi
    if [[ "$(git -C "${dir}" rev-parse HEAD)" != "${commit}" ]]; then
        git -C "${dir}" fetch --quiet origin
        git -C "${dir}" checkout --quiet "${commit}"
    fi
}

# A TOML basic string, for a cargo --config value.
toml_string() {
    local text="${1//\\/\\\\}"
    printf '"%s"' "${text//\"/\\\"}"
}

for tool in git cargo python3; do
    command -v "${tool}" >/dev/null 2>&1 || { echo "setup: ${tool} was not found." >&2; exit 1; }
done
if ! grep -q "${tiger_pkg_commit}" "${here}/tigerpkg-ffi/Cargo.toml"; then
    echo "setup: tigerpkg-ffi/Cargo.toml and setup.sh do not name the same commit of tiger-pkg." >&2
    exit 1
fi

mkdir -p "${area}/vendor" "${area}/runtime" "${area}/out"
clone_at "${tiger_pkg_url}" "${area}/vendor/tiger-pkg" "${tiger_pkg_commit}"
clone_at "${parser_url}" "${area}/vendor/tiger-animation-parser" "${parser_commit}"

# The parser has the d2_sk clip layout, but not the skeleton and rig layouts.
patch="${here}/patches/tiger-animation-parser-d2_sk.patch"
if git -C "${area}/vendor/tiger-animation-parser" apply --check "${patch}" 2>/dev/null; then
    git -C "${area}/vendor/tiger-animation-parser" apply "${patch}"
    echo "setup: applied the d2_sk patch to tiger-animation-parser."
elif ! git -C "${area}/vendor/tiger-animation-parser" apply --reverse --check "${patch}" 2>/dev/null; then
    echo "setup: the d2_sk patch does not apply to tiger-animation-parser." >&2
    exit 1
fi

# The manifest names tiger-pkg by its git commit. The patch gives cargo the clone, so cargo
# does not fetch tiger-pkg, and --locked keeps Cargo.lock in the source tree as it is.
echo "setup: building tigerpkg-ffi into ${area}/target ..."
cargo build --release --locked --quiet \
    --manifest-path "${here}/tigerpkg-ffi/Cargo.toml" \
    --target-dir "${area}/target" \
    --config "patch.'${tiger_pkg_url}'.tiger-pkg.path=$(toml_string "${area}/vendor/tiger-pkg")"

if [[ ! -x "${area}/venv/bin/python" ]]; then
    if command -v uv >/dev/null 2>&1; then
        uv venv --quiet "${area}/venv" --python 3.13
    else
        python3 -m venv "${area}/venv"
    fi
fi
if command -v uv >/dev/null 2>&1; then
    uv pip install --quiet --python "${area}/venv/bin/python" -r "${here}/requirements.txt"
else
    "${area}/venv/bin/pip" install --quiet -r "${here}/requirements.txt"
fi
# The environment, the parser and the patch: this import fails if one of them is not correct.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="${here}" FO4PORTS_DATA="${data}" \
    "${area}/venv/bin/python" -c "import d2x.anim, d2x.export, d2x.blender"

# linoodle loads the Windows Oodle DLL of the game from the working directory.
cp -f "${area}/vendor/tiger-pkg/liblinoodle3.so" "${area}/runtime/liblinoodle3.so"
game_dir="$(python3 "${root}/portkit/paths.py" get destiny_game || true)"
if [[ -z "${game_dir}" ]]; then
    echo "setup: the setting destiny_game has no value. All other steps are complete." >&2
    echo "setup: give the game folder in data/config.toml (destiny_game = \"...\") or in D2X_GAME, and run setup again." >&2
    exit 1
fi
oodle="${game_dir}/bin/x64/oo2core_3_win64.dll"
if [[ ! -f "${oodle}" ]]; then
    echo "setup: ${oodle} was not found. All other steps are complete." >&2
    echo "setup: the setting destiny_game (or D2X_GAME) must be the game folder that has packages/ and bin/x64/. Correct it and run setup again." >&2
    exit 1
fi
ln -sfn "${oodle}" "${area}/runtime/oo2core_3_win64.dll"

echo "setup: complete. Try: ./port destiny find \"last word\""
