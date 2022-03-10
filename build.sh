#!/bin/bash

set -e

DIR="$(basename "$(readlink -f ".")")"

cd ..
zip -r "$DIR/$DIR.zip" "$DIR"
