#!/usr/bin/env python3
"""Export the only HRSC D_cal fields permitted before threshold sealing."""
import argparse
import csv
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prediction")
    parser.add_argument("output")
    parser.add_argument("--coverage", type=float, required=True)
    args = parser.parse_args()

    prediction = Path(args.prediction)
    output = Path(args.output)
    with prediction.open("rb") as handle:
        results = pickle.load(handle)

    rows = []
    for sample in results:
        image_id = str(sample["img_id"])
        scores = sample["pred_instances"]["scores"].detach().cpu().numpy()
        rows.extend((image_id, index, float(score)) for index, score in enumerate(scores))
    rows.sort(key=lambda row: (row[0], row[1]))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("image_id", "prediction_id", "score"))
        writer.writerows(rows)

    scores = np.asarray([row[2] for row in rows], dtype=np.float64)
    threshold = float(np.quantile(scores, 1.0 - args.coverage, method="higher"))
    print(json.dumps({
        "columns": ["image_id", "prediction_id", "score"],
        "prediction_count": len(rows),
        "threshold": threshold,
        "retained_prediction_count": int(np.count_nonzero(scores >= threshold)),
        "csv_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
