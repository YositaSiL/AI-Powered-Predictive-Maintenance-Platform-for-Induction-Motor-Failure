from Frontend.utils.db_connection import load_data

df, _source = load_data()

print(df.head())
print()
print(f"Total Rows: {len(df)}")
