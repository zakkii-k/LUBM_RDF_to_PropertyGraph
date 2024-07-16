#!/bin/bash
path=$1

for file in $path/owl/*.owl; do
  base=$(basename "$file" .owl)
  riot --output=N-TRIPLES "$file" > "$path/ntriples/$base.nt"
done