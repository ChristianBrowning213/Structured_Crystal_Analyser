# SCA Paper-Comparable Benchmark Report

## Dataset / manifest

- Summary rows: 1410
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
|global|composition_match_rate|1.0|22||||
|global|pre_dft_validity_rate|0.8636363636363636|22||||
|global|geometry_ok_rate|1.0|22||||
|global|bond_reasonable_rate|0.8636363636363636|22||||
|global|bad_contact_rate|0.13636363636363635|22||||
|global|median_min_distance|1.9918584287042087|17||||
|global|median_bad_contacts|0.0|22||||
|global|hard_fail_count|3.0|22||||
|group|parse_validity_rate|1.0|22||||
|group|composition_match_rate|1.0|22||||
|group|pre_dft_validity_rate|0.8636363636363636|22||||
|group|geometry_ok_rate|1.0|22||||
|group|bond_reasonable_rate|0.8636363636363636|22||||
|group|bad_contact_rate|0.13636363636363635|22||||
|group|median_min_distance|1.9918584287042087|17||||
|group|median_bad_contacts|0.0|22||||
|group|hard_fail_count|3.0|22||||
|benchmark|parse_validity_rate|1.0|1||||
|benchmark|composition_match_rate|1.0|1||||

## B. Structure reproduction

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|structure_match_rate|0.09090909090909091|22||||
|global|match_rate|0.09090909090909091|22||||
|global|anonymous_match_rate|0.09090909090909091|22||||
|global|supercell_match_rate|0.0|22||||
|global|mean_rms_dist|0.0|1||||
|global|median_rms_dist|0.0|1||||
|global|best_rms_dist|0.0|1||||
|global|mean_max_dist|0.0|1||||
|global|structure_rmse|0.0|1||||
|global|structure_rmse_relaxed|0.05743700423680957|4||||
|global|match_rate_n1|0.09090909090909091|22||||
|global|match_rate_nk|0.09090909090909091|22||||
|group|structure_match_rate|0.09090909090909091|22||||
|group|match_rate|0.09090909090909091|22||||
|group|anonymous_match_rate|0.09090909090909091|22||||
|group|supercell_match_rate|0.0|22||||
|group|mean_rms_dist|0.0|1||||
|group|median_rms_dist|0.0|1||||
|group|best_rms_dist|0.0|1||||
|group|mean_max_dist|0.0|1||||

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
|group|chgnet_ok_rate|1.0|22||||
|group|m3gnet_ok_rate|1.0|22||||
|group|mace_ok_rate|1.0|22||||
|group|sevennet_ok_rate|1.0|22||||

## D. Relaxation

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|relax_success_rate|0.6818181818181818|22||||
|global|median_energy_drop_per_atom|0.7585931777954101|22||||
|global|median_max_force_before|1.963085286062248|22||||
|global|median_max_force_after|0.0626224384718283|22||||
|global|force_threshold_success_rate_0_20|0.8181818181818182|22||||
|global|force_threshold_success_rate_0_10|0.6818181818181818|22||||
|global|rmse_improvement_rate|0.0|1||||
|global|median_rmse_before|0.0|1||||
|global|median_rmse_after|0.0252609685194734|4||||
|global|median_rmse_delta|-9.991955972347017e-09|1||||
|global|rmse_improvement_after_relaxation|-9.991955972347017e-09|1||||
|global|relaxed_rmse|0.05743700423680957|4||||
|global|structure_preservation_rate|0.22727272727272727|22||||
|global|collapse_rate|0.0|22||||
|group|relax_success_rate|0.6818181818181818|22||||
|group|median_energy_drop_per_atom|0.7585931777954101|22||||
|group|median_max_force_before|1.963085286062248|22||||
|group|median_max_force_after|0.0626224384718283|22||||
|group|force_threshold_success_rate_0_20|0.8181818181818182|22||||
|group|force_threshold_success_rate_0_10|0.6818181818181818|22||||

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
|group|unique_rate|1.0|22|||local uniqueness|
|group|duplicate_rate|0.0|22||||
|group|known_match_rate||0||||
|group|local_novelty_rate||0|||local novelty relative to supplied reference corpus|
|group|novel_by_structure_matcher_rate||0||||
|group|sun_rate||0|||SUN uses local novelty and surrogate stability proxy|
|group|sun_count||0|||SUN uses local novelty and surrogate stability proxy|
|benchmark|unique_rate|1.0|1|||local uniqueness|
|benchmark|duplicate_rate|0.0|1||||
|benchmark|known_match_rate||0||||
|benchmark|local_novelty_rate||0|||local novelty relative to supplied reference corpus|
|benchmark|novel_by_structure_matcher_rate||0||||
|benchmark|sun_rate||0|||SUN uses local novelty and surrogate stability proxy|

## Comparator results

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|comparator|pre_dft_validity_rate|0.8636363636363636|22|crystal_text_llm_physical_constraints|False|around 90% physically constrained samples; contextual comparator|
|comparator|match_rate|0.09090909090909091|22|DiffCSP_MP20|False||
|comparator|match_rate|0.09090909090909091|22|FlowMM_MP20|False||
|comparator|match_rate|0.09090909090909091|22|CrystalFlow_MP20|False||
|comparator|match_rate|0.09090909090909091|22|Lang2Str_MP20|False||
|comparator|match_rate|0.09090909090909091|22|Uni3DAR_MP20|False||
|comparator|structure_rmse|0.0|1|Lang2Str_MP20|True||
|comparator|structure_rmse_relaxed|0.05743700423680957|4|Lang2Str_MP20_relaxed|False||
|comparator|match_rate|0.09090909090909091|22|Lang2Str_MPTS52|False||
|comparator|match_rate|0.09090909090909091|22|Uni3DAR_MPTS52|False||
|comparator|predicted_metastable_rate_ehull_0_15||0|CDVAE_crystal_text_llm_comparator||metric not computable|
|comparator|predicted_metastable_rate_ehull_0_15||0|finetuned_LLaMA2_70B_crystal_text_llm||metric not computable|
|comparator|metastability_threshold|0.15|22|Chemeleon_ZnTiO_metastable_threshold|True||
|comparator|rmse_improvement_after_relaxation|-9.991955972347017e-09|1|Lang2Str_MP20_relaxation_improvement|False|0.076 -> 0.055|
|comparator|relaxed_rmse|0.05743700423680957|4|Lang2Str_MP20_relaxed|False||
|comparator|unique_rate|1.0|22|internal_first_target|True||
|comparator|sun_rate||0|internal_first_target||metric not computable|
|comparator|sun_rate||0|internal_strong_target||metric not computable|

## Not-computable metrics

|summary_scope|metric_name|our_value|n_computable|comparator_name|beats_comparator|notes|
|---|---|---|---|---|---|---|
|global|median_min_distance|1.9918584287042087|17||||
|global|mean_rms_dist|0.0|1||||
|global|median_rms_dist|0.0|1||||
|global|best_rms_dist|0.0|1||||
|global|mean_max_dist|0.0|1||||
|global|structure_rmse|0.0|1||||
|global|structure_rmse_relaxed|0.05743700423680957|4||||
|global|predicted_ehull_rate_0_00||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_05||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_10||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_ehull_rate_0_15||0|||missing required columns: predicted_energy_above_hull|
|global|predicted_metastable_rate_ehull_0_15||0|||missing required columns: predicted_energy_above_hull|
|global|rmse_improvement_rate|0.0|1||||
|global|median_rmse_before|0.0|1||||
|global|median_rmse_after|0.0252609685194734|4||||
|global|median_rmse_delta|-9.991955972347017e-09|1||||
|global|rmse_improvement_after_relaxation|-9.991955972347017e-09|1||||
|global|relaxed_rmse|0.05743700423680957|4||||
|global|known_match_rate||0||||
|global|local_novelty_rate||0|||local novelty relative to supplied reference corpus|
|global|novel_by_structure_matcher_rate||0||||
|global|sun_rate||0|||SUN uses local novelty and surrogate stability proxy|
|global|sun_count||0|||SUN uses local novelty and surrogate stability proxy|
|group|median_min_distance|1.9918584287042087|17||||
|group|mean_rms_dist|0.0|1||||
|group|median_rms_dist|0.0|1||||
|group|best_rms_dist|0.0|1||||
|group|mean_max_dist|0.0|1||||
|group|structure_rmse|0.0|1||||
|group|structure_rmse_relaxed|0.05743700423680957|4||||
|group|predicted_ehull_rate_0_00||0|||missing required columns: predicted_energy_above_hull|
|group|predicted_ehull_rate_0_05||0|||missing required columns: predicted_energy_above_hull|
|group|predicted_ehull_rate_0_10||0|||missing required columns: predicted_energy_above_hull|
|group|predicted_ehull_rate_0_15||0|||missing required columns: predicted_energy_above_hull|
|group|predicted_metastable_rate_ehull_0_15||0|||missing required columns: predicted_energy_above_hull|
|group|rmse_improvement_rate|0.0|1||||
|group|median_rmse_before|0.0|1||||
|group|median_rmse_after|0.0252609685194734|4||||
|group|median_rmse_delta|-9.991955972347017e-09|1||||
|group|rmse_improvement_after_relaxation|-9.991955972347017e-09|1||||
|group|relaxed_rmse|0.05743700423680957|4||||
|group|known_match_rate||0||||
|group|local_novelty_rate||0|||local novelty relative to supplied reference corpus|
|group|novel_by_structure_matcher_rate||0||||
|group|sun_rate||0|||SUN uses local novelty and surrogate stability proxy|
|group|sun_count||0|||SUN uses local novelty and surrogate stability proxy|
|benchmark|predicted_ehull_rate_0_00||0|||missing required columns: predicted_energy_above_hull|
|benchmark|predicted_ehull_rate_0_05||0|||missing required columns: predicted_energy_above_hull|
|benchmark|predicted_ehull_rate_0_10||0|||missing required columns: predicted_energy_above_hull|
|benchmark|predicted_ehull_rate_0_15||0|||missing required columns: predicted_energy_above_hull|

## Caveats

- Surrogate MLIP scores are not DFT.
- Local novelty is not global novelty.
- Paper-derived target subset results are not full MP-20/MPTS-52 leaderboard results unless the manifest explicitly says so.
- Predicted hull metrics require a local reference hull.
- Relaxation metrics require actual relaxed structures.
