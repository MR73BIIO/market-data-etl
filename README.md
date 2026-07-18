# Market-Data ETL
Turns a raw exchange-API feed into a gap-free, validated time-series archive.
De-duplicates, sorts, detects missing intervals, back-fills them, and verifies
100% coverage before writing the clean archive.

## Run

```
pip install pandas numpy
python make_raw_feed.py        # tworzy raw_feed.csv + _reference_source.csv
python etl_pipeline.py raw_feed.csv
```
