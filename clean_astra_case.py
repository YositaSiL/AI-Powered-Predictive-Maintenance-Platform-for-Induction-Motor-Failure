import argparse
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_PATH = PROJECT_ROOT / "Dataset" / "Astra_Case.csv"
OUTPUT_PATH = PROJECT_ROOT / "Dataset" / "Astra_Case_cleaned.csv"

NUMERIC_COLS = [
    "air_temperature",
    "process_temperature",
    "rotational_speed",
    "torque",
    "tool_wear",
    "vibration",
    "electrical_current",
    "pressure",
    "rul",
]

BINARY_COLS = ["machine_failure", "twf", "hdf", "pwf", "osf", "rnf"]
STRING_COLS = ["udi", "product_id", "type"]

RANGE_RULES = {
    "air_temperature": (250, 320),
    "process_temperature": (280, 330),
    "rotational_speed": (0, 5000),
    "torque": (0, 100),
    "tool_wear": (0, 300),
    "vibration": (0, 10),
    "electrical_current": (0, 100),
    "pressure": (0, 10),
    "rul": (0, 1000),
}


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    return pd.read_csv(path)


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    if "udi" in df.columns:
        dupe_count = df.duplicated(subset=["udi"]).sum()
        if dupe_count > 0:
            print(f"Removing {dupe_count} duplicate rows based on 'udi'.")
            df = df.drop_duplicates(subset=["udi"])  # keep first occurrence
    else:
        dupe_count = df.duplicated().sum()
        if dupe_count > 0:
            print(f"Removing {dupe_count} fully duplicated rows.")
            df = df.drop_duplicates()
    return df


def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in STRING_COLS:
        if col in df.columns:
            df[col] = df[col].astype("string").fillna("unknown")

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in BINARY_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")

    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isna().sum()
    if missing.sum() > 0:
        print("Missing values found:")
        print(missing[missing > 0])

    for col in NUMERIC_COLS:
        if col in df.columns and df[col].isna().any():
            median_value = df[col].median()
            print(f"Filling missing numeric values in '{col}' with median: {median_value}")
            df[col] = df[col].fillna(median_value)

    for col in STRING_COLS:
        if col in df.columns and df[col].isna().any():
            df[col] = df[col].fillna("unknown")

    for col in BINARY_COLS:
        if col in df.columns and df[col].isna().any():
            df[col] = df[col].fillna(0).astype("int64")

    return df


def create_target(df: pd.DataFrame) -> pd.DataFrame:
    if "machine_failure" in df.columns:
        df["failure_label"] = df["machine_failure"].apply(lambda x: 1 if x == 1 else 0)
    else:
        raise KeyError("Column 'machine_failure' not found; cannot create target label.")
    return df


def validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    anomalies = {}
    for col, (min_value, max_value) in RANGE_RULES.items():
        if col not in df.columns:
            continue
        invalid = df[(df[col].notna()) & ((df[col] < min_value) | (df[col] > max_value))]
        if not invalid.empty:
            anomalies[col] = invalid.shape[0]
            print(f"Column '{col}' has {invalid.shape[0]} values outside range [{min_value}, {max_value}].")
            print(invalid[[col]].head(5))

    if not anomalies:
        print("All validated numeric columns are within expected ranges.")
    return df


def normalize_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    try:
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise ImportError("scikit-learn is required for normalization. Install it or omit --normalize.") from exc

    scaler = StandardScaler()
    df[cols] = scaler.fit_transform(df[cols])
    return df


def save_data(df: pd.DataFrame, output_path: Path) -> None:
    df.to_csv(output_path, index=False)
    print(f"Saved cleaned dataset to: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean the Astra_Case.csv dataset.")
    parser.add_argument("--input", type=Path, default=DATASET_PATH, help="Input CSV dataset path.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Output cleaned CSV path.")
    parser.add_argument("--normalize", action="store_true", help="Normalize numeric features after cleaning.")
    args = parser.parse_args()

    df = load_data(args.input)
    print(f"Loaded dataset with shape: {df.shape}")

    df = remove_duplicates(df)
    df = convert_types(df)
    df = fill_missing(df)
    df = validate_ranges(df)
    df = create_target(df)

    if args.normalize:
        print("Normalizing numeric columns...")
        df = normalize_columns(df, [c for c in NUMERIC_COLS if c in df.columns])

    save_data(df, args.output)


if __name__ == "__main__":
    main()
