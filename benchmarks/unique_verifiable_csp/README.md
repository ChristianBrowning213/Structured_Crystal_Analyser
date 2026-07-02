# Unique Verifiable CSP Benchmark Assets

These prompt suites evaluate the parts of a text-to-crystal workflow that are not covered by ordinary CIF-only benchmarks:

- traceability: retrieved evidence, derived constraints, SPP/pair statistics, solver status, and final decisions are inspectable.
- constraint faithfulness: generated artifacts preserve explicit formula, space-group, family, distance, contact, and motif constraints.
- solver infeasibility: impossible requests should be certified or refused rather than silently emitted as plausible CIFs.
- retrieval ablation: the same prompts are run with retrieval disabled, metadata retrieval, and evidence/SPP retrieval.
- repairability: failed candidates are diagnosed, repaired, and compared before/after.
- evidence faithfulness: final explanations should cite only evidence that was actually retrieved.
- audit completeness: a run bundle should contain enough metadata to reproduce the run.

The fixtures are synthetic scaffolds. They are designed for offline CI and smoke tests, not for claiming production LLM-CSP performance.
