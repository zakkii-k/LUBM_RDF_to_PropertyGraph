#!/bin/bash
path=$1

# create ntriples directory if it doesn't exist
mkdir -p "$path/ntriples"

# count the number of files
total_files=$(ls $path/owl/*.owl | wc -l)
current_file=0

for file in $path/owl/*.owl; do
  base=$(basename "$file" .owl)
  current_file=$((current_file + 1))
  
  # show progress bar
  progress=$(echo "$current_file $total_files" | awk '{printf "%.2f", $1/$2 * 100}')
  echo -ne "Processing: $current_file/$total_files ["
  for ((i=0; i<50; i++)); do
    if [ $i -lt $((current_file * 50 / total_files)) ]; then
      echo -ne "#"
    else
      echo -ne " "
    fi
  done
  echo -ne "] $progress%\r"
  
  riot --output=N-TRIPLES "$file" > "$path/ntriples/$base.nt"
done

# add a newline at the end
echo