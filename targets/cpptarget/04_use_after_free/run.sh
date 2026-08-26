#!/usr/bin/env bash
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

g++ -std=c++17 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    vulnerable.cpp -o app

echo "[built] $DIR/app"
echo "[PoV replay]"
./app < "poc.txt" || true
