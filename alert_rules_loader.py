import pandas as pd
import os

# Base folder = one level up from current file
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

CSV_FILE_PATH = os.path.join(BASE_DIR, "alert.csv")
PARQUET_FILE_PATH = os.path.join(BASE_DIR, "alert_rules.parquet")

# Internal cache
_parquet_df = None
load_count = 0  # For debugging how many times file is loaded

def load_alert_rules(engine: str = "pyarrow"):
    global _parquet_df, load_count

    if _parquet_df is not None:
        print("[alert_rules_loader] DataFrame already loaded in memory")
        return _parquet_df

    regenerate = False

    if os.path.exists(PARQUET_FILE_PATH):
        # Compare modified times
        csv_mtime = os.path.getmtime(CSV_FILE_PATH)
        parquet_mtime = os.path.getmtime(PARQUET_FILE_PATH)
        if csv_mtime > parquet_mtime:
            print("[alert_rules_loader] CSV is newer -> regenerating Parquet")
            os.remove(PARQUET_FILE_PATH)
            regenerate = True
        else:
            print(f"[alert_rules_loader] Parquet file found: {PARQUET_FILE_PATH}")
    else:
        regenerate = True

    # Create parquet if needed
    if regenerate:
        df = pd.read_csv(CSV_FILE_PATH)
        df.to_parquet(PARQUET_FILE_PATH, index=False, engine=engine)
        print(f"[alert_rules_loader] CSV → Parquet conversion done (engine={engine})")

    # Load parquet into memory
    _parquet_df = pd.read_parquet(PARQUET_FILE_PATH, engine=engine)
    load_count += 1
    print(f"[alert_rules_loader] Parquet loaded into memory — load count = {load_count}, rows = {len(_parquet_df)}")

    return _parquet_df