"""Freeze r017 inputs from native support and filenames, before pixel inspection."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

TRIPLETS = [
    ["1030010003472200", "10300100036D5200", "1030010003315300"],
    ["103001000392F600", "1030010003315300", "10300100036D5200"],
]


def build(inventory_path, support_path):
    inventory = json.loads(inventory_path.read_text())
    support = json.loads(support_path.read_text())
    pool = sorted(t for t, triples in support["by_tile"].items() if all(v in triples for v in TRIPLETS))

    def tile_key(t):
        return hashlib.sha256(("orientbench-r017|" + t).encode()).hexdigest()

    def block(t):
        x, y = map(int, t.split("_"))
        return x // 2700, y // 2700

    def block_key(b):
        return hashlib.sha256((f"orientbench-r017-block|{b[0]},{b[1]}").encode()).hexdigest()

    blocks = defaultdict(list)
    for tile in pool:
        blocks[block(tile)].append(tile)
    cal_blocks = sorted((b for b, ts in blocks.items() if len(ts) >= 4), key=block_key)[:16]
    if len(cal_blocks) != 16:
        raise ValueError("insufficient geographic blocks")
    cal_pool = [t for b in cal_blocks for t in blocks[b]]
    required = {t for b in cal_blocks for t in sorted(blocks[b], key=tile_key)[:4]}
    calibration = sorted(required, key=tile_key) + sorted(set(cal_pool) - required, key=tile_key)[:128 - len(required)]

    def distance(a, b):
        x, y = map(int, a.split("_"))
        xx, yy = map(int, b.split("_"))
        return math.hypot(max(abs(x - xx) - 450, 0), max(abs(y - yy) - 450, 0))

    train_pool = [t for t in pool if block(t) not in cal_blocks and all(distance(t, c) >= 450 for c in cal_pool)]
    train = sorted(train_pool, key=tile_key)[:256]
    if len(train) != 256 or len(calibration) != 128:
        raise ValueError("fixed sample size unavailable")
    views = sorted(set(sum(TRIPLETS, [])))
    images = [{"split": split, "tile": tile, "catid": catid, **inventory["training_members"][catid][tile]}
              for split, tiles in (("train", train), ("calibration", calibration)) for tile in tiles for catid in views]
    labels = {"_".join(Path(o["key"]).stem.split("_")[-2:]): o for o in inventory["label_file_names_only"]}
    label_items = [{"split": split, "tile": tile, **labels[tile]}
                   for split, tiles in (("train", train), ("calibration", calibration)) for tile in tiles]
    if any(o["bytes"] <= 0 for o in label_items):
        raise ValueError("empty label object in fixed sample")
    return {
        "inventory_sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        "support_sha256": hashlib.sha256(support_path.read_bytes()).hexdigest(),
        "selection": "Native mean geometry only; same two crossed triples, 2700m geographic blocks, 16 calibration blocks with >=4 tiles each, 450m train-to-calibration buffer.",
        "triplets": TRIPLETS, "views": views, "candidate_tiles": len(pool),
        "train_pool_after_buffer": len(train_pool), "calibration_pool": len(cal_pool),
        "training_tiles": train, "calibration_tiles": calibration,
        "training_blocks": len({block(t) for t in train}), "calibration_blocks": len(cal_blocks),
        "calibration_block_keys": cal_blocks, "images": images, "labels": label_items,
        "image_bytes": sum(o["bytes"] for o in images), "label_bytes": sum(o["bytes"] for o in label_items),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.inventory, args.support), indent=2))
