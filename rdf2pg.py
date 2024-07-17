import rdflib
import json
import glob
import os
import tqdm
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description="RDF to Property Graph Converter")
    parser.add_argument("-o", "--owl_file", required=True, help="Path to the OWL file")
    parser.add_argument(
        "-nt",
        "--ntriples_dir",
        required=True,
        help="Path to the N-Triples files (use wildcard for multiple files)",
    )
    parser.add_argument(
        "-j", "--json_dir_path", required=True, help="Directory path to save JSON files"
    )
    parser.add_argument(
        "-c",
        "--chunk_size",
        type=int,
        default=10000,
        help="Chunk size for JSON files (default: 10000)",
    )
    return parser.parse_args()


def load_owl_graph(owl_file):
    owl_graph = rdflib.Graph()
    owl_graph.parse(owl_file, format="xml")
    return owl_graph


def load_ntriples_graph(ntriples_dir):
    print(f"===== loading ntriples graph =====")
    g = rdflib.Graph()
    for file in tqdm.tqdm(glob.glob(os.path.join(ntriples_dir, "*.nt"))):
        g.parse(file, format="nt")
    return g


def replace_https_with_http(uri):
    if str(uri).startswith("https://"):
        return rdflib.URIRef(str(uri).replace("https://", "http://"))
    return uri


def extract_class_info(owl_graph):
    print(f"===== extracting class info =====")
    class_labels = {}
    dataTypeProperty = {}
    objectProperty = {}
    for subj, pred, obj in tqdm.tqdm(owl_graph):
        subj = replace_https_with_http(subj)
        pred = replace_https_with_http(pred)
        obj = replace_https_with_http(obj)

        if pred == rdflib.RDF.type and obj == rdflib.OWL.Class:
            class_labels[str(subj)] = str(subj).split("#")[-1]
        elif pred == rdflib.RDF.type and obj == rdflib.OWL.DatatypeProperty:
            dataTypeProperty[str(subj)] = str(subj).split("#")[-1]
        elif pred == rdflib.RDF.type and (
            obj == rdflib.OWL.ObjectProperty or obj == rdflib.OWL.TransitiveProperty
        ):
            objectProperty[str(subj)] = str(subj).split("#")[-1]
    return class_labels, dataTypeProperty, objectProperty


def process_node(uri, node_id_map, node_map, next_node_id):
    if uri not in node_id_map:
        node_id_map[uri] = next_node_id
        node_map[next_node_id] = {"id": next_node_id, "property": {"uri": uri}}
        next_node_id += 1
    return node_id_map[uri], next_node_id


def construct_property_graph(g, class_labels, dataTypeProperty, objectProperty):
    print(f"===== constructing property graph =====")
    node_map = {}
    edge_map = {}
    node_id_map = {}
    edge_id_map = {}
    next_node_id = 1
    next_edge_id = 1

    for subj, pred, obj in tqdm.tqdm(g):
        subj = replace_https_with_http(subj)
        pred = replace_https_with_http(pred)
        obj = replace_https_with_http(obj)
        subj = str(subj)
        pred = str(pred)
        obj = str(obj)
        if "file://" in subj or "file://" in pred or "file://" in obj:
            continue

        sub_id, next_node_id = process_node(subj, node_id_map, node_map, next_node_id)
        obj_id, next_node_id = process_node(obj, node_id_map, node_map, next_node_id)

        if pred in objectProperty:
            if (pred, sub_id, obj_id) not in edge_id_map:
                edge_id_map[(pred, sub_id, obj_id)] = next_edge_id
                edge_map[next_edge_id] = {
                    "id": next_edge_id,
                    "label": [objectProperty[pred]],
                    "src": sub_id,
                    "dst": obj_id,
                    "property": {"uri": pred},
                }
                next_edge_id += 1

        elif pred in dataTypeProperty:
            node_map[sub_id]["property"][dataTypeProperty[pred]] = obj
        elif "type" in str(pred):
            if "label" in node_map[sub_id]:
                node_map[sub_id]["label"].append(class_labels[obj])
            else:
                node_map[sub_id]["label"] = [class_labels[obj]]

    return node_map, edge_map


def write_json_in_chunks(data, file_prefix, dir_path, chunk_size=10000):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    print(f"===== writing {file_prefix} files =====")
    for i in tqdm.tqdm(range(0, len(data), chunk_size)):
        chunk = data[i : i + chunk_size]
        file_path = os.path.join(dir_path, f"{file_prefix}_{i // chunk_size + 1}.json")
        with open(file_path, "w") as file:
            json.dump(chunk, file, ensure_ascii=False, indent=4)


def main():
    args = parse_arguments()
    owl_graph = load_owl_graph(args.owl_file)
    rdf_graph = load_ntriples_graph(args.ntriples_dir)
    class_labels, dataTypeProperty, objectProperty = extract_class_info(owl_graph)
    node_map, edge_map = construct_property_graph(
        rdf_graph, class_labels, dataTypeProperty, objectProperty
    )

    node_list = list(node_map.values())
    edge_list = list(edge_map.values())

    write_json_in_chunks(node_list, "nodes", args.json_dir_path, args.chunk_size)
    write_json_in_chunks(edge_list, "edges", args.json_dir_path, args.chunk_size)


if __name__ == "__main__":
    main()
