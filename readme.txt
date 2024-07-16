####################################################
Univ-Bench Artificial Data Generator (UBA)
  Version 1.7
  The Semantic Web and Agent Technologies (SWAT) Lab
  CSE Department, Lehigh University
####################################################

1. javac edu/lehigh/swat/bench/uba/Generator.java
2. java edu.lehigh.swat.bench.uba.Generator -onto https://swat.cse.lehigh.edu/onto/univ-bench.owl
その他オプションは任意で．

==================
USAGES
==================

command:
   Java edu.lehigh.swat.bench.uba.Generator
      	[-univ <univ_num>]
	[-index <starting_index>]
	[-seed <seed>]
	[-daml]
	-onto <ontology_url>

(http://swat.cse.lehigh.edu/onto/univ-bench.owl)

options:
   -univ number of universities to generate; 1 by default
   -index starting index of the universities; 0 by default
   -seed seed used for random data generation; 0 by default
   -daml generate DAML+OIL data; OWL data by default
   -onto url of the univ-bench ontology

- The package's path should be on CLASSPATH.

==================
Contact
==================

Yuanbo Guo	yug2@lehigh.edu

For more information about the benchmark, visit its homepage http://www.lehigh.edu/~yug2/Research/SemanticWeb/LUBM/LUBM.htm.
