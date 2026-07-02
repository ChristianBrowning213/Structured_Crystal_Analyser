# Literature-Replication Direct CIF Benchmark Report

## Input set

- Input: reports\e2e_fake_runs\generated_cifs_manifest.csv
- Result rows: 27
- Protocols selected: 24
- Protocol match level: contextual_only
- Evaluators: pre_dft_validity, structure_match, property_targets

## Computable metrics

| benchmark_family | metric_name | our_value | paper_value | paper_name | beats_paper | protocol_match_level | n_computable | required_inputs_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_validity | pre_dft_validity_rate | 0.0 | 0.98 | Chemeleon | False | contextual_only | 27 |  |
| A_validity | pre_dft_validity_rate | 0.0 | 0.99 | Chemeleon | False | contextual_only | 27 |  |
| A_validity | composition_and_sg_match_rate | 0.0 | 0.74 | CrysText | False | contextual_only | 27 |  |
| A_validity | composition_match_rate | 0.0 | 0.95 | CrysText | False | contextual_only | 27 |  |
| B_structure_reproduction | match_rate_n1 | 0.0 | 0.57 | CrysText | False | contextual_only | 5 |  |
| B_structure_reproduction | match_rate_nk | 0.0 | 0.73 | CrysText | False | contextual_only | 5 |  |
| A_validity | space_group_match_rate | 0.1111111111111111 | 0.74 | CrysText | False | contextual_only | 27 |  |
| B_structure_reproduction | structure_match_rate | 0.0 | 0.6392 | Lang2Str | False | contextual_only | 15 |  |
| B_structure_reproduction | structure_match_rate | 0.0 | 0.2836 | Lang2Str | False | contextual_only | 15 |  |
| A_validity | pre_dft_validity_rate | 0.0 | 0.9 | Crystal-text LLM / Gruver et al. | False | contextual_only | 27 |  |
| A_validity | parse_validity_rate | 1.0 |  |  |  |  | 27 |  |
| A_validity | bad_contact_rate | 0.0 |  |  |  |  | 27 |  |
| B_structure_reproduction | anonymous_match_rate | 0.0 |  |  |  |  | 15 |  |
| B_structure_reproduction | supercell_match_rate | 0.0 |  |  |  |  | 15 |  |
| E_property | property_hit_rate_within_tolerance | 0.0 |  |  |  |  | 27 |  |

## Comparator matrix

| benchmark_family | metric_name | our_value | paper_value | paper_name | beats_paper | protocol_match_level | n_computable | required_inputs_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E_property | formation_energy_mae |  | 0.033 | ALIGNN baseline |  | not_comparable | 0 | formation_energy_error |
| E_property | formation_energy_mae |  | 0.072 | AtomGPT |  | not_comparable | 0 | formation_energy_error |
| C_mlip_stability | predicted_ehull_rate_0_15 |  | 0.28 | Crystal-text LLM |  | not_comparable | 0 | predicted_energy_above_hull |
| C_mlip_stability | predicted_ehull_rate_0_15 |  | 0.15 | Chemeleon |  | not_comparable | 0 | predicted_energy_above_hull |
| C_mlip_stability | metastable_count |  | 435 | Chemeleon |  | not_comparable | 0 | predicted_energy_above_hull |
| C_mlip_stability | stable_count |  | 17 | Chemeleon |  | not_comparable | 0 | predicted_energy_above_hull |
| C_mlip_stability | within_threshold_rate_0_15 |  | 0.8 | Chemeleon |  | not_comparable | 0 | predicted_energy_above_hull |
| D_relaxation | relax_success_rate |  | 0.9817850637522769 | Chemeleon |  | not_comparable | 0 | relax_ok |
| A_validity | pre_dft_validity_rate | 0.0 | 0.98 | Chemeleon | False | contextual_only | 27 |  |
| A_validity | pre_dft_validity_rate | 0.0 | 0.99 | Chemeleon | False | contextual_only | 27 |  |
| A_validity | composition_and_sg_match_rate | 0.0 | 0.74 | CrysText | False | contextual_only | 27 |  |
| A_validity | composition_match_rate | 0.0 | 0.95 | CrysText | False | contextual_only | 27 |  |
| B_structure_reproduction | match_rate_n1 | 0.0 | 0.57 | CrysText | False | contextual_only | 5 |  |
| B_structure_reproduction | match_rate_nk | 0.0 | 0.73 | CrysText | False | contextual_only | 5 |  |
| B_structure_reproduction | best_of_k_rms |  | 0.0243 | CrysText |  | not_comparable | 0 | rms_dist,benchmark_id |
| A_validity | space_group_match_rate | 0.1111111111111111 | 0.74 | CrysText | False | contextual_only | 27 |  |
| B_structure_reproduction | structure_match_rate | 0.0 | 0.6392 | Lang2Str | False | contextual_only | 15 |  |
| D_relaxation | relaxed_rms_dist |  | 0.055 | Lang2Str |  | not_comparable | 0 | rms_dist_after,relaxed_rms_dist |
| B_structure_reproduction | mean_rms_dist |  | 0.076 | Lang2Str |  | not_comparable | 0 | rms_dist |
| B_structure_reproduction | structure_match_rate | 0.0 | 0.2836 | Lang2Str | False | contextual_only | 15 |  |
| B_structure_reproduction | mean_rms_dist |  | 0.1424 | Lang2Str |  | not_comparable | 0 | rms_dist |
| C_mlip_stability | predicted_ehull_rate_0_15 |  | 0.49 | Crystal-text LLM |  | not_comparable | 0 | predicted_energy_above_hull |
| A_validity | min_distance_pass_rate |  | 0.5 | CrystaLLM / Chemeleon |  | not_comparable | 0 | min_distance |
| A_validity | pre_dft_validity_rate | 0.0 | 0.9 | Crystal-text LLM / Gruver et al. | False | contextual_only | 27 |  |

## Values beaten

No rows.

## Values not beaten

| benchmark_family | metric_name | our_value | paper_value | paper_name | beats_paper | protocol_match_level | n_computable | required_inputs_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_validity | pre_dft_validity_rate | 0.0 | 0.98 | Chemeleon | False | contextual_only | 27 |  |
| A_validity | pre_dft_validity_rate | 0.0 | 0.99 | Chemeleon | False | contextual_only | 27 |  |
| A_validity | composition_and_sg_match_rate | 0.0 | 0.74 | CrysText | False | contextual_only | 27 |  |
| A_validity | composition_match_rate | 0.0 | 0.95 | CrysText | False | contextual_only | 27 |  |
| B_structure_reproduction | match_rate_n1 | 0.0 | 0.57 | CrysText | False | contextual_only | 5 |  |
| B_structure_reproduction | match_rate_nk | 0.0 | 0.73 | CrysText | False | contextual_only | 5 |  |
| A_validity | space_group_match_rate | 0.1111111111111111 | 0.74 | CrysText | False | contextual_only | 27 |  |
| B_structure_reproduction | structure_match_rate | 0.0 | 0.6392 | Lang2Str | False | contextual_only | 15 |  |
| B_structure_reproduction | structure_match_rate | 0.0 | 0.2836 | Lang2Str | False | contextual_only | 15 |  |
| A_validity | pre_dft_validity_rate | 0.0 | 0.9 | Crystal-text LLM / Gruver et al. | False | contextual_only | 27 |  |

## Not-computable metrics

| benchmark_family | metric_name | our_value | paper_value | paper_name | beats_paper | protocol_match_level | n_computable | required_inputs_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E_property | formation_energy_mae |  | 0.033 | ALIGNN baseline |  | not_comparable | 0 | formation_energy_error |
| E_property | formation_energy_mae |  | 0.072 | AtomGPT |  | not_comparable | 0 | formation_energy_error |
| C_mlip_stability | predicted_ehull_rate_0_15 |  | 0.28 | Crystal-text LLM |  | not_comparable | 0 | predicted_energy_above_hull |
| C_mlip_stability | predicted_ehull_rate_0_15 |  | 0.15 | Chemeleon |  | not_comparable | 0 | predicted_energy_above_hull |
| C_mlip_stability | metastable_count |  | 435 | Chemeleon |  | not_comparable | 0 | predicted_energy_above_hull |
| C_mlip_stability | stable_count |  | 17 | Chemeleon |  | not_comparable | 0 | predicted_energy_above_hull |
| C_mlip_stability | within_threshold_rate_0_15 |  | 0.8 | Chemeleon |  | not_comparable | 0 | predicted_energy_above_hull |
| D_relaxation | relax_success_rate |  | 0.9817850637522769 | Chemeleon |  | not_comparable | 0 | relax_ok |
| B_structure_reproduction | best_of_k_rms |  | 0.0243 | CrysText |  | not_comparable | 0 | rms_dist,benchmark_id |
| D_relaxation | relaxed_rms_dist |  | 0.055 | Lang2Str |  | not_comparable | 0 | rms_dist_after,relaxed_rms_dist |
| B_structure_reproduction | mean_rms_dist |  | 0.076 | Lang2Str |  | not_comparable | 0 | rms_dist |
| B_structure_reproduction | mean_rms_dist |  | 0.1424 | Lang2Str |  | not_comparable | 0 | rms_dist |
| C_mlip_stability | predicted_ehull_rate_0_15 |  | 0.49 | Crystal-text LLM |  | not_comparable | 0 | predicted_energy_above_hull |
| A_validity | min_distance_pass_rate |  | 0.5 | CrystaLLM / Chemeleon |  | not_comparable | 0 | min_distance |

## Caveats

- Contextual comparator values are not leaderboard claims.
- Surrogate MLIP is not DFT.
- Local novelty is not global novelty.
- Subset protocol is not full MP-20/MPTS-52.

## Per-target failures

Run `paper-target-diagnostics` for per-target failure analysis when reference and relaxation outputs are available.

# E2E Text-to-Crystal Benchmark Report

## Prompt set

- Prompts: 9
- Generated CIFs: 27

## Generation success

| prompt_id | status | exit_code | num_cifs |
|---|---|---:|---:|
| e2e_batio3_perovskite | ok | 0 | 3 |
| e2e_znfe2o4_spinel | ok | 0 | 3 |
| e2e_nio_rocksalt | ok | 0 | 3 |
| e2e_tio2_rutile | ok | 0 | 3 |
| e2e_li6ps5cl_argyrodite | ok | 0 | 3 |
| e2e_fes2_pyrite | ok | 0 | 3 |
| e2e_ceo2_fluorite | ok | 0 | 3 |
| e2e_zno_wurtzite | ok | 0 | 3 |
| e2e_ndag_hg2_sg225 | ok | 0 | 3 |

## Traceability audit

Generation stdout/stderr paths and command templates are recorded in `generation_log.csv`.
