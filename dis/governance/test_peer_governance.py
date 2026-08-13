import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "dis" / "governance"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_validator():
    path = GOV / "validate_peer_governance.py"
    spec = importlib.util.spec_from_file_location("orientbench_peer_validator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PeerGovernanceContractTests(unittest.TestCase):
    def test_public_entrypoints_and_governance_files_exist(self):
        required = [
            ROOT / "AGENTS.md",
            ROOT / "CLAUDE.md",
            ROOT / "CC_PROMPT.md",
            ROOT / "dis" / "PEER_START.md",
            ROOT / "dis" / "coordination.json",
            GOV / "workers.json",
            GOV / "role_contract.json",
            GOV / "roles" / "B.md",
            GOV / "roles" / "C.md",
            GOV / "roles" / "SERVER.md",
            GOV / "validate_peer_governance.py",
        ]
        self.assertEqual([], [str(path.relative_to(ROOT)) for path in required if not path.is_file()])

    def test_worker_identity_is_account_independent_and_fail_closed(self):
        workers = load_json(GOV / "workers.json")
        self.assertEqual("paper.worker-id", workers["selector"]["git_config_key"])
        self.assertEqual("repo_local", workers["selector"]["scope"])
        self.assertEqual("fail_closed", workers["selector"]["missing_behavior"])
        self.assertEqual("B", workers["workers"]["peer-b-primary"]["role"])
        self.assertEqual("C", workers["workers"]["peer-c-primary"]["role"])
        self.assertEqual("SERVER", workers["workers"]["server-primary"]["role"])

    def test_b_and_c_have_mirror_capabilities_and_separate_ownership(self):
        contract = load_json(GOV / "role_contract.json")
        b = contract["actors"]["B"]
        c = contract["actors"]["C"]
        self.assertEqual(b["capabilities"], c["capabilities"])
        self.assertEqual("dis/B.md", b["owned_roots"]["memo"])
        self.assertEqual("dis/C.md", c["owned_roots"]["memo"])
        self.assertEqual("dis/plans/B", b["owned_roots"]["plans"])
        self.assertEqual("dis/plans/C", c["owned_roots"]["plans"])
        self.assertTrue(contract["visibility"]["role_rules_mutually_visible"])
        self.assertIsNone(contract["client_entrypoints"]["AGENTS.md"]["default_actor"])
        self.assertIsNone(contract["client_entrypoints"]["CLAUDE.md"]["default_actor"])

    def test_new_dispatch_slot_starts_idle_and_legacy_plan_is_archived_exactly(self):
        coordination = load_json(ROOT / "dis" / "coordination.json")
        self.assertEqual("B_C_PEER_EQUAL", coordination["governance_mode"])
        self.assertIsNone(coordination["active_dispatch"])
        self.assertFalse((ROOT / "dis" / "sug.md").exists())
        archive = ROOT / "dis" / "sug" / "orientbench-c-r020-measurement-validity-20260811-server-returned.md"
        self.assertTrue(archive.is_file())
        self.assertEqual(
            "74ef9c65eb660aa36fa6c7f5d78043a4f68540bff3d9903a9303ad6603c9abf5",
            hashlib.sha256(archive.read_bytes()).hexdigest(),
        )

    def test_entrypoints_restore_role_from_repo_local_selector(self):
        for relative in ("AGENTS.md", "CLAUDE.md", "CC_PROMPT.md", "dis/PEER_START.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("paper.worker-id", text, relative)
        protocol = (ROOT / "dis" / "collaboration_protocol.md").read_text(encoding="utf-8")
        self.assertIn("B/C 同级", protocol)
        self.assertNotIn("C 维护 active 合同与共享状态", protocol)

    def test_repository_validator_accepts_the_migrated_checkout(self):
        result = subprocess.run(
            [sys.executable, str(GOV / "validate_peer_governance.py"), str(ROOT)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("PEER_GOVERNANCE_OK", result.stdout)

    def test_validator_rejects_asymmetric_capabilities(self):
        validator = load_validator()
        contract = load_json(GOV / "role_contract.json")
        workers = load_json(GOV / "workers.json")
        coordination = load_json(ROOT / "dis" / "coordination.json")
        contract["actors"]["B"]["capabilities"].append("unilateral_veto")
        with self.assertRaises(validator.GovernanceError):
            validator.validate_documents(contract, workers, coordination)

    def test_validator_rejects_missing_server_worker(self):
        validator = load_validator()
        contract = load_json(GOV / "role_contract.json")
        workers = load_json(GOV / "workers.json")
        coordination = load_json(ROOT / "dis" / "coordination.json")
        del workers["workers"]["server-primary"]
        with self.assertRaises(validator.GovernanceError):
            validator.validate_documents(contract, workers, coordination)


if __name__ == "__main__":
    unittest.main()
