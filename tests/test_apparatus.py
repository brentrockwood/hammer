import json
import shutil
import unittest
import uuid
from unittest.mock import patch

from corpus import TARGET, add_records, expected_filenames, generate_corpus
from c48 import continuation_message, treatment_prompt
from dependency_task import generate_fixture as generate_dependency_fixture
from dependency_task import validate_answer as validate_dependency_answer
from graph_task import generate_graph, validate_answer, write_fixture
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


class CompactionFakeClient:
    settings = FakeSettings()

    def __init__(self):
        self.histories = []
        self.messages = [
            {"role": "assistant", "content": '{"action":"syscall","op":"close","fd":9}'},
            {"role": "assistant", "content": '{"action":"answer","answer":"done"}'},
        ]

    def ask(self, history):
        self.histories.append(list(history))
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
        if request == {"op": "close", "fd": 9}:
            return {"ok": True, "op": "close", "syscall": "close"}
        raise AssertionError("unexpected adapter request")

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

            rejected_append = self.call(
                container, op="openat", path="/work/roundtrip",
                mode="write_append_create",
            )
            self.assertFalse(rejected_append["ok"], rejected_append)
            self.assertIsNone(rejected_append["syscall"])
        finally:
            container.stop()

        append_container = AgentContainer(
            "append-" + uuid.uuid4().hex[:10], 1, self.work_dir,
            agent_args=("--append",),
        ).start()
        try:
            self.assert_isolated(append_container)
            opened = self.call(
                append_container, op="openat", path="/work/roundtrip",
                mode="write_append_create",
            )
            appended = "second line\n"
            wrote = self.call(append_container, op="write", fd=opened["fd"], data=appended)
            self.assertEqual(wrote["n"], len(appended))
            self.call(append_container, op="close", fd=opened["fd"])
            opened = self.call(append_container, op="openat", path="/work/roundtrip", mode="read")
            read = self.call(append_container, op="read", fd=opened["fd"], count=4096)
            self.assertEqual(read["data"], roundtrip + appended)
            self.call(append_container, op="close", fd=opened["fd"])
        finally:
            append_container.stop()

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

    def test_compaction_replaces_history_and_records_exact_continuation(self):
        log = MemoryLog()
        client = CompactionFakeClient()
        message = "Checkpoint 1 of 1 reached after model turn 1. Continue."
        with patch("runner.AgentContainer", return_value=FakeContainer()):
            answer, _ = run_generation(
                log, client, 1, "test prompt", max_steps=2,
                compaction_steps=(1,),
                compaction_message=lambda step, index, limit: message,
            )
        self.assertEqual(answer, "done")
        compaction = next(
            event for event in log.events if event["event"] == "context_compaction"
        )
        self.assertEqual(compaction["continuation_message"], message)
        self.assertEqual(
            client.histories[1],
            [
                {"role": "system", "content": "test prompt"},
                {"role": "user", "content": message},
            ],
        )

    def test_horizon_continuation_has_complete_sentences(self):
        self.assertEqual(
            continuation_message("horizon", 70, 1, 280),
            "Checkpoint 1 of 2 reached after model turn 70. The prior conversation "
            "transcript is no longer available. /work persists. Continue the same "
            "task. This run permits at most 280 model turns; at most 210 turns remain.",
        )

    def test_retained_tail_is_verbatim_and_precedes_continuation(self):
        log = MemoryLog()
        client = CompactionFakeClient()
        message = "Older messages are unavailable; retained tail follows."
        with patch("runner.AgentContainer", return_value=FakeContainer()):
            answer, _ = run_generation(
                log, client, 1, "test prompt", max_steps=2,
                compaction_steps=(1,), retain_history_turns=1,
                compaction_message=lambda step, index, limit: message,
            )
        self.assertEqual(answer, "done")
        self.assertEqual(client.histories[1][0], {"role": "system", "content": "test prompt"})
        self.assertEqual(client.histories[1][1]["content"], '{"action":"syscall","op":"close","fd":9}')
        self.assertTrue(client.histories[1][2]["content"].startswith("syscall result: "))
        self.assertEqual(client.histories[1][3], {"role": "user", "content": message})
        compaction = next(event for event in log.events if event["event"] == "context_compaction")
        self.assertEqual(compaction["retained_turns"], 1)
        self.assertEqual(compaction["retained_message_count"], 2)
        self.assertEqual(compaction["retained_step_start"], 1)

    def test_h12_prompt_declares_the_retained_tail(self):
        self.assertIn("last 12 complete action/result exchanges", treatment_prompt("h12"))

    def test_append_prompt_lists_only_the_enabled_affordance(self):
        self.assertNotIn("write_append_create", treatment_prompt("h0"))
        self.assertIn("write_append_create", treatment_prompt("h0", append_enabled=True))

    def test_c48_fixture_and_route_validator(self):
        fixture = generate_graph(20260819)
        creation = write_fixture(self.work_dir, fixture)
        self.assertEqual(len(creation), 48)
        self.assertTrue((self.work_dir / "start").exists())
        self.assertEqual(len(list((self.work_dir / "n").iterdir())), 48)
        valid, reason = validate_answer("\n".join(fixture.backbone) + "\n", fixture)
        self.assertTrue(valid, reason)
        invalid, _ = validate_answer("\n".join(reversed(fixture.backbone)) + "\n", fixture)
        self.assertFalse(invalid)

    def test_d96_fixture_and_dependency_validator(self):
        fixture = generate_dependency_fixture(20260820)
        self.assertEqual(len(fixture.nodes), 96)
        valid, reason = validate_dependency_answer(
            "\n".join(fixture.reference_order) + "\n", fixture
        )
        self.assertTrue(valid, reason)
        invalid, _ = validate_dependency_answer(
            "\n".join(reversed(fixture.reference_order)) + "\n", fixture
        )
        self.assertFalse(invalid)


if __name__ == "__main__":
    unittest.main()
