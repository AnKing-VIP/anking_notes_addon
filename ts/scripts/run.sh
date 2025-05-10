#!/usr/bin/env bash
declare DIR="$(cd "$(dirname "$0")/.." && pwd -P)"
set -e

"$DIR/tools/build.sh"

cd "$DIR";
git submodule init

cd "$DIR/anki";
git submodule update
ANKI_BASE="$DIR/ankidata" "$DIR/anki/tools/ts-run"
