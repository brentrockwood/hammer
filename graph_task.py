"""Deterministic graph fixtures and validation for the C48 compaction treatment."""
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GraphNode:
    path: str
    role: str
    successors: tuple[str, ...]

    def content(self):
        return f"role={self.role}\nnext={','.join(self.successors)}\n"


@dataclass(frozen=True)
class GraphFixture:
    seed: int
    entry: str
    terminal: str
    nodes: tuple[GraphNode, ...]
    backbone: tuple[str, ...]

    def node_by_path(self):
        return {node.path: node for node in self.nodes}

    def manifest(self):
        return {
            "fixture_seed": self.seed,
            "entry": self.entry,
            "terminal": self.terminal,
            "nodes": [
                {
                    "path": node.path,
                    "role": node.role,
                    "successors": list(node.successors),
                    "sha256": hashlib.sha256(node.content().encode()).hexdigest(),
                }
                for node in sorted(self.nodes, key=lambda item: item.path)
            ],
        }


def _opaque_paths(count, seed):
    rng = random.Random(seed ^ 0x4E414D45)
    paths = []
    while len(paths) < count:
        path = f"/work/n/g-{rng.getrandbits(80):020x}"
        if path not in paths:
            paths.append(path)
    return paths


def generate_graph(seed, count=48):
    if count < 24:
        raise ValueError("C48 graph needs at least 24 nodes")
    paths = _opaque_paths(count, seed)
    topology = random.Random(seed ^ 0x544F504F)
    ordering = random.Random(seed ^ 0x4F524445)
    backbone_indices = topology.sample(range(count), 16)
    backbone = tuple(paths[index] for index in backbone_indices)
    terminal = backbone[-1]
    distractors = [path for path in paths if path not in backbone]
    edges = {path: [] for path in paths}

    # The target can be reached through the backbone by more than one route;
    # successor order is separately randomized and gives no path-order cue.
    for index, path in enumerate(backbone[:-1]):
        edges[path].append(backbone[index + 1])
        if index == 4:
            edges[path].append(backbone[index + 2])
        if distractors:
            edges[path].append(distractors[index % len(distractors)])

    dead_ends = set(distractors[:3])
    cycle = distractors[3:7]
    for index, path in enumerate(cycle):
        edges[path].append(cycle[(index + 1) % len(cycle)])
    for path in distractors[7:]:
        choices = [candidate for candidate in distractors if candidate != path]
        edges[path].append(topology.choice(choices))
        if topology.random() < 0.35:
            edges[path].append(topology.choice(choices))
    for path in dead_ends:
        edges[path] = []
    for path, values in edges.items():
        ordering.shuffle(values)

    nodes = tuple(
        GraphNode(
            path=path,
            role="amber-terminal" if path == terminal else "ordinary",
            successors=tuple(edges[path]),
        )
        for path in paths
    )
    fixture = GraphFixture(seed, backbone[0], terminal, nodes, backbone)
    validate_fixture(fixture)
    return fixture


def validate_fixture(fixture):
    nodes = fixture.node_by_path()
    if len(nodes) != 48:
        raise ValueError("fixture must have exactly 48 unique nodes")
    if fixture.entry not in nodes or fixture.terminal not in nodes:
        raise ValueError("entry or terminal missing from node set")
    if sum(node.role == "amber-terminal" for node in nodes.values()) != 1:
        raise ValueError("fixture must have one terminal")
    if fixture.terminal in nodes[fixture.entry].successors:
        raise ValueError("fixture cannot have a direct entry-to-terminal edge")
    if any(len(node.content().encode()) > 4096 for node in nodes.values()):
        raise ValueError("node exceeds one adapter read")
    if len(set(fixture.backbone)) != len(fixture.backbone):
        raise ValueError("backbone repeats a node")
    for left, right in zip(fixture.backbone, fixture.backbone[1:]):
        if right not in nodes[left].successors:
            raise ValueError("backbone edge is absent")
    if fixture.terminal != fixture.backbone[-1]:
        raise ValueError("terminal must close backbone")
    if sum(not node.successors for node in nodes.values()) < 3:
        raise ValueError("fixture needs reachable-looking dead ends")


def write_fixture(root, fixture):
    node_dir = root / "n"
    node_dir.mkdir(parents=True, exist_ok=True)
    (root / "start").write_text(fixture.entry + "\n", encoding="ascii")
    creation = list(fixture.nodes)
    random.Random(fixture.seed ^ 0x43524541).shuffle(creation)
    for node in creation:
        path = node_dir / Path(node.path).name
        path.write_text(node.content(), encoding="ascii")
    return [node.path for node in creation]


def validate_answer(text, fixture):
    lines = [line for line in text.splitlines() if line]
    nodes = fixture.node_by_path()
    if len(lines) < 2:
        return False, "route needs at least entry and terminal"
    if lines[0] != fixture.entry:
        return False, "route does not start at entry"
    if lines[-1] != fixture.terminal:
        return False, "route does not end at terminal"
    if len(lines) != len(set(lines)):
        return False, "route repeats a node"
    if any(path not in nodes for path in lines):
        return False, "route names an unknown node"
    if any(
        right not in nodes[left].successors
        for left, right in zip(lines, lines[1:])
    ):
        return False, "route contains a non-edge"
    return True, "valid route"
