import pandas as pd
df = pd.read_csv("Dataset/Astra_Case_cleaned.csv")
print("Columns:", list(df.columns))
print("Shape:", df.shape)
print("\nDtypes:")
print(df.dtypes)
print("\nSample:")
print(df.head(2))
print("\nproduct_id sample:", df["product_id"].head(10).tolist())
print("\nunique product_ids:", df["product_id"].nunique())

