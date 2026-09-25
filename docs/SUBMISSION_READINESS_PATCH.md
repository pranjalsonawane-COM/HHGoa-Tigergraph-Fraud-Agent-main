# Submission Readiness Patch — HHGOA 2026

This additive patch preserves the existing architecture and makes the benchmark case artifacts explicit for the submission rubric.

## Added to all 20 `cases/HHG-*.json` and mirrored `answers/HHG-*.json`

- `nba_before_additional_evidence`: the recorded NBA, verdict, confidence, and approval route at the initial evidence state.
- `additional_evidence_request`: whether more evidence is required, the controlled action type, rationale, and policy-approved outcome branches.
- `after_additional_evidence`: the post-evidence state. For uncertain cases, it deliberately records **conditional simulated branches** rather than inventing a real customer response. For cases already above the action threshold, it records `not_applicable`.
- `evidence_progression`: a single audit-friendly object containing the before/request/after lifecycle.
- `graph_writeback`: identifies the case/customer/card/transaction graph entities and the generated GSQL artifact. It says `ready_for_tigergraph_writeback`, not `written`, unless the GSQL is actually executed against the team's TigerGraph deployment.

## Generated graph artifact

`tigergraph/generated/benchmark_case_writeback.gsql` contains writeback statements for all 20 benchmark cases. Execute it only after the configured TigerGraph graph is loaded and the team has verified the target schema.

## Validation

Run:

```bash
python scripts/submission_check.py
python scripts/evaluate_benchmarks.py
python -m unittest tests.test_case_management tests.test_evidence_simulator
```

The submission check verifies exact case filenames, JSON validity, explicit before/request/after NBA fields, SAR fields, playbook fields, and graph-writeback manifests.
