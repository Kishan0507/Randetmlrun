# 03 — Paper audit (check before citing any number)

Paper: Onwuegbuche et al., JNCA 250 (2026) 104475. Status values: `UNVERIFIED` · `CONFIRMED` · `NOT CONFIRMED` · `UNCLEAR`.
Items A1–A12 were found by reading the paper text. Nobody has verified them against the data yet (T-P0-05).

| ID | Where in paper | Observation | How to check | Status | Evidence / who |
|---|---|---|---|---|---|
| A1 | Sec. 6.2, Algorithm 2, Fig. 9 | RFE feature percentage is chosen by **balanced accuracy on the test set** (Alg. 2 lines 15–21). This contradicts the paper's own "no test snooping" guideline (Sec. 3.4.3). The best point (2% / 483 feats) differs from neighbours only in the 3rd decimal (axis 0.972–0.980) | Re-run RFE with selection on a chronological validation slice inside train | UNVERIFIED | |
| A2 | Table 6 caption | Caption says "XGBoost" but the models listed are LightGBM, Decision Trees, LR, RF, Extra Trees. Table 5 caption likewise | Read captions | UNVERIFIED | |
| A3 | Table 5, Chi-Square / LightGBM row | F1 = 98.41 while Acc/Pre/Re ≈ 93.85 — inconsistent (F1 cannot exceed both precision and recall) | Recompute F1 from Pre & Re | UNVERIFIED | |
| A4 | Abstract vs tables | Abstract says accuracy/precision/recall "up to 98.7 / 98.9 / 98.5". Tables 5–6 show best binary accuracy 98.15 (Table 6) / 98.05 (Table 5). Confusion matrix (Fig. 12): ransomware recall = 459/465 = 98.7%, precision = 459/471 = 97.5%, accuracy = 957/975 = 98.15% | Recompute from Fig. 12 and Table 6 | UNVERIFIED | |
| A5 | Result 2 box vs Table 7 | Text says STR = 46.58% after RFE; table says 46.1697% | Compare | UNVERIFIED | |
| A6 | Table 1, ShieldFS row | `#Ran` = 2245 and `#Good` = 383, while the text says 383 ransomware instances and 2245 applications (goodware) — columns look swapped | Compare with Sec. 2.1 | UNVERIFIED | |
| A7 | Intro vs abstract | Abstract: samples span 2006–2024; Intro: families 2008–2024 (goodware starts 2006). Consistent only if read carefully; do not quote "2006–2024" for ransomware | Check metadata `first_submission_date_year` by class | UNVERIFIED | |
| A8 | Sec. 7.1.1 | "65-class classification problem": 64 families + goodware = 65 only if goodware counted as a class. Confirm how family labels are encoded (`family_label` in labels CSV) | Inspect `MLRan_labels.csv` | UNVERIFIED | |
| A9 | Algorithm 2 line 6 | `⌊(p/100)·|X_train|⌋` — if `|X_train|` means rows, 2% would be ≈78, not 483. Only consistent if it means number of features (24,162 × 2% = 483) | Read code in repo `6_experiments/2_Impact_FS.ipynb` | UNVERIFIED | |
| A10 | Sec. 5.5 vs Table 9 | Sec. 5.5 says tuning uses ROC-AUC (binary) and weighted-F1 (multiclass); Table 9 lists LR solver `lbfgs`/`liblinear`, but Algorithm 2 uses `saga`. Check which solver produced Table 6 | Read notebooks | UNVERIFIED | |
| A11 | Fig. 6 vs text | Curated source: 785 collected, 777 analysed (text says "sample size remained unchanged" then 777); MarauderMap 575 analysed but flowchart shows 23 families vs text 25 | Compare Fig. 6 and Sec. 4.2 | UNVERIFIED | |
| A12 | Sec. 6.4.1 | 11 of 12 false positives said to be 2023–24 goodware; text lists 2024 (7) + 2023 (4) + 2022 (1) = 12 → 11 in 2023–24. Fine, but check whether test set simply contains mostly recent goodware (base-rate effect) | Count goodware per year in test set | UNVERIFIED | |
| A13 | Fig. 11 / SHAP text | Top feature `STRING:!this program cannot be run in dos mode` is present in nearly all Windows executables; its SHAP importance may reflect packaging/collection artefacts (benign installers vs raw ransomware executables) rather than behaviour | Check feature prevalence by class and by source | UNVERIFIED | |
| A14 | Dataset construction | Goodware are installers from one site, ransomware from malware repos: possible **source/format bias** (installer vs bare payload). A model may learn "installer-ness" | Source-held-out evaluation; drop top static-looking features and re-evaluate | UNVERIFIED | |

## Rules
- Do not cite a paper number in our report until the related audit item is `CONFIRMED` or we recomputed it ourselves.
- Add new items at the bottom with the next ID. Put code/notebook path in Evidence.
