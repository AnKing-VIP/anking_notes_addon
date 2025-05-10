#!/usr/bin/env bash
declare DIR="$(cd "$(dirname "$0")/.." && pwd -P)"
set -e

"$DIR/tools/build.sh" &

cd "$DIR"
git submodule init

cd "$DIR/anki"
git submodule update
(
  # Start Anki
  ANKI_BASE="$DIR/ankidata" "$DIR/anki/tools/ts-run" &
  # Watch for changes in Anki TypeScript code
  "$DIR/anki/tools/ts-watch" &
  # Watch for changes in Add-on TypeScript code
  yarn --cwd "$DIR/ts" dev
)
