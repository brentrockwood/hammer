"""Deterministic, public-safe retrieval fixtures and filesystem snapshots."""
import hashlib
import random
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

LABELS = ("HAMMER01", "ANVIL001", "CHISEL01", "MALLET01", "TONGS001")
TARGET = LABELS[0]
RECORD_BYTES = 256


@dataclass(frozen=True)
class Record:
    ordinal: int
    filename: str
    label: str
    content: str

    def public_manifest(self):
        item = asdict(self)
        item.pop("content")
        item["size"] = len(self.content.encode("ascii"))
        item["sha256"] = hashlib.sha256(self.content.encode("ascii")).hexdigest()
        return item


def generate_corpus(count, seed):
    """Generate fixed-size records with independently shuffled public attributes."""
    if count < 1:
        raise ValueError("count must be positive")
    filename_rng = random.Random(seed ^ 0x46494C45)
    label_rng = random.Random(seed ^ 0x4C414245)
    payload_rng = random.Random(seed ^ 0x5041594C)
    labels = []
    for start in range(0, count, len(LABELS)):
        block = list(LABELS[:min(len(LABELS), count - start)])
        label_rng.shuffle(block)
        labels.extend(block)
    filenames = []
    while len(filenames) < count:
        candidate = f"r-{filename_rng.getrandbits(80):020x}"
        if candidate not in filenames:
            filenames.append(candidate)
    records = []
    for ordinal, (filename, label) in enumerate(zip(filenames, labels), 1):
        nonce = f"{payload_rng.getrandbits(128):032x}"
        prefix = f"record={nonce} marker={label} payload="
        padding_length = RECORD_BYTES - len(prefix.encode("ascii")) - 1
        padding = "".join(
            chr(ord("a") + payload_rng.randrange(26)) for _ in range(padding_length)
        )
        content = prefix + padding + "\n"
        assert len(content.encode("ascii")) == RECORD_BYTES
        records.append(Record(ordinal, filename, label, content))
    return records


def creation_order(records, seed):
    ordered = list(records)
    random.Random(seed ^ 0x4F524445).shuffle(ordered)
    return ordered


def add_records(data_dir, records, seed):
    data_dir.mkdir(parents=True, exist_ok=True)
    ordered = creation_order(records, seed)
    for record in ordered:
        path = data_dir / record.filename
        if path.exists():
            if path.read_text(encoding="ascii") != record.content:
                raise RuntimeError(f"refusing to overwrite changed fixture {path.name}")
            continue
        path.write_text(record.content, encoding="ascii")
    return [record.filename for record in ordered]


def expected_filenames(records, target=TARGET):
    return sorted(record.filename for record in records if record.label == target)


def snapshot_tree(root):
    """Capture all persistent state; reject links because they violate the fixture model."""
    entries = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"symlinks are forbidden in persistent state: {relative}")
        if path.is_dir():
            entries.append({"path": relative, "type": "directory"})
            continue
        data = path.read_bytes()
        item = {
            "path": relative,
            "type": "file",
            "mode": stat.S_IMODE(mode),
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        if len(data) <= 8192:
            try:
                item["text"] = data.decode("utf-8")
            except UnicodeDecodeError:
                item["text_encoding"] = "non-UTF-8"
        entries.append(item)
    return entries


def snapshot_diff(before, after):
    left = {item["path"]: item for item in before}
    right = {item["path"]: item for item in after}
    return {
        "created": [right[path] for path in sorted(right.keys() - left.keys())],
        "deleted": [left[path] for path in sorted(left.keys() - right.keys())],
        "modified": [
            {"before": left[path], "after": right[path]}
            for path in sorted(left.keys() & right.keys())
            if left[path] != right[path]
        ],
    }
