#!/bin/bash

year=$(date +%Y)
if [ $# -eq 0 ]; then
  src=.
else
  src=$1
fi
echo "Source path: $src"

UNAME_S=$(uname -s)
if [ "$UNAME_S" = "Darwin" ]; then
  SED=gsed
else
  SED=sed
fi

echo "Module name:"
read module

echo "Author name:"
read author

echo "Release version:"
read version

$SED -i "s/__AUTHORNAME__/$author/g" docs/*.* pyproject.toml
$SED -i "s/__MODULENAME__/$module/g" docs/*.* README.md
$SED -i "s/__YEAR__/$year/g" docs/*.*
$SED -i "s/__RELEASE__/$version/g" docs/*.* pyproject.toml
$SED -i "s/__SRCPATH__/../g" docs/*.* 
$SED -i "s/__SRCPATH__/./g" build_docs.sh
$SED -i "s/__SRCPATH__/$src/g" pyproject.toml
$SED -i "/Copyright (c)/c\\Copyright (c) $year $author" LICENSE