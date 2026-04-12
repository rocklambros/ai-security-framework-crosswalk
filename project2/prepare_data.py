"""Pre-compute derived data from nodes.json and edges.json.

Run once at setup time:
    python prepare_data.py

Produces data/derived/*.json consumed by the Dash app at runtime.
NetworkX is used here for graph traversal but is NOT imported by the app.
"""

import json
import os
from collections import Counter, defaultdict

import networkx as nx


def load_raw(data_dir: str):
    """Load raw nodes and edges from JSON files."""
    with open(os.path.join(data_dir, "nodes.json")) as f:
        nodes = json.load(f)
    with open(os.path.join(data_dir, "edges.json")) as f:
        edges = json.load(f)
    return nodes, edges


def build_graph(nodes, edges):
    """Build a NetworkX DiGraph from nodes and edges."""
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["node_id"], **n)
    for e in edges:
        G.add_edge(
            e["source_node_id"],
            e["target_node_id"],
            **{k: v for k, v in e.items() if k not in ("source_node_id", "target_node_id")},
        )
    return G


def compute_framework_stats(nodes, edges):
    """Per-framework summary statistics."""
    node_map = defaultdict(list)
    for n in nodes:
        node_map[n["framework"]].append(n)

    edge_out = Counter()
    edge_in = Counter()
    for e in edges:
        edge_out[e["source_framework"]] += 1
        edge_in[e["target_framework"]] += 1

    stats = {}
    for fw, fw_nodes in node_map.items():
        stats[fw] = {
            "node_count": len(fw_nodes),
            "edge_count_out": edge_out.get(fw, 0),
            "edge_count_in": edge_in.get(fw, 0),
            "entry_type_counts": dict(Counter(n.get("entry_type", "") for n in fw_nodes)),
            "domain_counts": dict(Counter(n.get("domain", "") for n in fw_nodes if n.get("domain"))),
            "function_class_counts": dict(Counter(n.get("function_class", "") for n in fw_nodes if n.get("function_class"))),
        }
    return stats


def compute_hierarchy(nodes):
    """Build sunburst-compatible hierarchy per framework.

    Levels: framework root -> domain -> individual nodes.
    Uses domain as the grouping level. Nodes without a domain go under '(ungrouped)'.
    """
    fw_nodes = defaultdict(list)
    for n in nodes:
        fw_nodes[n["framework"]].append(n)

    hierarchy = {}
    for fw, ns in fw_nodes.items():
        ids = [fw]  # root
        labels = [fw]
        parents = [""]
        values = [0]  # root value will be sum

        # Group by domain
        domain_groups = defaultdict(list)
        for n in ns:
            domain = n.get("domain") or "(ungrouped)"
            domain_groups[domain].append(n)

        for domain, domain_nodes in sorted(domain_groups.items()):
            domain_id = f"{fw}::{domain}"
            ids.append(domain_id)
            labels.append(domain)
            parents.append(fw)
            values.append(0)

            for n in sorted(domain_nodes, key=lambda x: x["local_id"]):
                ids.append(n["node_id"])
                labels.append(f"{n['local_id']}: {n['name']}")
                parents.append(domain_id)
                values.append(1)

        hierarchy[fw] = {
            "ids": ids,
            "labels": labels,
            "parents": parents,
            "values": values,
        }
    return hierarchy


def compute_transitive_mappings(nodes, edges):
    """For every node, compute 1-hop (direct) and 2-hop (transitive) reachability.

    Direct: edges where this node is source or target (cross-framework only).
    Transitive: for each direct neighbor in another framework, follow THAT node's
    cross-framework edges to reach a third framework.

    Edges are bidirectional for reachability: if A->B exists, B can reach A.
    """
    node_map = {n["node_id"]: n for n in nodes}

    # Build adjacency: for each node, its cross-framework neighbors with edge metadata
    # We treat edges as undirected for reachability
    neighbors = defaultdict(list)
    for e in edges:
        src, tgt = e["source_node_id"], e["target_node_id"]
        src_fw = e.get("source_framework") or node_map.get(src, {}).get("framework")
        tgt_fw = e.get("target_framework") or node_map.get(tgt, {}).get("framework")
        if src_fw != tgt_fw:
            neighbors[src].append({
                "node_id": tgt,
                "framework": tgt_fw,
                "confidence": e.get("confidence"),
                "rationale_code": e.get("rationale_code"),
            })
            neighbors[tgt].append({
                "node_id": src,
                "framework": src_fw,
                "confidence": e.get("confidence"),
                "rationale_code": e.get("rationale_code"),
            })

    result = {}
    for n in nodes:
        nid = n["node_id"]
        nfw = n["framework"]

        # 1-hop: direct cross-framework neighbors
        direct = []
        for nb in neighbors.get(nid, []):
            direct.append({
                "target_node_id": nb["node_id"],
                "target_framework": nb["framework"],
                "target_name": node_map.get(nb["node_id"], {}).get("name", ""),
                "confidence": nb["confidence"],
                "rationale_code": nb["rationale_code"],
            })

        # 2-hop: for each direct neighbor, get THEIR cross-framework neighbors
        # that are in a DIFFERENT framework than both the original node and the bridge
        seen_direct = {d["target_node_id"] for d in direct}
        transitive = []
        for d in direct:
            bridge_id = d["target_node_id"]
            bridge_fw = d["target_framework"]
            bridge_name = node_map.get(bridge_id, {}).get("name", "")
            bridge_rationale = d["rationale_code"]

            for nb2 in neighbors.get(bridge_id, []):
                hop2_id = nb2["node_id"]
                hop2_fw = nb2["framework"]
                # Skip if it's the original node, already a direct neighbor,
                # or in the same framework as the original
                if hop2_id == nid or hop2_id in seen_direct or hop2_fw == nfw:
                    continue
                transitive.append({
                    "target_node_id": hop2_id,
                    "target_framework": hop2_fw,
                    "target_name": node_map.get(hop2_id, {}).get("name", ""),
                    "bridge_node_id": bridge_id,
                    "bridge_node_name": bridge_name,
                    "bridge_framework": bridge_fw,
                    "bridge_rationale": bridge_rationale,
                    "hop2_rationale": nb2["rationale_code"],
                    "hop2_confidence": nb2["confidence"],
                })

        # Deduplicate transitive: keep unique (target_node_id, bridge_node_id) pairs
        seen_trans = set()
        deduped_transitive = []
        for t in transitive:
            key = (t["target_node_id"], t["bridge_node_id"])
            if key not in seen_trans:
                seen_trans.add(key)
                deduped_transitive.append(t)

        if direct or deduped_transitive:
            result[nid] = {
                "direct": direct,
                "transitive": deduped_transitive,
            }

    return result


def compute_graph_metrics(nodes, edges):
    """Per-framework-pair edge stats and per-node degree metrics."""
    node_map = {n["node_id"]: n for n in nodes}

    # Framework pairs
    pair_data = defaultdict(lambda: {"edge_count": 0, "confidence_counts": Counter(), "rationale_counts": Counter()})
    for e in edges:
        src_fw = e["source_framework"]
        tgt_fw = e["target_framework"]
        if src_fw != tgt_fw:
            key = f"{src_fw}->{tgt_fw}"
            pair_data[key]["edge_count"] += 1
            pair_data[key]["confidence_counts"][e.get("confidence", "unknown")] += 1
            pair_data[key]["rationale_counts"][e.get("rationale_code", "unknown")] += 1

    # Serialize counters to dicts
    framework_pairs = {}
    for key, data in pair_data.items():
        framework_pairs[key] = {
            "edge_count": data["edge_count"],
            "confidence_counts": dict(data["confidence_counts"]),
            "rationale_counts": dict(data["rationale_counts"]),
        }

    # Node degrees
    out_degree = Counter()
    in_degree = Counter()
    cross_out = Counter()
    cross_in = Counter()
    for e in edges:
        out_degree[e["source_node_id"]] += 1
        in_degree[e["target_node_id"]] += 1
        if e["source_framework"] != e["target_framework"]:
            cross_out[e["source_node_id"]] += 1
            cross_in[e["target_node_id"]] += 1

    node_degrees = {}
    for n in nodes:
        nid = n["node_id"]
        node_degrees[nid] = {
            "out_degree": out_degree.get(nid, 0),
            "in_degree": in_degree.get(nid, 0),
            "cross_out": cross_out.get(nid, 0),
            "cross_in": cross_in.get(nid, 0),
        }

    return {"framework_pairs": framework_pairs, "node_degrees": node_degrees}


def compute_coverage_matrix(nodes, transitive_mappings):
    """For each (source_fw, target_fw) pair, compute what percentage of
    target_fw nodes are reachable from ANY node in source_fw.

    Uses both direct and transitive mappings.
    """
    fw_nodes = defaultdict(set)
    for n in nodes:
        fw_nodes[n["framework"]].add(n["node_id"])

    frameworks = sorted(fw_nodes.keys())
    matrix = {}

    for src_fw in frameworks:
        matrix[src_fw] = {}
        for tgt_fw in frameworks:
            if src_fw == tgt_fw:
                continue

            tgt_node_set = fw_nodes[tgt_fw]
            if not tgt_node_set:
                matrix[src_fw][tgt_fw] = {"total_pct": 0.0, "direct_pct": 0.0, "transitive_pct": 0.0}
                continue

            reached_direct = set()
            reached_transitive = set()
            reached_by_confidence = defaultdict(set)

            for src_nid in fw_nodes[src_fw]:
                mappings = transitive_mappings.get(src_nid, {})
                for d in mappings.get("direct", []):
                    if d["target_framework"] == tgt_fw:
                        reached_direct.add(d["target_node_id"])
                        conf = d.get("confidence", "unvalidated")
                        reached_by_confidence[conf].add(d["target_node_id"])
                for t in mappings.get("transitive", []):
                    if t["target_framework"] == tgt_fw:
                        reached_transitive.add(t["target_node_id"])
                        conf = t.get("hop2_confidence", "unvalidated")
                        reached_by_confidence[conf].add(t["target_node_id"])

            # Transitive-only = reached via transitive but NOT via direct
            transitive_only = reached_transitive - reached_direct
            all_reached = reached_direct | reached_transitive

            total = len(tgt_node_set)
            confidence_breakdown = {}
            for conf in ["authoritative", "expert", "suggestive", "unvalidated"]:
                count = len(reached_by_confidence.get(conf, set()))
                confidence_breakdown[conf] = {
                    "count": count,
                    "pct": round(count / total * 100, 1),
                }

            matrix[src_fw][tgt_fw] = {
                "total_pct": round(len(all_reached) / total * 100, 1),
                "direct_pct": round(len(reached_direct) / total * 100, 1),
                "transitive_pct": round(len(transitive_only) / total * 100, 1),
                "direct_count": len(reached_direct),
                "transitive_only_count": len(transitive_only),
                "total_reached": len(all_reached),
                "total_target": total,
                "by_confidence": confidence_breakdown,
            }

    return matrix


def save_json(data, path):
    """Write JSON with consistent formatting."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def prepare_all(data_dir: str, output_dir: str):
    """Run the full preparation pipeline."""
    nodes, edges = load_raw(data_dir)

    stats = compute_framework_stats(nodes, edges)
    save_json(stats, os.path.join(output_dir, "framework_stats.json"))

    hierarchy = compute_hierarchy(nodes)
    save_json(hierarchy, os.path.join(output_dir, "hierarchy.json"))

    transitive = compute_transitive_mappings(nodes, edges)
    save_json(transitive, os.path.join(output_dir, "transitive_mappings.json"))

    metrics = compute_graph_metrics(nodes, edges)
    save_json(metrics, os.path.join(output_dir, "graph_metrics.json"))

    coverage = compute_coverage_matrix(nodes, transitive)
    save_json(coverage, os.path.join(output_dir, "coverage_matrix.json"))

    print(f"Derived data written to {output_dir}/")
    print(f"  framework_stats.json  ({len(stats)} frameworks)")
    print(f"  hierarchy.json        ({len(hierarchy)} frameworks)")
    print(f"  transitive_mappings.json ({len(transitive)} nodes with mappings)")
    print(f"  graph_metrics.json    ({len(metrics['framework_pairs'])} pairs)")
    print(f"  coverage_matrix.json  ({len(coverage)} source frameworks)")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(here, "data")
    output_dir = os.path.join(data_dir, "derived")
    prepare_all(data_dir, output_dir)
