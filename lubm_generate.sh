#!/bin/bash

DEFAULT_UNIV=1

UNIV=${1:-$DEFAULT_UNIV}

if [ ! -d "bin" ]; then
  mkdir -p bin
  echo "Created bin directory"
else
  echo "bin directory already exists"
fi

javac -d bin src/edu/lehigh/swat/bench/uba/*.java

java -cp bin edu.lehigh.swat.bench.uba.Generator -univ $UNIV -onto https://swat.cse.lehigh.edu/onto/univ-bench.owl