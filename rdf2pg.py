import rdflib
import json
import glob
import os
import tqdm
import argparse
import shutil
from owlready2 import *


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
    subClassOf = {}
    dataTypeProperty = {}
    objectProperty = {}
    transitiveProperty = {}

    # First, extract all class labels and properties
    for subj, pred, obj in tqdm.tqdm(owl_graph):
        subj = replace_https_with_http(subj)
        pred = replace_https_with_http(pred)
        obj = replace_https_with_http(obj)

        # ブランクノードを無視
        if isinstance(subj, rdflib.BNode) or isinstance(obj, rdflib.BNode):
            continue

        if pred == rdflib.RDF.type and obj == rdflib.OWL.Class:
            class_labels[str(subj)] = str(subj).split("#")[-1]
        elif pred == rdflib.RDF.type and obj == rdflib.OWL.DatatypeProperty:
            dataTypeProperty[str(subj)] = str(subj).split("#")[-1]
        elif pred == rdflib.RDF.type and (obj == rdflib.OWL.ObjectProperty):
            objectProperty[str(subj)] = str(subj).split("#")[-1]
        elif pred == rdflib.RDF.type and obj == rdflib.OWL.TransitiveProperty:
            transitiveProperty[str(subj)] = str(subj).split("#")[-1]

    # Next, process subclass and intersectionOf relationships
    for subj, pred, obj in tqdm.tqdm(owl_graph):
        subj = replace_https_with_http(subj)
        pred = replace_https_with_http(pred)
        obj = replace_https_with_http(obj)

        # ignore blank nodes
        if isinstance(subj, rdflib.BNode) or isinstance(obj, rdflib.BNode):
            continue

        if pred == rdflib.RDFS.subClassOf:
            if str(subj) not in subClassOf:
                subClassOf[str(subj)] = []
            subClassOf[str(subj)].append(str(obj))
        elif pred == rdflib.OWL.intersectionOf:
            # Handle intersectionOf to treat it as a subClassOf relationship
            collection = obj
            for item in owl_graph.items(collection):
                if isinstance(item, rdflib.URIRef) and str(item) in class_labels:
                    if str(subj) not in subClassOf:
                        subClassOf[str(subj)] = []
                    subClassOf[str(subj)].append(str(item))

    return (
        class_labels,
        subClassOf,
        dataTypeProperty,
        objectProperty,
        transitiveProperty,
    )


def add_inferred_subclasses(owl_file, subClassOf):
    onto = get_ontology(owl_file).load()
    with onto:
        sync_reasoner()

    for cls in onto.classes():
        for subclass in cls.subclasses():
            if str(subclass.iri) not in subClassOf:
                subClassOf[str(subclass.iri)] = []
            subClassOf[str(subclass.iri)].append(str(cls.iri))
    return subClassOf


def process_node(uri, node_id_map, node_map, next_node_id):
    if uri not in node_id_map:
        node_id_map[uri] = next_node_id
        node_map[next_node_id] = {"id": next_node_id, "property": {"uri": uri}}
        next_node_id += 1
    return node_id_map[uri], next_node_id


def get_all_super_classes(cls, subClassOf, visited=None):
    if visited is None:
        visited = set()
    if cls in visited:
        return set()
    visited.add(cls)
    super_classes = set()
    if cls in subClassOf:
        for super_cls in subClassOf[cls]:
            super_classes.add(super_cls)
            super_classes.update(get_all_super_classes(super_cls, subClassOf, visited))
    return super_classes


def get_all_transitive_relations(uri, transitive_relations, visited=None):
    if visited is None:
        visited = set()
    if uri in visited:
        return set()
    visited.add(uri)
    relations = set()
    if uri in transitive_relations:
        for related_uri in transitive_relations[uri]:
            relations.add(related_uri)
            relations.update(
                get_all_transitive_relations(related_uri, transitive_relations, visited)
            )
    return relations


def construct_property_graph(
    g, class_labels, subClassOf, dataTypeProperty, objectProperty, transitiveProperty
):
    print(f"===== constructing property graph =====")
    node_map = {}
    edge_map = {}
    node_id_map = {}
    edge_id_map = {}
    next_node_id = 1
    next_edge_id = 1

    transitive_relations = {prop: {} for prop in transitiveProperty}
    for subj, pred, obj in tqdm.tqdm(g):
        subj = replace_https_with_http(subj)
        pred = replace_https_with_http(pred)
        obj = replace_https_with_http(obj)

        if str(pred) in transitiveProperty:
            if str(subj) not in transitive_relations[str(pred)]:
                transitive_relations[str(pred)][str(subj)] = []
            transitive_relations[str(pred)][str(subj)].append(str(obj))
    for subj, pred, obj in tqdm.tqdm(g):
        subj = replace_https_with_http(subj)
        pred = replace_https_with_http(pred)
        obj = replace_https_with_http(obj)
        subj = str(subj)
        pred = str(pred)
        obj = str(obj)
        if (
            "file://" in subj
            or "file://" in pred
            or "file://" in obj
            or isinstance(subj, rdflib.BNode)
            or isinstance(obj, rdflib.BNode)
        ):
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
            labels = set()
            if obj in class_labels:
                labels.add(class_labels[obj])
            super_classes = get_all_super_classes(obj, subClassOf)
            for super_cls in super_classes:
                if super_cls in class_labels:
                    labels.add(class_labels[super_cls])
            if labels:
                if "label" in node_map[sub_id]:
                    node_map[sub_id]["label"].extend(list(labels))
                    node_map[sub_id]["label"] = list(set(node_map[sub_id]["label"]))
                else:
                    node_map[sub_id]["label"] = list(labels)

    # Handle all transitive relations
    for prop, relations in transitive_relations.items():
        for subj, objs in relations.items():
            subj = str(subj)
            all_related_objs = get_all_transitive_relations(subj, relations)
            for related_obj in all_related_objs:
                if (prop, subj, related_obj) not in edge_id_map:
                    sub_id = node_id_map[subj]
                    obj_id = node_id_map[related_obj]
                    edge_id_map[(prop, subj, related_obj)] = next_edge_id
                    edge_map[next_edge_id] = {
                        "id": next_edge_id,
                        "label": [transitiveProperty[prop]],
                        "src": sub_id,
                        "dst": obj_id,
                        "property": {"uri": prop},
                    }
                    next_edge_id += 1

    return node_map, edge_map


def write_json_in_chunks(data, file_prefix, dir_path, chunk_size=10000):
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
    class_labels, subClassOf, dataTypeProperty, objectProperty, transitiveProperty = (
        extract_class_info(owl_graph)
    )
    subClassOf = add_inferred_subclasses(args.owl_file, subClassOf)
    node_map, edge_map = construct_property_graph(
        rdf_graph,
        class_labels,
        subClassOf,
        dataTypeProperty,
        objectProperty,
        transitiveProperty,
    )

    node_list = list(node_map.values())
    edge_list = list(edge_map.values())
    if os.path.exists(args.json_dir_path):
        shutil.rmtree(args.json_dir_path)
    os.makedirs(args.json_dir_path)
    write_json_in_chunks(node_list, "nodes", args.json_dir_path, args.chunk_size)
    write_json_in_chunks(edge_list, "edges", args.json_dir_path, args.chunk_size)


if __name__ == "__main__":
    main()
