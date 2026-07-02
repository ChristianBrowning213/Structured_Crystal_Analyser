# Paper Target Diagnostics

- Targets: 22
- This report classifies failures from existing benchmark columns and parsed CIF/reference/relaxed structures.
- It does not change benchmark metrics.

## Category Counts

| category | count |
|---|---:|
| wrong_prototype_or_symmetry | 6 |
| relaxed_structure_collapsed | 5 |
| near_match | 3 |
| relaxation_failed | 3 |
| bad_contacts_or_invalid_geometry | 3 |
| exact_reference_match | 2 |

## Per Target

| benchmark_id | primary_category | relaxation_effect | reference_risk | diagnostic_reason |
| --- | --- | --- | --- | --- |
| sanity_batio3_perovskite | near_match | relaxation_improved | prototype_or_polymorph_note | Generated CIF did not match, but the relaxed CIF matches the reference. Generated CIF is geometrically plausible but does not match the reference prototype. |
| sanity_catio3_perovskite | exact_reference_match | relaxation_worsened | prototype_or_polymorph_note | StructureMatcher matched the generated CIF to the reference. |
| generated_challenge_mgal2o4_spinel | relaxation_failed | relaxation_improved | prototype_or_polymorph_note | CHGNet relaxation did not satisfy the configured force threshold. Generated CIF is geometrically plausible but does not match the reference prototype. |
| generated_challenge_znfe2o4_spinel | bad_contacts_or_invalid_geometry | relaxation_improved | prototype_or_polymorph_note | Pre-DFT geometry/contact checks flagged the generated CIF. CHGNet relaxation did not satisfy the configured force threshold. |
| generated_challenge_limn2o4_spinel | bad_contacts_or_invalid_geometry | relaxation_improved | prototype_or_polymorph_note | Pre-DFT geometry/contact checks flagged the generated CIF. CHGNet relaxation did not satisfy the configured force threshold. |
| sanity_lif_rocksalt | relaxed_structure_collapsed | relaxation_improved | prototype_or_polymorph_note | Relaxed volume ratio or relaxation error indicates possible collapse. Generated CIF is geometrically plausible but does not match the reference prototype. MLIP consensus marks the structure stable while StructureMatcher does not match the reference. |
| sanity_nacl_rocksalt | wrong_prototype_or_symmetry | relaxation_improved | prototype_or_polymorph_note | Generated CIF is geometrically plausible but does not match the reference prototype. |
| generated_challenge_cspbbr3_perovskite | wrong_prototype_or_symmetry | relaxation_improved | prototype_or_polymorph_note | Generated CIF is geometrically plausible but does not match the reference prototype. |
| generated_challenge_cssni3_mapbi3_proxy | near_match | relaxation_improved | prototype_or_polymorph_note;family_alias_or_proxy | Generated CIF did not match, but the relaxed CIF matches the reference. Generated CIF is geometrically plausible but does not match the reference prototype. |
| sanity_zns_sphalerite | near_match | relaxation_improved | prototype_or_polymorph_note | Generated CIF did not match, but the relaxed CIF matches the reference. Generated CIF is geometrically plausible but does not match the reference prototype. MLIP consensus marks the structure stable while StructureMatcher does not match the reference. |
| generated_challenge_basno3_perovskite | wrong_prototype_or_symmetry | relaxation_improved | prototype_or_polymorph_note | Generated CIF is geometrically plausible but does not match the reference prototype. |
| generated_challenge_baceo3_perovskite | exact_reference_match | relaxation_worsened | prototype_or_polymorph_note | StructureMatcher matched the generated CIF to the reference. |
| generated_challenge_feo_wustite | relaxed_structure_collapsed | relaxation_worsened | prototype_or_polymorph_note;family_alias_or_proxy | Relaxed volume ratio or relaxation error indicates possible collapse. Generated CIF is geometrically plausible but does not match the reference prototype. |
| sanity_nio_rocksalt | relaxed_structure_collapsed | relaxation_improved | prototype_or_polymorph_note | Relaxed volume ratio or relaxation error indicates possible collapse. Generated CIF is geometrically plausible but does not match the reference prototype. MLIP consensus marks the structure stable while StructureMatcher does not match the reference. |
| sanity_coo_rocksalt | relaxed_structure_collapsed | relaxation_worsened | prototype_or_polymorph_note | Relaxed volume ratio or relaxation error indicates possible collapse. Generated CIF is geometrically plausible but does not match the reference prototype. MLIP consensus marks the structure stable while StructureMatcher does not match the reference. |
| generated_challenge_mno_rocksalt | relaxation_failed | relaxation_improved | prototype_or_polymorph_note | CHGNet relaxation did not satisfy the configured force threshold. Generated CIF is geometrically plausible but does not match the reference prototype. |
| sanity_zro2_fluorite | relaxed_structure_collapsed | relaxation_improved | prototype_or_polymorph_note;family_alias_or_proxy | CHGNet relaxation did not satisfy the configured force threshold. Relaxed volume ratio or relaxation error indicates possible collapse. Generated CIF is geometrically plausible but does not match the reference prototype. |
| sanity_ceo2_fluorite | bad_contacts_or_invalid_geometry | relaxation_improved | prototype_or_polymorph_note | Pre-DFT geometry/contact checks flagged the generated CIF. CHGNet relaxation did not satisfy the configured force threshold. |
| generated_challenge_pbs_rocksalt | wrong_prototype_or_symmetry | relaxation_improved | prototype_or_polymorph_note | Generated CIF is geometrically plausible but does not match the reference prototype. |
| generated_challenge_fes2_pyrite | wrong_prototype_or_symmetry | relaxation_improved | prototype_or_polymorph_note | Generated CIF is geometrically plausible but does not match the reference prototype. |
| generated_challenge_cos2_pyrite | wrong_prototype_or_symmetry | relaxation_improved | prototype_or_polymorph_note | Generated CIF is geometrically plausible but does not match the reference prototype. |
| generated_challenge_nis2_pyrite | relaxation_failed | relaxation_improved | prototype_or_polymorph_note | CHGNet relaxation did not satisfy the configured force threshold. Generated CIF is geometrically plausible but does not match the reference prototype. |
