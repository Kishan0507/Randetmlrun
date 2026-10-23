"""Quick inspection of the 4 new datasets in datasets/."""
import pandas as pd
import os

datasets_dir = "datasets"

# 1. Ransomware.csv (pipe-separated)
print("=" * 60)
print("1. Ransomware.csv")
print("=" * 60)
df = pd.read_csv(os.path.join(datasets_dir, "Ransomware.csv"), sep="|")
print(f"Shape: {df.shape}")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")
print(f"Label col 'legitimate' values: {df['legitimate'].value_counts().to_dict()}")
print(f"dtypes summary: {df.dtypes.value_counts().to_dict()}")
print(f"Size: {os.path.getsize(os.path.join(datasets_dir, 'Ransomware.csv'))/1e6:.1f}MB")
print()

# 2. data_file.csv
print("=" * 60)
print("2. data_file.csv")
print("=" * 60)
df2 = pd.read_csv(os.path.join(datasets_dir, "data_file.csv"))
print(f"Shape: {df2.shape}")
print(f"Columns ({len(df2.columns)}): {list(df2.columns)[:20]}...")
last_col = df2.columns[-1]
print(f"Last column: '{last_col}' -> values: {df2[last_col].value_counts().to_dict()}")
print(f"dtypes summary: {df2.dtypes.value_counts().to_dict()}")
print(f"Size: {os.path.getsize(os.path.join(datasets_dir, 'data_file.csv'))/1e6:.1f}MB")
print()

# 3. ransom.csv
print("=" * 60)
print("3. ransom.csv")
print("=" * 60)
df3 = pd.read_csv(os.path.join(datasets_dir, "ransom.csv"))
print(f"Shape: {df3.shape}")
print(f"Columns ({len(df3.columns)}): {list(df3.columns)[:20]}...")
last_col3 = df3.columns[-1]
print(f"Last column: '{last_col3}' -> values: {df3[last_col3].value_counts().to_dict()}")
print(f"dtypes summary: {df3.dtypes.value_counts().to_dict()}")
print(f"Size: {os.path.getsize(os.path.join(datasets_dir, 'ransom.csv'))/1e6:.1f}MB")
print()

# 4. ransomset-multiclass-dataset.csv
print("=" * 60)
print("4. ransomset-multiclass-dataset.csv")
print("=" * 60)
df4 = pd.read_csv(os.path.join(datasets_dir, "ransomset-multiclass-dataset.csv"))
print(f"Shape: {df4.shape}")
print(f"Columns ({len(df4.columns)}): {list(df4.columns)[:20]}...")
last_col4 = df4.columns[-1]
print(f"Last column: '{last_col4}' -> values: {df4[last_col4].value_counts().to_dict()}")
print(f"dtypes summary: {df4.dtypes.value_counts().to_dict()}")
print(f"Size: {os.path.getsize(os.path.join(datasets_dir, 'ransomset-multiclass-dataset.csv'))/1e6:.1f}MB")
