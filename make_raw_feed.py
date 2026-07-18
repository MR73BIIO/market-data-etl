"""Simulate a raw exchange-API pull with the usual real-world defects:
duplicate rows, missing intervals (gaps), and out-of-order timestamps."""
import numpy as np, pandas as pd

np.random.seed(7)
STEP_MS = 3_600_000                      # 1h candles
N = 2160                                  # 90 days
start = pd.Timestamp("2026-01-01", tz="UTC").value // 10**6

# --- ground-truth clean series (a random-walk OHLCV) ---------------------
ts = np.arange(start, start + N * STEP_MS, STEP_MS)
price = 42000 + np.cumsum(np.random.randn(N) * 120)
rows = []
for i, t in enumerate(ts):
    o = price[i]
    c = o + np.random.randn() * 60
    h = max(o, c) + abs(np.random.randn() * 40)
    l = min(o, c) - abs(np.random.randn() * 40)
    v = abs(np.random.randn() * 500 + 1200)
    rows.append([int(t), round(o, 2), round(h, 2), round(l, 2), round(c, 2), round(v, 3)])
full = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume"])

# --- inject defects to mimic a flaky pull --------------------------------
messy = full.copy()
gap_idx = np.random.choice(messy.index[10:-10], 40, replace=False)   # 40 missing
messy = messy.drop(index=gap_idx)
dupes = messy.sample(30, random_state=1)                              # 30 duplicates
messy = pd.concat([messy, dupes])
messy = messy.sample(frac=1, random_state=2).reset_index(drop=True)   # shuffle order

messy.to_csv("raw_feed.csv", index=False)
full.to_csv("_reference_source.csv", index=False)   # stands in for a re-fetch source
print(f"raw_feed.csv: {len(messy)} rows "
      f"({messy.duplicated('open_time').sum()} duplicate timestamps, "
      f"{40} missing intervals, unsorted)")
