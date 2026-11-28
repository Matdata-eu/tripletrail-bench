#!/bin/sh
# Downloads RMLMapper (MIT, https://github.com/RMLio/rmlmapper-java) to DIR/rmlmapper.jar
# (default data/), checked against its SHA-256. The jar holds its dependencies.
set -eu
VERSION=7.3.3
URL=https://github.com/RMLio/rmlmapper-java/releases/download/v$VERSION/rmlmapper-$VERSION-r374-all.jar
SHA=1f0d3f8830bd86bf02d6981718bbd812cad04c5d54e7404a68fb35e9c13b20bd
DIR=${1:-data}
mkdir -p "$DIR"
[ -f "$DIR/rmlmapper.jar" ] && echo "$SHA  $DIR/rmlmapper.jar" | sha256sum -c --quiet && exit 0
curl -sSfL -o "$DIR/rmlmapper.jar.part" "$URL"
echo "$SHA  $DIR/rmlmapper.jar.part" | sha256sum -c --quiet
mv "$DIR/rmlmapper.jar.part" "$DIR/rmlmapper.jar"
