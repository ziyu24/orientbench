#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import socket
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PACKAGE = Path(__file__).resolve().parents[1]
FIELDS = ["assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
          "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip", "notes",
          "annotator_id", "annotation_timestamp_utc"]


def atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    os.replace(temp, path)


def free_port(start):
    port = start
    while port < 65535:
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError("no free local port")


def build_handler(slot, test_mode, task_set):
    annotator = PACKAGE
    manifest = annotator / ("task_manifest.json" if task_set == "full" else f"{task_set}/task_manifest.json")
    tasks = json.loads(manifest.read_text())
    task_ids = {row["task_id"] for row in tasks}
    output = annotator / ("test_outputs" if test_mode else
                          ("outputs" if task_set == "full" else f"outputs_{task_set}"))
    output.mkdir(exist_ok=True)
    draft = output / "draft_state.json"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(f"HTTP {self.address_string()} {fmt % args}", flush=True)

        def send_json(self, payload, status=200):
            data = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def send_file(self, path, mime):
            if not path.is_file():
                self.send_error(404)
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                return self.send_file(PACKAGE / "common/templates/index.html", "text/html; charset=utf-8")
            if path == "/static/app.js":
                return self.send_file(PACKAGE / "common/static/app.js", "text/javascript; charset=utf-8")
            if path == "/static/style.css":
                return self.send_file(PACKAGE / "common/static/style.css", "text/css; charset=utf-8")
            if path == "/api/tasks":
                return self.send_json({"slot": slot, "tasks": tasks, "test_mode": test_mode,
                                       "task_set": task_set})
            if path == "/api/state":
                state = json.loads(draft.read_text()) if draft.is_file() else {"current_index": 0, "annotator_id": "", "records": {}}
                return self.send_json(state)
            if path.startswith("/images/"):
                name = Path(path).name
                return self.send_file(annotator / "images" / name, "image/jpeg")
            self.send_error(404)

        def read_payload(self):
            size = int(self.headers.get("Content-Length", "0"))
            if size > 5_000_000:
                raise ValueError("payload too large")
            return json.loads(self.rfile.read(size) or b"{}")

        def validate_state(self, payload):
            records = payload.get("records", {})
            if not isinstance(records, dict) or not set(records).issubset(task_ids):
                raise ValueError("unknown task id")
            clean = {}
            for task_id, record in records.items():
                ambiguous = bool(record.get("ambiguous", False))
                skip = bool(record.get("skip", False))
                angle = record.get("angle")
                if angle in ("", None):
                    angle = None
                else:
                    angle = float(angle) % 180.0
                if sum((ambiguous, skip, angle is not None)) > 1:
                    raise ValueError("angle/ambiguous/skip are mutually exclusive")
                clean[task_id] = {"angle": angle, "ambiguous": ambiguous, "skip": skip,
                                  "notes": str(record.get("notes", ""))[:1000]}
            return {"current_index": max(0, min(int(payload.get("current_index", 0)), len(tasks) - 1)),
                    "annotator_id": str(payload.get("annotator_id", ""))[:100], "records": clean,
                    "saved_at_utc": datetime.now(timezone.utc).isoformat()}

        def do_POST(self):
            try:
                payload = self.read_payload()
                state = self.validate_state(payload)
                if self.path == "/api/save":
                    atomic_json(draft, state)
                    return self.send_json({"status": "saved", "records": len(state["records"])})
                if self.path == "/api/export":
                    stems = {
                        "full": "annotations_3",
                        "pilot_200": f"annotations_{slot}_pilot200",
                        "pilot_176_remaining": f"annotations_{slot}_pilot176_remaining",
                        "full_remaining": f"annotations_{slot}_full_remaining",
                        "b526_remaining": f"annotations_{slot}_b526_remaining",
                        "m600_plus_recheck": f"annotations_{slot}_m600_plus_recheck",
                    }
                    stem = stems[task_set]
                    csv_path, json_path = output / f"{stem}.csv", output / f"{stem}.json"
                    if csv_path.exists() or json_path.exists():
                        return self.send_json({"error": "export exists; refusing overwrite"}, HTTPStatus.CONFLICT)
                    now = datetime.now(timezone.utc).isoformat()
                    exported = []
                    for task in tasks:
                        record = state["records"].get(task["task_id"], {})
                        row = dict(task)
                        row["long_side_angle_deg_le90"] = "" if record.get("angle") is None else f"{record['angle']:.6f}"
                        row["ambiguous"] = "1" if record.get("ambiguous") else "0"
                        row["skip"] = "1" if record.get("skip") else "0"
                        row["notes"] = record.get("notes", "")
                        row["annotator_id"] = state["annotator_id"]
                        row["annotation_timestamp_utc"] = now if record else ""
                        exported.append(row)
                    tmp_csv = csv_path.with_suffix(".csv.tmp")
                    with tmp_csv.open("w", newline="") as handle:
                        writer = csv.DictWriter(handle, fieldnames=FIELDS)
                        writer.writeheader(); writer.writerows(exported)
                    os.replace(tmp_csv, csv_path)
                    atomic_json(json_path, exported)
                    return self.send_json({"status": "exported", "csv": str(csv_path), "json": str(json_path)})
                self.send_error(404)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=["3"], required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--test-mode", action="store_true")
    parser.add_argument(
        "--task-set",
        choices=["full", "pilot_200", "pilot_176_remaining", "full_remaining",
                 "b526_remaining", "m600_plus_recheck"],
        default="full",
    )
    args = parser.parse_args()
    port = free_port(args.port)
    server = ThreadingHTTPServer(("127.0.0.1", port), build_handler(args.slot, args.test_mode, args.task_set))
    print(f"ANNOTATOR_{args.slot}_URL=http://127.0.0.1:{port}/ test_mode={args.test_mode} task_set={args.task_set}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
