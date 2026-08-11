# orientbench r020 measurement-validity server report

- round_id: `orientbench-c-r020-measurement-validity-20260811`
- route: `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`
- execution_status: `FAILURE_EARLY_STOP`
- scientific_state: `NOT_ADJUDICATED`
- sug_genuinely_exhausted: `false`
- recorded_at: `2026-08-11 22:30:29 CST`
- pre_pull_head: `594654a95d50b1f14b87252698911cc3fc583b03`
- post_sync_head: `6855080d7674da4b4da54ab4d9aeab550974c69e`
- execution_base: `NOT_FROZEN`
- git_publish_status: `PENDING_ABNORMAL_RESULT_PUBLICATION`

## Decision

The r020 scientific gate is not adjudicated. Preflight found two independent protocol defects before any scientific input was opened. Under sections 2 and 12 of the active contract, either defect requires `FAILURE_EARLY_STOP / NOT_ADJUDICATED`; the A/B implementations, Comparator C, bootstrap, hypotheses, witnesses and four-state scientific gate must not be emitted.

## Git preflight defect

The repository was initially clean on local `main` at `594654a95d50b1f14b87252698911cc3fc583b03`, with configured origin `https://github.com/ziyu24/orientbench.git`. The server synchronization performed:

1. `git fetch origin main`
2. `git merge --ff-only origin/main`

and fast-forwarded to `6855080d7674da4b4da54ab4d9aeab550974c69e`. The reflog records `merge origin/main: Fast-forward`. Although the resulting local HEAD equals the fetched remote-tracking ref and the configured origin resolves to the required HTTPS repository, the contract permits only the literal command `git pull --ff-only https://github.com/ziyu24/orientbench.git main` and explicitly prohibits invoking configured origin. The method is therefore non-conforming and cannot be retroactively repaired by issuing a no-op pull.

## CPU preflight defect

The contract requires exactly `N=48` logical CPUs, 39 worker processes, and 39-core affinity. The migrated server exposes:

- `getconf _NPROCESSORS_ONLN = 112`
- `nproc = 112`
- process affinity `0-111`
- `/sys/fs/cgroup/cpuset.cpus.effective = 0-111`
- `lscpu`: 112 online logical CPUs, 56 cores, 2 sockets

With 39 fixed workers and the contract's denominator `30*N`, the maximum unthrottled job CPU percentage is `39/112*100 = 34.8214%`, below the mandatory 60% lower bound. Re-labeling `N`, silently restricting the migrated host to 48 CPUs, or changing worker count/resource thresholds is not authorized. This mismatch independently prevents a valid full execution.

## Checks completed before stop

- branch: `main`
- local HEAD after synchronization: `6855080d7674da4b4da54ab4d9aeab550974c69e`
- cached `origin/main`: `6855080d7674da4b4da54ab4d9aeab550974c69e`
- worktree/index after synchronization: clean
- planning base `594654a95d50b1f14b87252698911cc3fc583b03`: ancestor of post-sync HEAD
- protected `dis/B.md` blob: `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`
- protected `dis/B.md` staged and unstaged diffs: empty
- receipt3 report blob: `498dd8094f713a4a76339890ffd3a9ec45352344`
- new code root, runtime root, postseal receipt root and report path: absent at initial path preflight
- both output roots: ignored by `/outputs/`

## Scope and negative evidence

No m069, r014, frozen-delta, learned-EQS, receipt3 runtime, annotation or other scientific input was opened. No code seal, synthetic fixture, tracer, pinned reference fetch, A/B computation, Comparator C, bootstrap replicate, mutation harness, manifest, tracked-content seal or postseal receipt was produced. No GPU, installation, training, forward, inference, new target outcome, method experiment, threshold/split/formal-label change, manuscript edit or old-artifact write occurred.

The only persistent runtime object is the preflight failure record at `outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/preflight.json`. This consumed round and its paths must not be reused.

## Required next control-plane action

C must issue a new round ID and fresh code/runtime/report/postseal paths after explicitly reconciling the migrated server's 112-logical-CPU topology with worker count and telemetry thresholds. The new dispatch should retain explicit HTTPS Git provenance while permitting an auditable synchronization method that the server can execute before reading the pulled contract. No scientific conclusion may be inferred from this early stop.
