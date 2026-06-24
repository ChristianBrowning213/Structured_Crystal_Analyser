# SCA Paper-Comparable Benchmark Report

## Dataset / manifest

- Summary rows: 76
- Manifest warnings: 21
- row 2: reference-dependent target missing reference_cif_path
- row 3: reference-dependent target missing reference_cif_path
- row 4: reference-dependent target missing reference_cif_path
- row 5: reference-dependent target missing reference_cif_path
- row 6: reference-dependent target missing reference_cif_path
- row 7: reference-dependent target missing reference_cif_path
- row 8: hull-dependent target missing hull_reference_path
- row 9: hull-dependent target missing hull_reference_path
- row 10: hull-dependent target missing hull_reference_path
- row 11: hull-dependent target missing hull_reference_path
- row 12: hull-dependent target missing hull_reference_path
- row 13: hull-dependent target missing hull_reference_path
- row 14: hull-dependent target missing hull_reference_path
- row 15: hull-dependent target missing hull_reference_path
- row 16: hull-dependent target missing hull_reference_path
- row 17: hull-dependent target missing hull_reference_path
- row 18: hull-dependent target missing hull_reference_path
- row 19: hull-dependent target missing hull_reference_path
- row 20: hull-dependent target missing hull_reference_path
- row 21: hull-dependent target missing hull_reference_path

## A. Validity

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|parse_validity_rate|1.0|22||||
|global|composition_match_rate||0||||
|global|pre_dft_validity_rate|0.8636363636363636|22||||
|global|geometry_ok_rate|1.0|22||||
|global|bond_reasonable_rate|0.8636363636363636|22||||
|global|bad_contact_rate|0.13636363636363635|22||||
|global|median_min_distance|1.9918584287042087|17||||
|global|median_bad_contacts|0.0|22||||
|global|hard_fail_count|3.0|22||||

## B. Structure reproduction

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|structure_match_rate||0|||missing required columns: structure_match|
|global|match_rate||0|||missing required columns: structure_match|
|global|anonymous_match_rate||0|||missing required columns: anonymous_match|
|global|supercell_match_rate||0|||missing required columns: supercell_match|
|global|mean_rms_dist||0|||missing required columns: rms_dist|
|global|median_rms_dist||0|||missing required columns: rms_dist|
|global|best_rms_dist||0|||missing required columns: rms_dist|
|global|mean_max_dist||0|||missing required columns: max_dist|
|global|structure_rmse||0|||missing required columns: rms_dist|
|global|structure_rmse_relaxed||0|||missing required columns: rms_dist_after, relaxed_rms_dist|
|global|match_rate_n1||0|||missing required columns: structure_match|
|global|match_rate_nk||0|||missing required columns: structure_match|

## C. MLIP stability and predicted metastability

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|chgnet_ok_rate|1.0|22||||
|global|m3gnet_ok_rate|1.0|22||||
|global|mace_ok_rate|1.0|22||||
|global|sevennet_ok_rate|1.0|22||||
|global|mlip_ensemble_ok_rate|1.0|22||||
|global|mlip_consensus_stable_rate|0.18181818181818182|22||||
|global|mlip_disagreement_rate|0.8181818181818182|22||||
|global|median_mlip_mean_energy|-2.988885998725891|22||||
|global|median_mlip_energy_std|1.2731933335368386|22||||
|global|median_mlip_max_force|2.6765640032235116|22||||
|global|predicted_ehull_rate_0_00||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_05||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_10||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_15||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_metastable_rate_ehull_0_15||0|||missing required columns: predicted_energy_above_hull|
|global|metastability_threshold|0.15|22||||

## D. Relaxation

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|relax_success_rate||0|||missing required columns: relax_ok|
|global|median_energy_drop_per_atom||0|||missing required columns: energy_drop_per_atom|
|global|median_max_force_before||0|||missing required columns: max_force_before|
|global|median_max_force_after||0|||missing required columns: max_force_after|
|global|force_threshold_success_rate_0_20||0|||missing required columns: max_force_after|
|global|force_threshold_success_rate_0_10||0|||missing required columns: max_force_after|
|global|rmse_improvement_rate||0|||missing required columns: rms_dist_before, rms_dist_after|
|global|median_rmse_before||0|||missing required columns: rms_dist_before|
|global|median_rmse_after||0|||missing required columns: rms_dist_after|
|global|median_rmse_delta||0|||missing required columns: rms_dist_before, rms_dist_after|
|global|rmse_improvement_after_relaxation||0|||missing required columns: rms_dist_before, rms_dist_after|
|global|relaxed_rmse||0|||missing required columns: rms_dist_after|
|global|structure_preservation_rate||0|||missing required columns: structure_match_after|
|global|collapse_rate||0|||missing required columns: relax_error|

## E. Novelty, uniqueness, and SUN

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|unique_rate|1.0|22|||local uniqueness|
|global|duplicate_rate|0.0|22||||
|global|known_match_rate||0||||
|global|local_novelty_rate||0|||local novelty relative to supplied reference corpus|
|global|novel_by_structure_matcher_rate||0||||
|global|sun_rate||0|||SUN uses local novelty and surrogate stability proxy|
|global|sun_count||0|||SUN uses local novelty and surrogate stability proxy|

## Comparator results

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|comparator|pre_dft_validity_rate|0.8636363636363636|22|crystal_text_llm_physical_constraints|False|around 90% physically constrained samples; contextual comparator|
|comparator|match_rate||0|DiffCSP_MP20||metric not computable|
|comparator|match_rate||0|FlowMM_MP20||metric not computable|
|comparator|match_rate||0|CrystalFlow_MP20||metric not computable|
|comparator|match_rate||0|Lang2Str_MP20||metric not computable|
|comparator|match_rate||0|Uni3DAR_MP20||metric not computable|
|comparator|structure_rmse||0|Lang2Str_MP20||metric not computable|
|comparator|structure_rmse_relaxed||0|Lang2Str_MP20_relaxed||metric not computable|
|comparator|match_rate||0|Lang2Str_MPTS52||metric not computable|
|comparator|match_rate||0|Uni3DAR_MPTS52||metric not computable|
|comparator|predicted_metastable_rate_ehull_0_15||0|CDVAE_crystal_text_llm_comparator||metric not computable|
|comparator|predicted_metastable_rate_ehull_0_15||0|finetuned_LLaMA2_70B_crystal_text_llm||metric not computable|
|comparator|metastability_threshold|0.15|22|Chemeleon_ZnTiO_metastable_threshold|True||
|comparator|rmse_improvement_after_relaxation||0|Lang2Str_MP20_relaxation_improvement||metric not computable; 0.076 -> 0.055|
|comparator|relaxed_rmse||0|Lang2Str_MP20_relaxed||metric not computable|
|comparator|unique_rate|1.0|22|internal_first_target|True||
|comparator|sun_rate||0|internal_first_target||metric not computable|
|comparator|sun_rate||0|internal_strong_target||metric not computable|

## Not-computable metrics

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|composition_match_rate||0||||
|global|median_min_distance|1.9918584287042087|17||||
|global|structure_match_rate||0|||missing required columns: structure_match|
|global|match_rate||0|||missing required columns: structure_match|
|global|anonymous_match_rate||0|||missing required columns: anonymous_match|
|global|supercell_match_rate||0|||missing required columns: supercell_match|
|global|mean_rms_dist||0|||missing required columns: rms_dist|
|global|median_rms_dist||0|||missing required columns: rms_dist|
|global|best_rms_dist||0|||missing required columns: rms_dist|
|global|mean_max_dist||0|||missing required columns: max_dist|
|global|structure_rmse||0|||missing required columns: rms_dist|
|global|structure_rmse_relaxed||0|||missing required columns: rms_dist_after, relaxed_rms_dist|
|global|match_rate_n1||0|||missing required columns: structure_match|
|global|match_rate_nk||0|||missing required columns: structure_match|
|global|predicted_ehull_rate_0_00||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_05||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_10||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_15||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_metastable_rate_ehull_0_15||0|||missing required columns: predicted_energy_above_hull|
|global|relax_success_rate||0|||missing required columns: relax_ok|
|global|median_energy_drop_per_atom||0|||missing required columns: energy_drop_per_atom|
|global|median_max_force_before||0|||missing required columns: max_force_before|
|global|median_max_force_after||0|||missing required columns: max_force_after|
|global|force_threshold_success_rate_0_20||0|||missing required columns: max_force_after|
|global|force_threshold_success_rate_0_10||0|||missing required columns: max_force_after|
|global|rmse_improvement_rate||0|||missing required columns: rms_dist_before, rms_dist_after|
|global|median_rmse_before||0|||missing required columns: rms_dist_before|
|global|median_rmse_after||0|||missing required columns: rms_dist_after|
|global|median_rmse_delta||0|||missing required columns: rms_dist_before, rms_dist_after|
|global|rmse_improvement_after_relaxation||0|||missing required columns: rms_dist_before, rms_dist_after|
|global|relaxed_rmse||0|||missing required columns: rms_dist_after|
|global|structure_preservation_rate||0|||missing required columns: structure_match_after|
|global|collapse_rate||0|||missing required columns: relax_error|
|global|known_match_rate||0||||
|global|local_novelty_rate||0|||local novelty relative to supplied reference corpus|
|global|novel_by_structure_matcher_rate||0||||
|global|sun_rate||0|||SUN uses local novelty and surrogate stability proxy|
|global|sun_count||0|||SUN uses local novelty and surrogate stability proxy|

## Caveats

- Surrogate MLIP scores are not DFT.
- Local novelty is not global novelty.
- Paper-derived target subset results are not full MP-20/MPTS-52 leaderboard results unless the manifest explicitly says so.
- Predicted hull metrics require a local reference hull.
- Relaxation metrics require actual relaxed structures.
