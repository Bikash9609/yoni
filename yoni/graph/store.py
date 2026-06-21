"""NetworkX-backed graph store."""

from __future__ import annotations

import networkx as nx

from yoni.graph.models import Edge, EdgeKind, KnowledgeGraph


class GraphStore:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph
        self._nx = nx.DiGraph()
        for node_id, node in graph.nodes.items():
            self._nx.add_node(node_id, **node.model_dump())
        for edge in graph.edges:
            self._nx.add_edge(
                edge.source,
                edge.target,
                kind=edge.kind.value,
                ref_raw=edge.ref_raw,
                resolved=edge.resolved,
            )

    def successors(self, node_id: str) -> list[str]:
        if node_id not in self._nx:
            return []
        return list(self._nx.successors(node_id))

    def predecessors(self, node_id: str) -> list[str]:
        if node_id not in self._nx:
            return []
        return list(self._nx.predecessors(node_id))

    def reverse_reachable(self, node_id: str) -> set[str]:
        if node_id not in self._nx:
            return set()
        return nx.ancestors(self._nx, node_id)

    def find_cycles(self, kinds: set[EdgeKind] | None = None) -> list[list[str]]:
        if kinds is None:
            simple = nx.simple_cycles(self._nx)
            return [list(c) for c in simple]
        subgraph = nx.DiGraph()
        for edge in self.graph.edges:
            if edge.kind in kinds:
                subgraph.add_edge(edge.source, edge.target)
        return [list(c) for c in nx.simple_cycles(subgraph)]

    def edges_of_kind(self, kind: EdgeKind) -> list[Edge]:
        return [edge for edge in self.graph.edges if edge.kind == kind]
