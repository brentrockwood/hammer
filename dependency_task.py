"""Deterministic dependency-ordering fixtures for the D96 pilot candidate."""
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DependencyNode:
    path: str
    dependencies: tuple[str, ...]

    def content(self):
        return f"depends={','.join(self.dependencies)}\n"


@dataclass(frozen=True)
class DependencyFixture:
    seed: int
    nodes: tuple[DependencyNode, ...]
    reference_order: tuple[str, ...]

    def node_by_path(self):
        return {node.path: node for node in self.nodes}

    def manifest(self):
        return {
            "fixture_seed": self.seed,
            "node_count": len(self.nodes),
            "nodes": [
                {
                    "path": node.path,
                    "dependency_count": len(node.dependencies),
                    "sha256": hashlib.sha256(node.content().encode()).hexdigest(),
                }
                for node in sorted(self.nodes, key=lambda item: item.path)
            ],
        }


def generate_fixture(seed, count=96):
    if count < 32:
        raise ValueError("D96 needs at least 32 nodes")
    names = []
    name_rng = random.Random(seed ^ 0x444E414D)
    while len(names) < count:
        path = f"/work/n/d-{name_rng.getrandbits(80):020x}"
        if path not in names:
            names.append(path)
    order = list(names)
    random.Random(seed ^ 0x444F5244).shuffle(order)
    edge_rng = random.Random(seed ^ 0x44454447)
    nodes = []
    for index, path in enumerate(order):
        if index == 0:
            dependencies = ()
        else:
            maximum = min(3, index)
            count_for_node = 1 if index < 6 else edge_rng.randint(1, maximum)
            dependencies = tuple(sorted(edge_rng.sample(order[:index], count_for_node)))
        nodes.append(DependencyNode(path, dependencies))
    fixture = DependencyFixture(seed, tuple(nodes), tuple(order))
    validate_fixture(fixture)
    return fixture


def validate_fixture(fixture):
    nodes = fixture.node_by_path()
    if len(nodes) != 96:
        raise ValueError("fixture must have exactly 96 unique nodes")
    if set(fixture.reference_order) != set(nodes):
        raise ValueError("reference order does not cover fixture")
    position = {path: index for index, path in enumerate(fixture.reference_order)}
    if any(
        dependency not in nodes or position[dependency] >= position[node.path]
        for node in fixture.nodes for dependency in node.dependencies
    ):
        raise ValueError("fixture dependencies are not acyclic")
    if any(len(node.content().encode()) > 4096 for node in fixture.nodes):
        raise ValueError("node exceeds one adapter read")


def write_fixture(root, fixture):
    node_dir = root / "n"
    node_dir.mkdir(parents=True, exist_ok=True)
    creation = list(fixture.nodes)
    random.Random(fixture.seed ^ 0x44435245).shuffle(creation)
    for node in creation:
        (node_dir / Path(node.path).name).write_text(node.content(), encoding="ascii")
    return [node.path for node in creation]


def validate_answer(text, fixture):
    lines = [line for line in text.splitlines() if line]
    nodes = fixture.node_by_path()
    if len(lines) != len(nodes):
        return False, f"order needs exactly {len(nodes)} nodes"
    if len(set(lines)) != len(lines):
        return False, "order repeats a node"
    if set(lines) != set(nodes):
        return False, "order does not name exactly the fixture nodes"
    position = {path: index for index, path in enumerate(lines)}
    if any(position[dependency] >= position[node.path]
           for node in fixture.nodes for dependency in node.dependencies):
        return False, "order violates a dependency"
    return True, "valid dependency order"
