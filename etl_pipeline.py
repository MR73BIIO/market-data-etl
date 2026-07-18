"""
Market-Data ETL Pipeline
Raw exchange feed -> de-duplicated, gap-free, validated time-series archive.

Steps:
  1. EXTRACT  load the raw pull
  2. TRANSFORM  drop duplicates, sort, build the expected timestamp grid,
                detect missing intervals, back-fill them by re-fetching
  3. VALIDATE  confirm 100% coverage against the expected grid
  4. LOAD  write the clean archive
"""
import sys, pandas as pd

STEP_MS = 3_600_000   # 1h

def refetch(missing_ts):
    """Re-fetch specific missing intervals. Here a reference CSV stands in
    for a second API call; in production this is a bounded API request for
    the missing time range."""
    src = pd.read_csv("_reference_source.csv")
    return src[src["open_time"].isin(missing_ts)]

def run(path):
    # 1. EXTRACT --------------------------------------------------------
    raw = pd.read_csv(path)
    n_raw = len(raw)

    # 2. TRANSFORM ------------------------------------------------------
    df = raw.drop_duplicates("open_time").sort_values("open_time")
    n_dupes = n_raw - len(df)

    lo, hi = df["open_time"].min(), df["open_time"].max()
    expected = set(range(lo, hi + STEP_MS, STEP_MS))
    missing = sorted(expected - set(df["open_time"]))
    n_gaps = len(missing)

    if missing:
        df = pd.concat([df, refetch(missing)]).sort_values("open_time")

    df = df.reset_index(drop=True)

    # 3. VALIDATE -------------------------------------------------------
    still_missing = sorted(expected - set(df["open_time"]))
    coverage = 100 * (1 - len(still_missing) / len(expected))
    ok = (len(still_missing) == 0
          and df["open_time"].is_monotonic_increasing
          and not df["open_time"].duplicated().any())

    # 4. LOAD -----------------------------------------------------------
    df["open_time_utc"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df.to_csv("clean_archive.csv", index=False)

    print("=" * 56)
    print("INTEGRITY REPORT")
    print("=" * 56)
    print(f"  Raw rows ingested     : {n_raw}")
    print(f"  Duplicate rows removed : {n_dupes}")
    print(f"  Gaps detected          : {n_gaps}")
    print(f"  Gaps back-filled       : {n_gaps - len(still_missing)}")
    print(f"  Final rows             : {len(df)}")
    print(f"  Expected intervals     : {len(expected)}")
    print(f"  Coverage               : {coverage:.2f}%")
    print(f"  Sorted & unique        : {df['open_time'].is_monotonic_increasing and not df['open_time'].duplicated().any()}")
    print(f"  ARCHIVE VALID          : {'YES' if ok else 'NO'}")
    print("\nSaved: clean_archive.csv")
    return dict(n_raw=n_raw, n_dupes=n_dupes, n_gaps=n_gaps,
                final=len(df), coverage=coverage, ok=ok)

if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "raw_feed.csv")
