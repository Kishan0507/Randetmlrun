# Data directory

## Provenance and integrity

### MLRan released data (`data/raw/mlran/`)

- **Source:** https://github.com/faithfulco/mlran
- **Source commit:** `ec2651fd5d791a63dded5d454cef2ec01f1500e3` (shallow clone, 2026-10-14)
- **Licence:** MIT (attribute Onwuegbuche et al.)
- **Paper:** "MLRan: A behavioural dataset for ransomware analysis and detection", JNCA 250 (2026) 104475

**Files from `6_experiments/FS_MLRan_Datasets/`:**

| File | SHA256 |
|---|---|
| `MLRan_X_train_RFE.csv` | `AAF75D5754AAC247B93E2A7D0BAA449CCB3EACC08117F50DFA0FB422AFF3DB1F` |
| `MLRan_X_test_RFE.csv` | `792E7BEA9CCFE8BB056A05BC4751EBF18311C55E548D1B80910214C052EE8E16` |
| `MLRan_labels.csv` | `1E00F2E11E02A34859E8863808422933988C151E8C821A88247798B051227E4F` |
| `RFE_selected_feature_names_dic.json` | `2990CF09143C3B8A40D2C6EDC0F794D79B736B06657BB0D5A7F99B7359A1195A` |
| `type_train_sampleids.csv` | `C897BF35FABC0F16C15FA61A60E55BFA42D7B9D0075D62893FA226F9A80C7120` |
| `type_test_sampleids.csv` | `7250D3EF5E495DB85E3668412FA16FBADA9EC8ACD4ACA6FA395F774A9344FF50` |
| `mlran_dataset_metadata.csv` | `0E275F49C2995CC31181D43B7F30E266BE8ECB7E4BF45DCC8BF6CC4CA7637A5A` |

**Files from `2_collected_samples_metadata/`:**

| File | SHA256 |
|---|---|
| `goodware_samples_description.csv` | `C75D0F56BD490D2FC1E48895A8FA73D9A60802F17D1620D3F08A604D99A0541D` |
| `ransomware_samples_families_description.csv` | `8B79C2FB890843A3FA6D18C8B2957D763ABDCB9D8F76D9FB292734144F0609B0` |

### RanSMAP data (`data/raw/ransmap/`)

- **Source:** https://github.com/manabu-hirano/RanSMAP
- **Source commit:** _(to be filled after clone completes)_
- **Licence:** _(to be verified from repo)_
- **Details:** See decision D-002 in `memory/05_DECISIONS.md`

## Rules

- **Never edit files in `data/raw/`.** Derived data goes to `data/processed/` with a version tag.
- Raw data is tracked by hash (above), not committed as large files.

## Full MLRan dataset status (D-003)

As of 2026-10-14, the full 6.4M-feature MLRan dataset is **NOT public**.
The `5_mlran_dataset/README.md` in the upstream repo still says:
> "The full MLRan dataset, containing all features, will be released after the paper is accepted for publication."

Only the 483-feature RFE subset is available in `6_experiments/FS_MLRan_Datasets/`.
