import json
import shutil
import unittest
import uuid
from unittest.mock import patch

from corpus import TARGET, add_records, expected_filenames, generate_corpus
from runner import AgentContainer, ROOT, run_generation
from retrieval import generation_observations


class FakeLog:
    def __init__(self, path):
        self.public_path = path


class MemoryLog:
    run_id = "model-action-repair-test"

    def __init__(self):
        self.events = []

    def event(self, kind, **fields):
        self.events.append({"event": kind, **fields})


class FakeSettings:
    max_steps = 2
    num_ctx = 32768


class FakeClient:
    settings = FakeSettings()

    def __init__(self):
        self.messages = [
            {"role": "assistant", "content": '{"action":"close","fd":5}'},
            {"role": "assistant", "content": '{"action":"answer","answer":"recovered"}'},
        ]

    def ask(self, history):
        usage = {
            "prompt_tokens": 10, "completion_tokens": 5,
            "context_tokens_after_response": 15, "context_utilization": 0.0,
        }
        return self.messages.pop(0), usage


class FakeContainer:
    identity = {
        "container_id": "fake", "network_mode": "none",
        "read_only_root": True, "init": False, "mounts": [],
    }

    def start(self):
        return self

    def syscall(self, request):
        raise AssertionError("rejected action must not reach the adapter")

    def stop(self):
        return 0


class ApparatusTest(unittest.TestCase):
    def setUp(self):
        base = ROOT / ".work" / "tests"
        base.mkdir(parents=True, exist_ok=True)
        self.case_dir = base / uuid.uuid4().hex
        self.work_dir = self.case_dir / "work"
        self.work_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.case_dir, ignore_errors=True)

    def call(self, container, **request):
        response = container.syscall(request)
        self.assertEqual(response.get("op"), request["op"], response)
        return response

    def assert_isolated(self, container):
        self.assertEqual(container.identity["network_mode"], "none")
        self.assertIs(container.identity["read_only_root"], True)
        self.assertIs(container.identity["init"], False)
        self.assertEqual(
            [mount["destination"] for mount in container.identity["mounts"] if mount["rw"]],
            ["/work"],
        )

    def reference_retrieve(self, container, records):
        directory = self.call(
            container, op="openat", path="/work/data", mode="read_directory"
        )
        self.assertTrue(directory["ok"])
        rejected = self.call(
            container, op="getdents64", fd=directory["fd"], count=32
        )
        self.assertFalse(rejected["ok"], rejected)
        self.assertIsNone(rejected["syscall"])
        self.assertEqual(rejected["phase"], "validation")
        names = []
        pages = 0
        while True:
            page = self.call(
                container, op="getdents64", fd=directory["fd"], count=512
            )
            self.assertTrue(page["ok"], page)
            pages += 1
            names.extend(page["entries"])
            if page["eof"]:
                break
            self.assertLess(pages, 100)
        self.assertGreater(pages, 2)
        self.assertEqual(sorted(names), sorted(record.filename for record in records))
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(self.call(container, op="close", fd=directory["fd"])["ok"])

        observed = []
        for name in names:
            opened = self.call(
                container, op="openat", path=f"/work/data/{name}", mode="read"
            )
            read = self.call(container, op="read", fd=opened["fd"], count=4096)
            self.assertEqual(read["n"], 256)
            if TARGET in read["data"]:
                observed.append(name)
            self.assertTrue(self.call(container, op="close", fd=opened["fd"])["ok"])
        self.assertEqual(sorted(observed), expected_filenames(records))

    def test_hardened_adapter_and_reference_retrieval(self):
        records = generate_corpus(50, 20260818)
        self.assertTrue(all(len(record.content.encode("ascii")) == 256 for record in records))
        for block_start in range(0, 50, 5):
            self.assertEqual(
                {record.label for record in records[block_start:block_start + 5]},
                {"HAMMER01", "ANVIL001", "CHISEL01", "MALLET01", "TONGS001"},
            )
        add_records(self.work_dir / "data", records[:10], 20260819)
        outside = self.case_dir / "outside"
        outside.write_text("must not be reachable")
        (self.work_dir / "escape").symlink_to(self.case_dir)

        first = AgentContainer(
            "reference-" + uuid.uuid4().hex[:10], 1, self.work_dir
        ).start()
        try:
            self.assert_isolated(first)

            for path in ("/etc/passwd", "/work/../agent"):
                response = self.call(first, op="openat", path=path, mode="read")
                self.assertFalse(response["ok"], response)
            response = self.call(
                first, op="openat", path="/work/escape/outside", mode="read"
            )
            self.assertFalse(response["ok"], response)
            self.assertEqual(response["syscall"], "openat2")

            for request in (
                {"op": "close", "fd": 0},
                {"op": "write", "fd": 1, "data": "corrupt"},
                {"op": "read", "fd": 0, "count": 10},
                {"op": "getdents64", "fd": 0, "count": 32},
            ):
                response = self.call(first, **request)
                self.assertFalse(response["ok"], response)
                self.assertIsNone(response["syscall"])
                self.assertEqual(response["phase"], "validation")
            self.reference_retrieve(first, records[:10])
        finally:
            first.stop()

        add_records(self.work_dir / "data", records[10:], 20260820)
        container = AgentContainer(
            "reference-" + uuid.uuid4().hex[:10], 2, self.work_dir
        ).start()
        try:
            self.assert_isolated(container)
            self.reference_retrieve(container, records)

            roundtrip = 'quote:" backslash:\\ tab:\t newline:\n'
            opened = self.call(
                container, op="openat", path="/work/roundtrip",
                mode="write_create_truncate",
            )
            wrote = self.call(container, op="write", fd=opened["fd"], data=roundtrip)
            self.assertEqual(wrote["n"], len(roundtrip))
            self.call(container, op="close", fd=opened["fd"])
            opened = self.call(container, op="openat", path="/work/roundtrip", mode="read")
            read = self.call(container, op="read", fd=opened["fd"], count=4096)
            self.assertEqual(read["data"], roundtrip)
            json.dumps(read)
            self.call(container, op="close", fd=opened["fd"])
        finally:
            container.stop()

    def test_eof_observation_is_scored_separately_from_answer(self):
        path = self.case_dir / "trajectory.jsonl"
        rows = [
            {"event": "syscall_result", "generation": 1,
             "result": {"ok": True, "op": "getdents64", "eof": False}},
            {"event": "syscall_result", "generation": 1,
             "result": {"ok": True, "op": "read", "n": 256}},
        ]
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        observed = generation_observations(FakeLog(path), 1)
        self.assertFalse(observed["directory_eof_observed"])
        rows.append(
            {"event": "syscall_result", "generation": 1,
             "result": {"ok": True, "op": "getdents64", "eof": True}}
        )
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        observed = generation_observations(FakeLog(path), 1)
        self.assertTrue(observed["directory_eof_observed"])
        self.assertEqual(observed["directory_calls"], 2)
        self.assertEqual(observed["successful_reads"], 1)

    def test_invalid_model_action_is_returned_for_bounded_repair(self):
        log = MemoryLog()
        with patch("runner.AgentContainer", return_value=FakeContainer()):
            answer, _ = run_generation(
                log, FakeClient(), 1, "test prompt", max_steps=2
            )
        self.assertEqual(answer, "recovered")
        rejected = [
            event for event in log.events
            if event["event"] == "model_action_rejected"
        ]
        self.assertEqual(len(rejected), 1)
        self.assertIsNone(rejected[0]["rejection"]["syscall"])
        self.assertFalse(any(event["event"] == "generation_error" for event in log.events))


if __name__ == "__main__":
    unittest.main()
