#!/bin/bash
path=$1

# ntriplesディレクトリがなければ作成
mkdir -p "$path/ntriples"

# ファイルの数をカウント
total_files=$(ls $path/owl/*.owl | wc -l)
current_file=0

for file in $path/owl/*.owl; do
  base=$(basename "$file" .owl)
  current_file=$((current_file + 1))
  
  # プログレスバーを表示
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

# 最後に改行を追加
echo