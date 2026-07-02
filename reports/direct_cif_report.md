# Literature-Replication Direct CIF Benchmark Report

## Input set

- Input: C:\Users\brown\Downloads\example created cifs
- Result rows: 22
- Protocols selected: 24
- Protocol match level: contextual_only
- Evaluators: pre_dft_validity

## Computable metrics

| benchmark_family | metric_name | our_value | paper_value | paper_name | beats_paper | protocol_match_level | n_computable | required_inputs_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.98 | Chemeleon | False | contextual_only | 22 |  |
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.99 | Chemeleon | False | contextual_only | 22 |  |
| A_validity | space_group_match_rate | 0.045454545454545456 | 0.74 | CrysText | False | contextual_only | 22 |  |
| A_validity | min_distance_pass_rate | 1.0 | 0.5 | CrystaLLM / Chemeleon | True | contextual_only | 17 |  |
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.9 | Crystal-text LLM / Gruver et al. | False | contextual_only | 22 |  |
| A_validity | parse_validity_rate | 1.0 |  |  |  |  | 22 |  |
| A_validity | bad_contact_rate | 0.13636363636363635 |  |  |  |  | 22 |  |
| A_validity | median_min_distance | 1.9918584287042087 |  |  |  |  | 17 |  |

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
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.98 | Chemeleon | False | contextual_only | 22 |  |
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.99 | Chemeleon | False | contextual_only | 22 |  |
| A_validity | composition_and_sg_match_rate |  | 0.74 | CrysText |  | not_comparable | 0 | target_formula_match,space_group_consistent |
| A_validity | composition_match_rate |  | 0.95 | CrysText |  | not_comparable | 0 | target_formula_match |
| B_structure_reproduction | match_rate_n1 |  | 0.57 | CrysText |  | not_comparable | 0 | structure_match,benchmark_id |
| B_structure_reproduction | match_rate_nk |  | 0.73 | CrysText |  | not_comparable | 0 | structure_match,benchmark_id |
| B_structure_reproduction | best_of_k_rms |  | 0.0243 | CrysText |  | not_comparable | 0 | rms_dist,benchmark_id |
| A_validity | space_group_match_rate | 0.045454545454545456 | 0.74 | CrysText | False | contextual_only | 22 |  |
| B_structure_reproduction | structure_match_rate |  | 0.6392 | Lang2Str |  | not_comparable | 0 | structure_match |
| D_relaxation | relaxed_rms_dist |  | 0.055 | Lang2Str |  | not_comparable | 0 | rms_dist_after,relaxed_rms_dist |
| B_structure_reproduction | mean_rms_dist |  | 0.076 | Lang2Str |  | not_comparable | 0 | rms_dist |
| B_structure_reproduction | structure_match_rate |  | 0.2836 | Lang2Str |  | not_comparable | 0 | structure_match |
| B_structure_reproduction | mean_rms_dist |  | 0.1424 | Lang2Str |  | not_comparable | 0 | rms_dist |
| C_mlip_stability | predicted_ehull_rate_0_15 |  | 0.49 | Crystal-text LLM |  | not_comparable | 0 | predicted_energy_above_hull |
| A_validity | min_distance_pass_rate | 1.0 | 0.5 | CrystaLLM / Chemeleon | True | contextual_only | 17 |  |
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.9 | Crystal-text LLM / Gruver et al. | False | contextual_only | 22 |  |

## Values beaten

| benchmark_family | metric_name | our_value | paper_value | paper_name | beats_paper | protocol_match_level | n_computable | required_inputs_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_validity | min_distance_pass_rate | 1.0 | 0.5 | CrystaLLM / Chemeleon | True | contextual_only | 17 |  |

## Values not beaten

| benchmark_family | metric_name | our_value | paper_value | paper_name | beats_paper | protocol_match_level | n_computable | required_inputs_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.98 | Chemeleon | False | contextual_only | 22 |  |
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.99 | Chemeleon | False | contextual_only | 22 |  |
| A_validity | space_group_match_rate | 0.045454545454545456 | 0.74 | CrysText | False | contextual_only | 22 |  |
| A_validity | pre_dft_validity_rate | 0.8636363636363636 | 0.9 | Crystal-text LLM / Gruver et al. | False | contextual_only | 22 |  |

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
| A_validity | composition_and_sg_match_rate |  | 0.74 | CrysText |  | not_comparable | 0 | target_formula_match,space_group_consistent |
| A_validity | composition_match_rate |  | 0.95 | CrysText |  | not_comparable | 0 | target_formula_match |
| B_structure_reproduction | match_rate_n1 |  | 0.57 | CrysText |  | not_comparable | 0 | structure_match,benchmark_id |
| B_structure_reproduction | match_rate_nk |  | 0.73 | CrysText |  | not_comparable | 0 | structure_match,benchmark_id |
| B_structure_reproduction | best_of_k_rms |  | 0.0243 | CrysText |  | not_comparable | 0 | rms_dist,benchmark_id |
| B_structure_reproduction | structure_match_rate |  | 0.6392 | Lang2Str |  | not_comparable | 0 | structure_match |
| D_relaxation | relaxed_rms_dist |  | 0.055 | Lang2Str |  | not_comparable | 0 | rms_dist_after,relaxed_rms_dist |
| B_structure_reproduction | mean_rms_dist |  | 0.076 | Lang2Str |  | not_comparable | 0 | rms_dist |
| B_structure_reproduction | structure_match_rate |  | 0.2836 | Lang2Str |  | not_comparable | 0 | structure_match |
| B_structure_reproduction | mean_rms_dist |  | 0.1424 | Lang2Str |  | not_comparable | 0 | rms_dist |
| C_mlip_stability | predicted_ehull_rate_0_15 |  | 0.49 | Crystal-text LLM |  | not_comparable | 0 | predicted_energy_above_hull |

## Caveats

- Contextual comparator values are not leaderboard claims.
- Surrogate MLIP is not DFT.
- Local novelty is not global novelty.
- Subset protocol is not full MP-20/MPTS-52.

## Per-target failures

Run `paper-target-diagnostics` for per-target failure analysis when reference and relaxation outputs are available.
