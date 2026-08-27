# Paper advanced-validation manifests

`PAPER_16_MANIFEST.csv` freezes the sixteen generated structures named in
`eletronic_stack.md`. It references the original CIFs in their source run archives; it does not
copy, regenerate, or rewrite them. `cif_sha256` is the immutable byte-level provenance guard.

`intent_source` points to the original run artifact/target manifest. The Li2FeO3 request targeted
the held-out `C2/m` structure, but exact space-group retention is not required for that broad
layered-family generation request (`require_space_group=false`). All other rows retain their
explicit prototype space-group requirement.

`PAPER_6_DFT_MANIFEST.csv` is the required smoke/campaign subset. Its existence does not mean a
DFT calculation was run. Preparation, scheduler submission, and collection are separate states.

NASICON/NZP is intentionally excluded from both manifests.

