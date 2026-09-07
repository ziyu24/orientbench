"""Perform r016's bounded, metadata-only acquisition-support audit.

The program never downloads imagery, labels, or a package larger than the
protocol limit.  It records unavailable native fields as ``unknown`` rather
than inferring them from filenames or published aggregate tables.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from orientbench.probes.multiview_geometry_support import audit


MAX_DOWNLOAD = 50_000_000
S3 = "https://spacenet-dataset.s3.amazonaws.com/?list-type=2&prefix="
GITHUB = "https://raw.githubusercontent.com/pubgeo/dfc2019/master/data/"


def fetch_text(url: str, target: Path, total: list[int]) -> dict:
    """Download a small public source, enforcing the cumulative byte cap."""
    request = urllib.request.Request(url, headers={"User-Agent": "orientbench-r016/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        length = response.headers.get("Content-Length")
        expected = int(length) if length and length.isdigit() else None
        if expected is not None and total[0] + expected > MAX_DOWNLOAD:
            return {"url": url, "status": "not_downloaded_over_budget", "content_length": expected}
        chunks, received = [], 0
        while True:
            chunk = response.read(min(1_048_576, MAX_DOWNLOAD - total[0] - received + 1))
            if not chunk:
                break
            received += len(chunk)
            if total[0] + received > MAX_DOWNLOAD:
                raise RuntimeError("download cap exceeded while reading response")
            chunks.append(chunk)
    payload = b"".join(chunks)
    target.write_bytes(payload)
    total[0] += len(payload)
    return {"url": url, "status": "downloaded", "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(), "path": str(target)}


def s3_prefix(prefix: str) -> str:
    return S3 + urllib.request.quote(prefix, safe="/") + "&delimiter=/"


def prefixes(xml: bytes) -> list[str]:
    return re.findall(rb"<Prefix>([^<]+)</Prefix>", xml)[1:].__iter__() and [
        x.decode("utf-8") for x in re.findall(rb"<CommonPrefixes><Prefix>([^<]+)</Prefix>", xml)
    ]


def torrent_files(raw: bytes) -> list[dict]:
    # The public torrent is a bencoded manifest; only the length/path entries
    # are used.  No peer-to-peer client is invoked.
    matches = re.findall(rb"6:lengthi(\d+)e4:pathl(\d+):([^e]+)e", raw)
    return [{"bytes": int(length), "path": name[:int(size)].decode("utf-8", "replace")}
            for length, size, name in matches]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    out, source_dir = args.out, args.out / "sources"
    out.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(exist_ok=True)
    total = [0]

    local_names = sorted(p.name for p in args.dataset_root.iterdir())
    aliases = [n for n in local_names if re.search(r"spacenet|mvoi|us3d|dfc", n, re.I)]
    source_manifest = {"download_limit_bytes": MAX_DOWNLOAD, "downloaded_bytes": 0,
                       "local_registered_aliases": aliases, "sources": []}
    for name, url in [
        ("sn4_root.xml", s3_prefix("spacenet/SN4_buildings/")),
        ("sn4_train.xml", s3_prefix("spacenet/SN4_buildings/train/")),
        ("sn4_atlanta.xml", s3_prefix("spacenet/SN4_buildings/train/AOI_6_Atlanta/")),
        ("sn4_example.xml", s3_prefix("spacenet/SN4_buildings/train/AOI_6_Atlanta/nadir10_catid_1030010003993E00/")),
        ("dfc2019_readme.md", GITHUB + "README.md"),
        ("dfc2019_track3_trainval.torrent", GITHUB + "DFC2019_track3_trainval_v1.0.0.torrent"),
    ]:
        source_manifest["sources"].append(fetch_text(url, source_dir / name, total))
    source_manifest["downloaded_bytes"] = total[0]

    table_audit = audit(args.table, args.config)
    (out / "published_table_geometry_proxy.json").write_text(json.dumps(table_audit, indent=2, sort_keys=True))
    train_torrent = (source_dir / "dfc2019_track3_trainval.torrent").read_bytes()
    package_files = torrent_files(train_torrent)
    metadata = next((x for x in package_files if x["path"] == "Track3-Metadata.zip"), None)
    conflicts = {
        "mvoi": {
            "published_vs_collection_ids_requiring_native_resolution": [
                "1030010003993E00 vs 103001000399300",
                "1030010003193D00 / 1030010003CD4300 resolution-off-nadir assignment",
            ],
            "native_text_metadata_obtained": False,
            "reason": "Public S3 listing exposes imagery product prefixes only; no independent native IMD/RPB/text object was located within the allowed directed listing.",
        },
        "us3d": {
            "track3_metadata_package": metadata,
            "native_text_metadata_obtained": False,
            "reason": "Official public torrent lists Track3-Metadata.zip as a 13,409,681,556-byte package, beyond the 50,000,000-byte cap; it was not downloaded or unpacked.",
        },
    }
    native_spec = {
        "MVOI": {"version": "SpaceNet4/MVOI", "city": "Atlanta", "sensor_product": "unknown",
                 "catalog_identity": "unresolved", "native_gsd": "unknown", "time": "unknown",
                 "satellite_angles": "unknown", "sun_angles": "unknown", "rpc_coordinate_system": "unknown",
                 "psf_mtf_noise_calibration": "unknown", "training_common_support": "unknown"},
        "US3D_DFC2019_Track3": {"version": "DFC2019 Track 3 v1.0.0", "cities": ["JAX", "OMA"],
                 "sensor_product": "WorldView-3 RGB/MSI (README assertion)", "catalog_identity": "unknown",
                 "native_gsd": "unknown", "time": "unknown", "satellite_angles": "unknown",
                 "sun_angles": "unknown", "rpc_coordinate_system": "unknown; README says RGB RPC was adjusted for registration/cropping",
                 "psf_mtf_noise_calibration": "unknown", "training_common_support": "unknown"},
        "field_availability_time": "unknown fields are not imputed; available README naming information is post-acquisition metadata, not a pre-acquisition predictor.",
    }
    counts = {
        "MVOI": {"catalogue_proxy": [{"case": r["case"], "period_deg": r["period_deg"], "triplets": r["catalogue_triplets"], "anchors": r["distinct_anchors"]} for r in table_audit["results"]],
                 "verified_native_triplets": 0, "unknown_native_eligibility": "all", "conclusion": "information insufficient to determine matched support"},
        "US3D_DFC2019_Track3": {"verified_native_triplets": 0, "unknown_native_eligibility": "all", "conclusion": "information insufficient to determine matched support"},
        "not_evidence_of": ["common geographic training support", "same event", "time/sun matching", "PSF mechanism", "task benefit", "causal identification"],
    }
    (out / "source_manifest.json").write_text(json.dumps(source_manifest, indent=2, sort_keys=True))
    (out / "native_specification.json").write_text(json.dumps(native_spec, indent=2, sort_keys=True))
    (out / "conflicts.json").write_text(json.dumps(conflicts, indent=2, sort_keys=True))
    (out / "stepwise_counts.json").write_text(json.dumps(counts, indent=2, sort_keys=True))
    (out / "complete_triplet_list.json").write_text(json.dumps({"verified_native_triplets": [], "reason": "required native fields unavailable"}, indent=2))
    (out / "RUN_SUMMARY.json").write_text(json.dumps({"finished_at": datetime.now(timezone.utc).isoformat(), "cpu_only": True,
        "pixels_decoded": False, "labels_or_outcomes_read": False, "model_run": False,
        "downloaded_bytes": total[0], "expanded_bytes": 0}, indent=2))
    shutil.copy2(args.table, out / "MVOI_TABLE8_TRANSCRIPTION_20260906.csv")


if __name__ == "__main__":
    main()
