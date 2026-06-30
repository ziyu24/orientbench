# Artifact Persistence Check (044)

> 2026-06-30 10:47:20 CST

- 共 21 artifacts；all_have_sha256=True。
- **Track A dumps + real TTA preds**：/dev/shm（非持久）+ manifest(sha256/gen_cmd/can_recompute)；可由 instrumented adapter / flip adapter 复算。
- **selector result CSVs**：项目内（git tracked，小文件）。
- **shadow farms**：/dev/shm（非持久），可由 build_dior_farm_042.py / build_farm_general_043.py 复算；原 dataset 未修改。
- ⚠️ /dev/shm 非持久：重启后需按 generation command 复算。
- 大文件不进 git（git 0 大文件）。
