#!/usr/bin/env bash

set -u -o pipefail

# Mount share, copy file(s), unmount share (scared of accidental rm -rf (which
# I've already done once))

dir="$(mktemp -d)"
sudo mount -v -t cifs //192.168.1.250/shared "$dir" -o user=Media,pass=Media,file_mode=0777,dir_mode=0777
function cleanup()
{
    sudo umount -v "$dir"
}
trap cleanup EXIT
files=("jr_yify.py")
dst="$dir"/Python
cp "${files[@]}" "$dst"
