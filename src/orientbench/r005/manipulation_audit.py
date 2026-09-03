"""Frozen r005 image-cluster manipulation audit and Holm-32 calculation."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np


CONDITIONS = {"blur": ("blur_1.25", "blur_1.5"), "downsample": ("downsample_1.75", "downsample_2")}
MODELS = ("oriented_rcnn_r50", "rotated_rtmdet_m")
QS = ("J_eff", "M15")


def _image_means(records, field):
    grouped = {}
    for record in records:
        grouped.setdefault(str(record["image_id"]), []).append(float(record[field]))
    return {image_id: float(np.mean(values)) for image_id, values in grouped.items()}


def _holm(rows):
    ordered = sorted(range(len(rows)), key=lambda i: rows[i]["p"])
    adjusted = [0.0] * len(rows)
    ceiling = 0.0
    total = len(rows)
    for rank, index in enumerate(ordered):
        ceiling = max(ceiling, (total - rank) * rows[index]["p"])
        adjusted[index] = min(1.0, ceiling)
    for row, value in zip(rows, adjusted):
        row["holm_p"] = value
        row["passed"] = bool(row["theta"] > 0.0 and value <= 0.05)


def _bootstrap(theta, values, weights, threshold):
    values = np.asarray(values, dtype=float)
    theta_boot = (weights @ values) / weights.sum(axis=1)
    p = (1 + int(np.count_nonzero((theta_boot - theta) >= (theta - threshold)))) / (len(theta_boot) + 1)
    return p, np.quantile(theta_boot, [0.025, 0.975]).tolist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--loss", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--draws", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=5005)
    args = parser.parse_args()
    features = json.loads(args.features.read_text())
    loss = json.loads(args.loss.read_text())
    all_images = sorted({str(row["image_id"]) for row in features if row["split"] == "test"})
    generator = np.random.default_rng(args.seed)
    draw_indices = generator.integers(0, len(all_images), size=(10000, len(all_images)), dtype=np.int32)
    args.draws.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.draws, image_ids=np.array(all_images), draw_indices=draw_indices, seed=args.seed)
    image_positions = {image_id: index for index, image_id in enumerate(all_images)}
    weights = np.apply_along_axis(lambda row: np.bincount(row, minlength=len(all_images)), 1, draw_indices).astype(float)
    normalizers, rows = {}, []
    for model in MODELS:
        train = [r for r in features if r["model"] == model and r["split"] == "trainval" and r["condition"] == "clean" and r["arm"] == "G"]
        normalizers[model] = {}
        positive_m = [float(r["M15"]) for r in train if float(r["M15"]) > 0.0]
        epsilon = max(1e-12, 0.01 * float(np.median(positive_m))) if positive_m else 1e-12
        for quantity in QS:
            transformed = [(r["image_id"], np.log1p(r[quantity]) if quantity == "J_eff" else np.log(float(r[quantity]) + epsilon)) for r in train]
            values = _image_means(({"image_id": image_id, "x": value} for image_id, value in transformed), "x")
            normalizers[model][quantity] = {"epsilon": epsilon, "mean": float(np.mean(list(values.values()))), "sd": float(np.std(list(values.values()), ddof=1)), "images": len(values), "objects": len(train)}
        for quantity in QS:
            normalizer = normalizers[model][quantity]
            def zmap(condition, arm="G"):
                source = [r for r in features if r["model"] == model and r["split"] == "test" and r["condition"] == condition and r["arm"] == arm]
                transformed = []
                for r in source:
                    value = np.log1p(float(r[quantity])) if quantity == "J_eff" else np.log(float(r[quantity]) + normalizer["epsilon"])
                    transformed.append({"image_id": r["image_id"], "z": (value - normalizer["mean"]) / normalizer["sd"]})
                return _image_means(transformed, "z")
            clean = zmap("clean")
            envelope = max(abs(float(np.mean([zmap("clean", f"N{i}")[image] - clean[image] for image in clean]))) for i in range(6))
            for corruption, (low_label, high_label) in CONDITIONS.items():
                low, high = zmap(low_label), zmap(high_label)
                common = sorted(set(clean) & set(low) & set(high))
                statistics = (("clean-low", 0.0, np.array([clean[i] - low[i] for i in common])),
                              ("low-high", 0.0, np.array([low[i] - high[i] for i in common])),
                              ("clean-high", 0.20, np.array([clean[i] - high[i] - 0.20 for i in common])),
                              ("clean-high-EN", 0.0, np.array([clean[i] - high[i] - envelope for i in common])))
                for kind, threshold, values in statistics:
                    full_values = np.zeros(len(all_images), dtype=float)
                    for image, value in zip(common, values): full_values[image_positions[image]] = value
                    theta = float(np.mean(values))
                    p, ci = _bootstrap(theta, full_values, weights, 0.0)
                    rows.append({"model": model, "quantity": quantity, "corruption": corruption, "statistic": kind,
                                 "threshold": threshold, "theta": theta, "raw_change": theta + threshold,
                                 "n_images": len(common), "envelope": envelope, "p": p, "ci95": ci})
    _holm(rows)
    noncollapse = []
    for model in MODELS:
        test_cells = loss["models"][model]["test"]
        universe = test_cells[0]["objects"]
        for cell in test_cells:
            retained = cell["retained"]
            noncollapse.append({"model": model, "condition": cell["condition"], "universe_objects": universe,
                                "retained_objects": retained, "retention": retained / universe, "images": cell["images"],
                                "passed": retained >= .70 * universe and retained >= 100 and cell["images"] >= 50})
    answer = {"normalizers": normalizers, "manipulation_holm32": rows, "noncollapse": noncollapse,
              "all_first_three_pass": all(row["passed"] for row in rows if row["statistic"] != "clean-high-EN"),
              "all_envelope_pass": all(row["passed"] for row in rows if row["statistic"] == "clean-high-EN"),
              "all_noncollapse_pass": all(row["passed"] for row in noncollapse),
              "draws": str(args.draws), "seed": args.seed}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(answer, indent=2) + "\n")


if __name__ == "__main__":
    main()
