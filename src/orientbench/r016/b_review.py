"""Review an existing r016 server snapshot offline; never access network or pixels.

The snapshot stores the explicitly scoped runs/r016 files as base64 with hashes.
Torrent decoding and published-table replay reuse existing code; they are not
claimed as second independent implementations. XML and source hashes are checked
directly against the retained response bodies.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

from orientbench.probes.multiview_geometry_support import audit
from orientbench.r016.metadata_audit import _bdecode, torrent_files


def compare_replay(saved, replayed) -> float:
    """Require identical structure/IDs/counts; tolerate only tiny float differences."""
    if type(saved) is not type(replayed):
        raise ValueError("replay value types differ")
    if isinstance(saved, dict):
        if saved.keys() != replayed.keys():
            raise ValueError("replay keys differ")
        return max((compare_replay(saved[k], replayed[k]) for k in saved), default=0.0)
    if isinstance(saved, list):
        if len(saved) != len(replayed):
            raise ValueError("replay list lengths differ")
        return max((compare_replay(a, b) for a, b in zip(saved, replayed)), default=0.0)
    if isinstance(saved, float):
        delta = abs(saved - replayed)
        if not math.isfinite(delta) or delta > 1e-10:
            raise ValueError("replay numeric difference exceeds 1e-10")
        return delta
    if saved != replayed:
        raise ValueError("replay discrete value differs")
    return 0.0


def review(snapshot_path: Path, table_path: Path, config_path: Path) -> dict:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    files = {}
    for name, item in snapshot.items():
        raw = base64.b64decode(item["base64"], validate=True)
        if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError(f"snapshot binding mismatch: {name}")
        files[name] = raw

    manifest = json.loads(files["artifacts/source_manifest.json"])
    source_checks = []
    for item in manifest["sources"]:
        name = "artifacts/sources/" + Path(item["path"]).name
        raw = files[name]
        if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError(f"source manifest mismatch: {name}")
        source_checks.append({"source": name, "url": item["url"],
                              "bytes": len(raw), "sha256": item["sha256"]})

    xml = ET.fromstring(files["artifacts/sources/sn4_atlanta.xml"])
    prefixes = [n.text for n in xml.findall("{*}CommonPrefixes/{*}Prefix")]
    products = [p for p in prefixes if "catid_" in p]
    example = ET.fromstring(files["artifacts/sources/sn4_example.xml"])
    child_prefixes = [n.text for n in example.findall("{*}CommonPrefixes/{*}Prefix")]
    torrent = files["artifacts/sources/dfc2019_track3_trainval.torrent"]
    decoded, end = _bdecode(torrent)
    if end != len(torrent):
        raise ValueError("torrent trailing data")
    metadata = [x for x in torrent_files(torrent) if x["path"] == "Track3-Metadata.zip"]
    html = files["artifacts/sources/dfc2019_dataport.html"].decode("utf-8")

    saved_proxy = json.loads(files["artifacts/published_table_geometry_proxy.json"])
    replay = audit(table_path, config_path)
    max_float_difference = compare_replay(saved_proxy, replay)
    retained_bytes = sum(x["bytes"] for x in source_checks)
    if retained_bytes != manifest["downloaded_bytes"]:
        raise ValueError("retained source byte count differs from manifest")

    return {
        "scope": "Offline review of retained responses, not a new native-metadata search or experiment.",
        "snapshot_sha256": hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
        "server_run_record": json.loads(files["RUN.json"]),
        "server_summary": json.loads(files["artifacts/RUN_SUMMARY.json"]),
        "source_checks": source_checks,
        "retained_sources_bytes": retained_bytes,
        "all_attempts_download_bytes": None,
        "accounting_limit": "Counters reset on program invocation; retained bodies do not establish all attempts' traffic.",
        "mvoi": {
            "directory_listing_truncated": xml.findtext("{*}IsTruncated"),
            "product_prefix_count": len(products),
            "other_prefixes": [p for p in prefixes if p not in products],
            "example_child_prefixes": child_prefixes,
            "sampled_product_directories": 1,
            "training_common_members_obtained": False,
            "native_record_support": "unknown",
            "counts_unit_correction": "27 denotes candidate product directories, not triples or independent verified acquisitions.",
            "search_limit": "One product directory was listed. No exhaustive native-metadata absence claim is supported.",
        },
        "us3d": {
            "metadata_manifest_entries": metadata,
            "torrent_decoder": "Reuses SERVER bencode parser; not independent decoding.",
            "torrent_has_http_webseed": any(k in decoded for k in (b"url-list", b"httpseeds")),
            "page_has_login_access_notice": "LOGIN TO ACCESS DATASET FILES" in html,
            "page_has_open_access_logged_in_notice": "accessible to all logged in" in html,
            "page_has_generic_subscription_modal": "This dataset requires an IEEE DataPort Subscription." in html,
            "metadata_entry_targets_access_modal": 'data-bs-target="#accessModal" class="refresh-get-customer">Track 3 / Metadata' in html,
            "authenticated_access_and_cost": "not verified; no promise that login alone supplies the package",
            "native_package_obtained": False,
        },
        "published_table_structure_counts_ids_equal": True,
        "published_table_exact_json_equal": saved_proxy == replay,
        "published_table_max_float_difference": max_float_difference,
        "published_table_float_tolerance": 1e-10,
        "published_table_counts": [{"case": r["case"], "period_deg": r["period_deg"],
                                     "triplets": r["catalogue_triplets"], "anchors": r["distinct_anchors"]}
                                    for r in replay["results"]],
        "stderr_has_earlier_import_failure": b"ModuleNotFoundError" in files["stderr.log"],
        "stderr_interpretation": "Retained error has no per-attempt time binding; current artifacts exist, but a complete attempt history is not proved.",
        "decision": "End bounded r016 with native support unknown. No model training or automatic next task.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(review(args.snapshot, args.table, args.config), ensure_ascii=False, indent=2, sort_keys=True))
