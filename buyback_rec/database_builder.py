import numpy as np
import pyarrow as pa
from pyarrow import parquet as pq
import pandas as pd
import http.client
import json
import datetime
from dtypes import SCHEMA_CANDLE
from time import sleep
from pathlib import Path

conn = http.client.HTTPSConnection("api.exchange.coinbase.com")
res_agg_lim = 300   # most aggregations coinbase will return at once
req_per_min_lim = 10    # says 10 per second, but that doesn't seem right for public API
sleep_time = 60 / req_per_min_lim
payload = ""
headers = {"Content-Type": "application/json", "User-Agent": "someone"}
token = "BTC"
token2 = 'USD'

# -------Market Depth------
# level=1 gives the highest bid and lowest ask
# level=2 gives the full orderbook (aggregated) and auction info
# level=3 gives the full orderbook (non aggregated) and auction info
# INFO: Level 1 and Level 2 are recommended for polling. For the most up-to-date data, consider using the WebSocket stream.
# Level 3 is only recommended for users wishing to maintain a full real-time order book using the WebSocket stream.
# Abuse of Level 3 via polling can cause your access to be limited or blocked.
# conn.request("GET", f"/products/{token}-USD/book?level=2", payload, headers)
# res = conn.getresponse()
# data = res.read()

# -----Candles------
granularity=86400   # 1 day = 86400 s
start_date = datetime.datetime(2017,1,1)
end_date = datetime.datetime.now()
start = start_date
stop = min(start + datetime.timedelta(seconds=(res_agg_lim-1)*granularity), end_date)
running_table = SCHEMA_CANDLE.empty_table()
table_size_lim = 100 * 1024**2  # X MB in bytes
database = Path.cwd() / "buyback_rec/database"
while start < end_date:
    conn.request("GET", f"/products/{token}-{token2}/candles?start={start.isoformat()}&end={stop.isoformat()}&granularity={granularity}", payload, headers)
    res = conn.getresponse()
    res_data = res.read()
    json_obj = json.loads(res_data.decode("utf-8"))

    data = pd.DataFrame(json_obj, columns=['start_time','low', 'high', "open", 'close', 'volume' ])
    data["start_time"] = pd.to_datetime(data["start_time"], unit='s')
    data["asset1"] = token
    data["asset2"] = token2

    table = pa.Table.from_pandas(data, preserve_index=False, schema=SCHEMA_CANDLE)
    running_table = pa.concat_tables([running_table, table])

    start = stop + datetime.timedelta(seconds=granularity)
    stop = min(start + datetime.timedelta(seconds=(res_agg_lim-1)*granularity), end_date)
    sleep(sleep_time)   # sleep to prevent over requesting from API

running_table = running_table.combine_chunks()
pq.write_table(running_table, (database / f"{token}-{token2}_candles.parquet").absolute())

