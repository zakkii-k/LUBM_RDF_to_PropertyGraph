# 日本語バージョン (English version is below)
1. はじめに  
このリポジトリは，[LUBM](https://swat.cse.lehigh.edu/projects/lubm/ )のUBA1.7で生成したRDFデータをプロパティグラフに変換するものです．RDFデータは，run.shをUBA1.7のディレクトリで実行することで生成できます．また，実行時引数として整数値を与えることで大学数の指定ができます．その他オプションについてはUBA1.7のreadme.txtを確認してください．
2. 変換後のデータ構成
    - 頂点:
      - id: 1以上の唯一性の保証された整数値．
      - label: データのラベルの配列．typeで指定されたもの．
      - property: 文字列をキーに持つ辞書．owlにおけるDataTypePropertyで指定されたものや，uriなど．
    - エッジ:
      - id: 頂点と同様
      - label: owlにおけるObjectTypePropertyのlabel．
      - property: 頂点と同様．
      - src: エッジの始点となる頂点のidを持つ．
      - dst: エッジの終点となる頂点のidを持つ．
3. 出力されるデータ  
   1. nodes_{num}.json  
上記の頂点データを含むjsonファイル．
    2. edges_{num}.json  
    上記のエッジデータを含むjsonファイル．
4. 前準備  
   1. LUBMのデータ生成．  
   「はじめに」で書いてあるとおり，LUBMのデータを生成してください．
   2. ntriples形式への変換．  
   LUBMデータはowlで生成されるので，これをntriplesへ変換してください．変換は以下のコマンドで行えます．
      ```bash
      # 生成されたowlファイルはあらかじめowlディレクトリに入れておく．
      # 例: /hoge/fuga/owl/University0_0.owl
      ./owl2nt.sh /path/to/owl/dir
      ```
5. 実行方法  
   以下のコマンドを実行してください．
   ```bash
   python3 rdf2pg.py -o /path/to/univ_bench.owl -nt /path/to/ntriples/dir -j /path/to/json/dir/to/save -c chunk_size_num
   ```
   各引数は以下のような役割です．
   - -o または --owl_file:  
    owlファイルへのパス
   - -nt または --ntriples_dir:  
    前準備で生成したntファイルのある**ディレクトリ**へのパス．
   - -j または --json_dir_path:  
    生成したjsonファイルの出力先
   - -c または --chunk_size:  
    1つのjsonファイルに含むデータ(頂点やエッジ)の数．デフォルトでは10000．

# English version
1. Introduction  
This repository converts RDF data generated by [LUBM](https://swat.cse.lehigh.edu/projects/lubm/) UBA1.7 into a property graph. RDF data can be generated by running run.sh in the UBA1.7 directory. You can specify the number of universities by providing an integer as a runtime argument. For other options, please refer to UBA1.7's readme.txt.
2. Data Structure After Conversion
    - Vertex:
      - id: A unique integer value starting from 1.
      - label: An array of data labels specified by type.
      - property: A dictionary with string keys. Specified by DataTypeProperty in owl, uri, etc.
    - Edge:
      - id: Same as vertex.
      - label: The label of ObjectTypeProperty in owl.
      - property: Same as vertex.
      - src: The id of the vertex at the start of the edge.
      - dst: The id of the vertex at the end of the edge.
3. Output Data  
   1. nodes_{num}.json  
   A json file containing the vertex data mentioned above.
   2. edges_{num}.json  
   A json file containing the edge data mentioned above.
4. Preparation  
   1. Generate LUBM data.  
   As mentioned in the introduction, generate LUBM data.
   2. Convert to ntriples format.  
   LUBM data is generated in owl format, so convert it to ntriples. The conversion can be done with the following command:
      ```bash
      # Place the generated owl files in the owl directory in advance.
      # Example: /hoge/fuga/owl/University0_0.owl
      ./owl2nt.sh /path/to/owl/dir
      ```
5. Execution Method  
   Run the following command:
   ```bash
   python3 rdf2pg.py -o /path/to/univ_bench.owl -nt /path/to/ntriples/dir -j /path/to/json/dir/to/save -c chunk_size_num
   ```
   Each argument has the following roles:
   - -o or --owl_file:  
    Path to the owl file
   - -nt or --ntriples_dir:  
    Path to the directory containing the nt files generated in the preparation step.
   - -j or --json_dir_path:  
    Output destination of the generated json files
   - -c or --chunk_size:  
    The number of data (vertices or edges) included in one json file. The default is 10000.