#!/usr/bin/env python3
"""Materialize the Command-071 annotation package in the authoritative project root."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
PROJECT = ROOT / "top_journal_v3_reaudit_055"
OLD = ROOT / "annotation_tools/m4_angle_annotation"
TARGET = PROJECT / "annotation_tools/m4_angle_annotation"
REPORTS = ROOT / "reports"
FIELDS = [
    "assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
    "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip", "notes",
    "annotator_id", "annotation_timestamp_utc",
]


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


APP_PY = r'''#!/usr/bin/env python3
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
    annotator = PACKAGE / f"annotator_{slot}"
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
                        "full": f"annotations_{slot}",
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
    parser.add_argument("--slot", choices=["A", "B"], required=True)
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
'''

INDEX_HTML = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>M4 长边方向标注</title><link rel="stylesheet" href="/static/style.css"></head><body><header><strong>M4 OBB 几何长边方向</strong><span id="progress"></span><input id="annotator" placeholder="标注者 ID"></header><main><section class="workspace"><div class="viewer" id="viewer"><div class="canvas-wrap"><img id="image" alt="目标局部裁剪"><canvas id="overlay"></canvas></div></div><aside class="side-controls"><div class="angle">当前角度：<b id="angle">未标注</b></div><div class="nav-actions"><button id="next">下一个</button><button id="zoom">放大图片</button><button id="restore" disabled>还原图片</button><button id="prev">上一个</button></div><label class="state-option"><input type="checkbox" id="ambiguous"> 图片模糊或方向无法判断（ambiguous）</label><label class="state-option"><input type="checkbox" id="skip"> 图片损坏或目标不可见（skip）</label><div class="save-actions"><button id="save">保存</button><button id="export">导出 CSV + JSON</button></div><p id="status"></p></aside></section><section class="notes-panel"><label for="notes">备注（可选）</label><textarea id="notes" placeholder="仅在需要补充说明时填写"></textarea></section></main><script src="/static/app.js"></script></body></html>'''

APP_JS = r'''let tasks=[],slot="",index=0,records={},dirty=false,dragStart=null;
const $=id=>document.getElementById(id),img=$("image"),canvas=$("overlay"),ctx=canvas.getContext("2d"),viewer=$("viewer");
function current(){return tasks[index]} function record(){let id=current().task_id;return records[id]||(records[id]={angle:null,ambiguous:false,skip:false,notes:""})}
function normalize(a){return ((a%180)+180)%180} function done(r){return r&&(r.angle!==null||r.ambiguous||r.skip)}
function drawOn(target,context){context.clearRect(0,0,target.width,target.height);let x=target.width/2,y=target.height/2;context.strokeStyle="#00e0ff";context.lineWidth=2;context.beginPath();context.arc(x,y,7,0,Math.PI*2);context.stroke();let r=records[current()?.task_id];if(r&&r.angle!==null){let rad=r.angle*Math.PI/180,len=Math.min(target.width,target.height)*.38;context.strokeStyle="#ffcc33";context.lineWidth=3;context.beginPath();context.moveTo(x-Math.cos(rad)*len,y+Math.sin(rad)*len);context.lineTo(x+Math.cos(rad)*len,y-Math.sin(rad)*len);context.stroke()}}
function resize(){canvas.width=img.clientWidth;canvas.height=img.clientHeight;drawOn(canvas,ctx)}
function show(){let t=current(),r=record(),src="/images/"+t.crop_relpath.split("/").pop();img.src=src;$("angle").textContent=r.angle===null?"未标注":r.angle.toFixed(2)+"°";$("ambiguous").checked=r.ambiguous;$("skip").checked=r.skip;$("notes").value=r.notes||"";$("progress").textContent=`${index+1}/${tasks.length} · 已完成 ${Object.values(records).filter(done).length}`;drawOn(canvas,ctx)}
async function save(){let res=await fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({current_index:index,annotator_id:$("annotator").value,records})});if(!res.ok)throw Error(await res.text());dirty=false;$("status").textContent="已保存"}
async function load(){let data=await (await fetch("/api/tasks")).json();tasks=data.tasks;slot=data.slot;let state=await (await fetch("/api/state")).json();index=state.current_index||0;records=state.records||{};$("annotator").value=state.annotator_id||"";show()}
function changed(){dirty=true;clearTimeout(window.autosave);window.autosave=setTimeout(()=>save().catch(e=>$("status").textContent=e),700)}
canvas.onpointerdown=e=>{dragStart=[e.offsetX,e.offsetY]};canvas.onpointerup=e=>{if(!dragStart)return;let dx=e.offsetX-dragStart[0],dy=dragStart[1]-e.offsetY;if(Math.hypot(dx,dy)>5){let r=record();r.angle=normalize(Math.atan2(dy,dx)*180/Math.PI);r.ambiguous=r.skip=false;changed();show()}dragStart=null};
$("ambiguous").onchange=e=>{let r=record();r.ambiguous=e.target.checked;if(r.ambiguous){r.angle=null;r.skip=false}changed();show()};$("skip").onchange=e=>{let r=record();r.skip=e.target.checked;if(r.skip){r.angle=null;r.ambiguous=false}changed();show()};$("notes").oninput=e=>{record().notes=e.target.value;changed()};$("annotator").oninput=changed;
$("prev").onclick=async()=>{if(dirty)await save();index=Math.max(0,index-1);show()};$("next").onclick=async()=>{if(dirty)await save();index=Math.min(tasks.length-1,index+1);show()};$("save").onclick=()=>save().catch(e=>$("status").textContent=e);
$("zoom").onclick=()=>{let wrap=viewer.querySelector(".canvas-wrap"),current=wrap.getBoundingClientRect().width,max=Math.min(980,viewer.clientWidth-4);if(current>=max-1){$("zoom").disabled=true;return}let next=Math.min(max,Math.max(current+80,current*1.3));wrap.style.setProperty("--zoom-width",next+"px");viewer.classList.add("image-enlarged");$("restore").disabled=false;$("zoom").disabled=next>=max-1;setTimeout(resize,230)};$("restore").onclick=()=>{let wrap=viewer.querySelector(".canvas-wrap");viewer.classList.remove("image-enlarged");wrap.style.removeProperty("--zoom-width");$("zoom").disabled=false;$("restore").disabled=true;setTimeout(resize,230)};
$("export").onclick=async()=>{await save();let res=await fetch("/api/export",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({current_index:index,annotator_id:$("annotator").value,records})});let data=await res.json();$("status").textContent=res.ok?"已导出 CSV 和 JSON":data.error};img.onload=resize;window.onresize=resize;window.addEventListener("beforeunload",e=>{if(dirty){e.preventDefault();e.returnValue=""}});load();'''

STYLE_CSS = r'''*{box-sizing:border-box}body{margin:0;background:#15181c;color:#eef2f5;font:15px system-ui,sans-serif}header{height:54px;padding:10px 18px;background:#22272d;display:flex;gap:24px;align-items:center}header input{margin-left:auto;padding:7px;background:#111;color:white;border:1px solid #56606a}main{padding:18px}.workspace{display:grid;grid-template-columns:minmax(480px,1fr) 330px;gap:18px;align-items:start}.viewer{text-align:center;min-width:0;min-height:420px;display:flex;align-items:center;justify-content:center;background:#101318;border:1px solid #303840;overflow:auto}.canvas-wrap{position:relative;display:inline-block;max-width:100%;background:#090a0c;transition:width .2s ease}.canvas-wrap img{display:block;max-width:100%;max-height:72vh}.canvas-wrap canvas{position:absolute;inset:0;width:100%;height:100%;cursor:crosshair}.viewer.image-enlarged .canvas-wrap{width:min(100%,var(--zoom-width))}.viewer.image-enlarged .canvas-wrap img{width:100%;height:auto;max-height:none}.side-controls{display:flex;flex-direction:column;gap:14px;padding:16px;background:#22272d}.angle{padding:4px 0 10px;font-size:18px}.nav-actions{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px}.save-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.state-option{padding:12px;background:#171a1e;border:1px solid #46505a;line-height:1.45}.state-option input{margin-right:8px}.notes-panel{margin-top:16px;display:flex;flex-direction:column;gap:7px}.notes-panel textarea{width:100%;height:90px;background:#111;color:white;border:1px solid #56606a;padding:10px;resize:vertical}button{padding:11px;border:0;background:#d9e2e8;color:#111;cursor:pointer}button:hover{background:#fff}button:disabled{background:#687078;color:#d8dde0;cursor:not-allowed}#status{min-height:22px;margin:0;color:#9fe2b0}@media(max-width:900px){.workspace{grid-template-columns:1fr}.viewer{min-height:300px}.canvas-wrap img{max-height:58vh}.side-controls{grid-row:2}.nav-actions{grid-template-columns:1fr 1fr}}'''

README_ZH = """# M4 人工双标说明

## 标注目标

标注 OBB 的**几何长边朝向**，角度标准化到 `[0°, 180°)`。只考虑 180° 周期，不判断物体头尾或语义航向。

## 操作

1. 在图像上沿目标长边方向拖动鼠标，黄色线仅表示你当前输入的方向，数值显示在图像下方。
2. 使用“上一个/下一个”切换；切换和输入后会自动保存，也可点击“保存”。断开后用相同启动命令恢复。
3. near-square 目标若仍能可靠判断几何长边则标注；无法可靠区分两轴时选 `ambiguous`。
4. 遮挡或截断目标：只在可见证据足以判断长边时标注；方向存在但证据不足时选 `ambiguous`。
5. 图像损坏、目标不可见或无法确认被标实例时选 `skip`。
6. 不得参考其他标注者、GT、模型预测框、phase_mod 或 reliability score。青色中心圆仅用于指出目标中心，不编码方向。
7. 完成后点击“导出 CSV + JSON”。已有导出文件不会被覆盖。

## 输出位置

- A：`annotator_A/outputs/annotations_A.csv` 和 `annotations_A.json`
- B：`annotator_B/outputs/annotations_B.csv` 和 `annotations_B.json`

两名标注者必须独立工作，不得互看结果。
"""


def main() -> int:
    audit_rows = [
        {"check": "070_claimed_package", "status": "FOUND", "path": str(OLD),
         "evidence": "070 package exists in outer orientbench root"},
        {"check": "authoritative_project_root", "status": "MISSING_BEFORE_071",
         "path": str(PROJECT / "annotation_tools"), "evidence": "user ls matched top_journal_v3_reaudit_055"},
        {"check": "root_cause", "status": "PATH_SCOPE_ERROR", "path": str(OLD),
         "evidence": "070 materialized outside the authoritative manuscript/project subroot and did not state that distinction"},
    ]
    write_csv(REPORTS / "071_annotation_package_path_audit.csv", audit_rows,
              ["check", "status", "path", "evidence"])
    log = ["Command 071 annotation-package path audit",
           f"outer_repository_root={ROOT}", f"user_visible_project_root={PROJECT}",
           f"070_package_found={OLD}", f"required_071_target={TARGET}",
           "cause=PATH_SCOPE_ERROR: 070 used the outer repository root; user inspected the authoritative top_journal_v3_reaudit_055 root.",
           "070_validation_csv existed, but the 070 artifact manifest did not make the annotation package location authoritative."]
    (ROOT / "logs/071_annotation_package_path_audit.log").write_text("\n".join(log) + "\n")

    if not OLD.is_dir():
        raise RuntimeError("070 source package is missing")
    for slot in ("A", "B"):
        output = TARGET / f"annotator_{slot}/outputs"
        if output.exists() and any(output.iterdir()):
            raise RuntimeError(f"refuse to overwrite existing formal annotations: {output}")

    for path in (TARGET / "common/static", TARGET / "common/templates", TARGET / "internal"):
        path.mkdir(parents=True, exist_ok=True)
    (TARGET / "common/app.py").write_text(APP_PY)
    (TARGET / "common/templates/index.html").write_text(INDEX_HTML)
    (TARGET / "common/static/app.js").write_text(APP_JS)
    (TARGET / "common/static/style.css").write_text(STYLE_CSS)
    schema = {"schema_version": "m4-071-v1", "angle_period_degrees": 180,
              "angle_range": "[0,180)", "fields": FIELDS,
              "forbidden_display": ["gt_angle", "detector_prediction", "phase_mod", "reliability_score"]}
    (TARGET / "common/schema.json").write_text(json.dumps(schema, indent=2) + "\n")
    (TARGET / "README_ANNOTATOR_ZH.md").write_text(README_ZH)

    mapping_source = read_csv(OLD / "internal_mapping_070.csv")
    mapping_by_task = {(row["annotator_slot"], row["task_id"]): row for row in mapping_source}
    final_mapping = []
    slot_rows = {}
    for slot in ("A", "B"):
        source_rows = read_csv(OLD / f"annotator_{slot}/tasks.csv")
        package = TARGET / f"annotator_{slot}"
        images = package / "images"
        outputs = package / "outputs"
        images.mkdir(parents=True, exist_ok=True)
        outputs.mkdir(exist_ok=True)
        tasks = []
        for source in source_rows:
            name = Path(source["crop_relpath"]).name
            src = OLD / f"annotator_{slot}/crops" / name
            dst = images / name
            if not src.is_file():
                raise RuntimeError(f"missing source image: {src}")
            if not dst.exists():
                os.link(src, dst)
            elif sha256(src) != sha256(dst):
                raise RuntimeError(f"changed target image: {dst}")
            with Image.open(dst) as image:
                image.verify()
            task = {
                "assignment_version": "m4-071-final-v1", "annotator_slot": slot,
                "task_order": source["task_order"], "task_id": source["task_id"],
                "dataset": source["dataset"], "crop_relpath": f"images/{name}",
                "long_side_angle_deg_le90": "", "ambiguous": "", "skip": "", "notes": "",
                "annotator_id": "", "annotation_timestamp_utc": "",
            }
            tasks.append(task)
            old_map = mapping_by_task[(slot, source["task_id"])]
            final_mapping.append({
                "assignment_version": "m4-071-final-v1", "annotator_slot": slot,
                "task_id": source["task_id"], "canonical_anon_id": old_map["canonical_anon_id"],
                "dataset": source["dataset"], "task_order": source["task_order"],
                "image_sha256": sha256(dst), "source_070_path": str(src),
            })
        write_csv(package / "task_manifest.csv", tasks, FIELDS)
        (package / "task_manifest.json").write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n")
        (package / "README.md").write_text(f"Annotator {slot}: from this directory run `bash ../start_annotator_{slot}.sh`. Do not access `../internal/`.\n")
        slot_rows[slot] = tasks

    write_csv(TARGET / "internal/instance_id_mapping.csv", final_mapping, list(final_mapping[0]))
    manifest = read_csv(REPORTS / "m4_human_annotation_sampling_manifest.csv")
    summary = []
    for dataset in ("DIOR-R", "FAIR1M-v1.0", "SODA-A"):
        subset = [row for row in manifest if row["dataset"] == dataset]
        summary.append({"dataset": dataset, "instances": len(subset),
                        "ar21_instances": sum(row["formal_ar21_eligible"] == "True" for row in subset),
                        "source_manifest": "reports/m4_human_annotation_sampling_manifest.csv"})
    write_csv(TARGET / "internal/sampling_summary.csv", summary, list(summary[0]))

    start = """#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec /home/rspip/anaconda3/envs/mr_dev1x/bin/python "$ROOT/common/app.py" --slot SLOT --port PORT
"""
    for slot, port in (("A", 17801), ("B", 17802)):
        path = TARGET / f"start_annotator_{slot}.sh"
        path.write_text(start.replace("SLOT", slot).replace("PORT", str(port)))
        path.chmod(0o755)

    ids = {slot: {r["task_id"] for r in rows} for slot, rows in slot_rows.items()}
    canonical = {slot: {m["canonical_anon_id"] for m in final_mapping if m["annotator_slot"] == slot}
                 for slot in ("A", "B")}
    counts = {slot: Counter(r["dataset"] for r in rows) for slot, rows in slot_rows.items()}
    validation = {
        "status": "PACKAGE_MATERIALIZED_HUMAN_BLOCKED", "target": str(TARGET),
        "source_070": str(OLD), "counts": {slot: dict(counts[slot]) for slot in counts},
        "tasks_per_annotator": {slot: len(slot_rows[slot]) for slot in slot_rows},
        "anonymous_ids_unique": {slot: len(ids[slot]) == 1500 for slot in ids},
        "anonymous_ids_disjoint": not bool(ids["A"] & ids["B"]),
        "same_instance_set": canonical["A"] == canonical["B"],
        "different_order": [m["canonical_anon_id"] for m in final_mapping if m["annotator_slot"] == "A"] !=
                           [m["canonical_anon_id"] for m in final_mapping if m["annotator_slot"] == "B"],
        "formal_output_files": 0, "human_results": 0, "human_status": "HUMAN_BLOCKED",
    }
    (TARGET / "internal/validation_report.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps(validation))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
