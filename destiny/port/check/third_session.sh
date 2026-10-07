#!/bin/sh
# Build a mod, start a new game test session with its release, and print the session ID.
#   ./port destiny game session NAME LABEL [--cell ID | --world] [--no-build] [--take-over]
#   sh destiny/port/check/third_session.sh NAME LABEL ...
# NAME is the name of a mod: its sources are mods/NAME and its project is data/mods/NAME.
# LABEL is your name for the session (the probe shows it in `esx probe status`).
#   --cell ID    the cell where the game starts (default: QASmoke, a test cell of the game)
#   --world      give no cell: the game starts in the cell of the test world of the test
#                folder (`esx probe install --world FILE`; `esx probe status` shows it). An
#                esx version with no test world stays in the main menu then.
#   --no-build   do not build: start the session with the release that is there. Use it to
#                test the release that you tested before, with its bytes.
#   --take-over  stop the session of the session file also when it has another label. With
#                no --take-over the program stops then (exit code 1): a second user can
#                have started that session.
#
# The steps:
# 1. The program stops the session that it started before (the ID in the session file), and
#    no other session.
# 2. It builds the mod: `./port mod build NAME --update-lock`. When ./port is not there, it
#    runs the same esx command on data/mods/NAME (with no sync of mods/NAME). Not with --no-build.
# 3. It looks at `esx probe status`. The probe has one session at a time for the whole
#    computer. When a session is there that this program did not start, the program does not
#    start a session and has the exit code 1.
# 4. It starts the session with data/mods/NAME/build/release and prints the session ID.
#
# The session file is data/destiny/port/work/probe_session.txt, and the label of the session
# is in probe_session.txt.label. It is one file for all users of this repository. If the
# session of the file has another label than LABEL, the program does not stop it and has the
# exit code 1 (see --take-over).
# Stop a session with `esx probe stop --session ID`, with the ID that this program printed.
#
# The settings (./port gives them; else they come from portkit): the esx program (ESX_BIN),
# the Data folder of Fallout 4 (FO4_DATA), the Proton folder (PROTON_DIR).
usage() { sed -n '2,34p' "$0" | sed 's/^# \{0,1\}//'; }
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then usage; exit 0; fi
if [ $# -lt 2 ]; then usage >&2; exit 2; fi
NAME=$1
LABEL=$2
shift 2
CELL=QASmoke
BUILD=yes
TAKE=no
while [ $# -gt 0 ]; do
  case "$1" in
    --cell) [ $# -ge 2 ] || { usage >&2; exit 2; }; CELL=$2; shift 2 ;;
    --world) CELL=; shift ;;
    --no-build) BUILD=no; shift ;;
    --take-over) TAKE=yes; shift ;;
    *) usage >&2; exit 2 ;;
  esac
done
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
export PYTHONDONTWRITEBYTECODE=1
setting() { python3 "$ROOT/portkit/paths.py" get "$1"; }
ESX=${ESX_BIN:-$(setting esx)}
DATA=${FO4_DATA:-$(setting fo4_data)}
PROTON=${PROTON_DIR:-$(setting proton)}
STORE=${FO4PORTS_DATA:-$ROOT/data}
for pair in "esx:$ESX" "fo4_data:$DATA" "proton:$PROTON"; do
  if [ -z "${pair#*:}" ]; then
    echo "third_session.sh: the setting ${pair%%:*} has no value. Give it in data/config.toml (./port doctor shows each setting)." >&2
    exit 1
  fi
done
PROJECT=$STORE/mods/$NAME
if [ ! -d "$ROOT/mods/$NAME" ] && [ ! -d "$PROJECT" ]; then
  echo "third_session.sh: no mod has the name $NAME (mods/$NAME and data/mods/$NAME are not there)." >&2
  exit 1
fi
STATE=$STORE/destiny/port/work/probe_session.txt
mkdir -p "$(dirname "$STATE")"
if [ -f "$STATE" ]; then
  OLD=$(cat "$STATE.label" 2>/dev/null)
  if [ -n "$OLD" ] && [ "$OLD" != "$LABEL" ] && [ "$TAKE" != yes ]; then
    echo "third_session.sh: the session file has the session $(cat "$STATE") with the label $OLD, and your label is $LABEL. A second user can have started it, so this program does not stop it. Examine \`esx probe status\`. Give --take-over to stop it." >&2
    exit 1
  fi
  "$ESX" probe stop --session "$(cat "$STATE")" --format json >/dev/null 2>&1
  rm -f "$STATE" "$STATE.label"
fi
if [ "$BUILD" = no ]; then
  [ -d "$PROJECT/build/release" ] || { echo "third_session.sh: --no-build, and $PROJECT/build/release is not there." >&2; exit 1; }
elif [ -x "$ROOT/port" ]; then
  "$ROOT/port" mod build "$NAME" --update-lock >&2 || { echo "build: failed" >&2; exit 1; }
else
  "$ESX" --data "$DATA" build "$PROJECT" --update-lock --format json | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('build:', d['data']['summary']['result'] if d.get('ok') else json.dumps(d)[:600], file=sys.stderr)
sys.exit(0 if d.get('ok') else 1)" || exit 1
fi
# the probe has one session at a time: wait until the session that this program stopped is gone
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16; do
  p=$("$ESX" probe status --format json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)['data']
s=d.get('session') or {}
print('free' if not s and not d.get('fallout4_pids') else 'session %s with the label %s' % (s.get('id'), (s.get('owner') or {}).get('label')))")
  [ "$p" = "free" ] && break
  python3 -c "import time; time.sleep(4)"
done
if [ "$p" != "free" ]; then
  echo "third_session.sh: the probe is not free: $p. This program did not start that session, so it does not stop it. Examine \`esx probe status\`." >&2
  exit 1
fi
if [ -n "$CELL" ]; then set -- --cell "$CELL"; else set --; fi
"$ESX" probe start --mod "$PROJECT/build/release" "$@" --label "$LABEL" --timeout 300 --proton "$PROTON" --format json | STATE=$STATE LABEL=$LABEL python3 -c "
import json,os,sys
d=json.load(sys.stdin); x=d.get('data') or d.get('error')
if d.get('ok'):
    open(os.environ['STATE'],'w').write(x['session'])
    open(os.environ['STATE']+'.label','w').write(os.environ['LABEL'])
    print(x['session'])
else:
    print(json.dumps(x)[:400], file=sys.stderr); sys.exit(1)"
