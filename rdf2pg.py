import rdflib
import json
import glob
import os
import tqdm
import argparse


def main():
    # Setting command line arguments
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
    args = parser.parse_args()

    # Setting file paths
    owl_file = args.owl_file
    ntriples_dir = args.ntriples_dir
    json_dir_path = args.json_dir_path

    # Loading OWL graph
    owl_graph = rdflib.Graph()
    owl_graph.parse(owl_file, format="xml")

    # Loading RDF graph
    g = rdflib.Graph()

    print("===== reading ntriples files =====")
    for file in tqdm.tqdm(glob.glob(ntriples_dir)):
        g.parse(file, format="nt")

    # Extracting class information
    class_labels = {}
    dataTypeProperty = {}
    objectProperty = {}
    print("===== extracting class information =====")
    for subj, pred, obj in tqdm.tqdm(owl_graph):
        if str(subj).startswith("https://"):
            subj = rdflib.URIRef(str(subj).replace("https://", "http://"))
        if str(pred).startswith("https://"):
            pred = rdflib.URIRef(str(pred).replace("https://", "http://"))
        if str(obj).startswith("https://"):
            obj = rdflib.URIRef(str(obj).replace("https://", "http://"))

        if pred == rdflib.RDF.type and obj == rdflib.OWL.Class:
            class_labels[str(subj)] = str(subj).split("#")[-1]
        elif pred == rdflib.RDF.type and obj == rdflib.OWL.DatatypeProperty:
            dataTypeProperty[str(subj)] = str(subj).split("#")[-1]
        elif pred == rdflib.RDF.type and (
            obj == rdflib.OWL.ObjectProperty or obj == rdflib.OWL.TransitiveProperty
        ):
            objectProperty[str(subj)] = str(subj).split("#")[-1]
        else:
            print("subj:", subj, "pred:", pred, "obj:", obj)

    # Maps for property graph
    node_map = {}
    edge_map = {}
    # Data and id maps
    node_id_map = {}
    edge_id_map = {}
    next_node_id = 1
    next_edge_id = 1

    print("===== constructing node_map and edge_map =====")
    for subj, pred, obj in tqdm.tqdm(g):
        if str(subj).startswith("https://"):
            subj = rdflib.URIRef(str(subj).replace("https://", "http://"))
        if str(pred).startswith("https://"):
            pred = rdflib.URIRef(str(pred).replace("https://", "http://"))
        if str(obj).startswith("https://"):
            obj = rdflib.URIRef(str(obj).replace("https://", "http://"))
        subj = str(subj)
        pred = str(pred)
        obj = str(obj)
        if "file://" in subj or "file://" in pred or "file://" in obj:
            continue
        sub_id = -1
        obj_id = -1
        if subj not in node_id_map:  # When subj appears for the first time
            node_id_map[subj] = next_node_id
            node_map[next_node_id] = {"id": next_node_id, "property": {"uri": subj}}
            sub_id = next_node_id
            next_node_id += 1
        else:
            sub_id = node_id_map[subj]

        if pred in objectProperty:  # When pred acts as an edge in the property graph
            if obj not in node_id_map:  # When obj appears for the first time
                node_id_map[obj] = next_node_id
                node_map[next_node_id] = {"id": next_node_id, "property": {"uri": obj}}
                obj_id = next_node_id
                next_node_id += 1
            else:
                obj_id = node_id_map[obj]

            if (pred, sub_id, obj_id) not in edge_id_map:
                edge_id_map[(pred, sub_id, obj_id)] = next_edge_id
                edge_map[next_edge_id] = {
                    "id": next_edge_id,
                    "label": objectProperty[pred],
                    "src": sub_id,
                    "dst": obj_id,
                    "property": {"uri": pred},
                }
                next_edge_id += 1

        elif pred in dataTypeProperty:  # Property
            node_map[sub_id]["property"][dataTypeProperty[pred]] = obj
        elif "type" in str(pred):
            if "label" in node_map[sub_id]:
                node_map[sub_id]["label"].append(class_labels[obj])
            else:
                node_map[sub_id]["label"] = [class_labels[obj]]
        else:
            print("sub:", subj, "pred:", pred, "obj:", obj)

    # Create directory if it does not exist
    if not os.path.exists(json_dir_path):
        os.makedirs(json_dir_path)

    # Convert node_map to list format
    node_list = list(node_map.values())

    # Convert edge_map to list format
    edge_list = list(edge_map.values())

    def write_json_in_chunks(data, file_prefix, dir_path, chunk_size=10000):
        print(f"===== writing {file_prefix} files =====")
        for i in tqdm.tqdm(range(0, len(data), chunk_size)):
            chunk = data[i : i + chunk_size]
            file_path = os.path.join(
                dir_path, f"{file_prefix}_{i // chunk_size + 1}.json"
            )
            with open(file_path, "w") as file:
                json.dump(chunk, file, ensure_ascii=False, indent=4)

    print("===== writing json files =====")
    # Split node_list and output in json format
    write_json_in_chunks(node_list, "nodes", json_dir_path)

    # Split edge_list and output in json format
    write_json_in_chunks(edge_list, "edges", json_dir_path)


if __name__ == "__main__":
    main()
