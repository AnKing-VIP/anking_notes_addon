#!/usr/bin/env bash
declare DIR="$(cd "$(dirname "$0")/.." && pwd -P)"
set -e

git clean -fdx "$DIR/dist"

# Typescript
yarn --cwd "$DIR/ts" && yarn --cwd "$DIR/ts" build

# Python
rsync -rai "$DIR/src" "$DIR/dist" --filter=":- $DIR/.gitignore" --delete-after

echo 'Was successfully built!'
