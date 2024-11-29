import numpy as np
import pyarrow as pa

candle_np = [
    ("asset1", np.str_),
    ("asset2", np.str_),
    ("start_time", "datetime64[s]"),
    ("low", np.float32),
    ("high", np.float32),
    ("open", np.float32),
    ("close", np.float32),
    ("volume", np.float32),
]

candle_pa = [
    ("asset1", pa.string()),
    ("asset2", pa.string()),
    ("start_time", pa.timestamp("s")),
    ("low", pa.float32()),
    ("high", pa.float32()),
    ("open", pa.float32()),
    ("close", pa.float32()),
    ("volume", pa.float32()),
]

buyback_np = [
    ("identifier", np.str_),
    ("start_time", "datetime64[s]"),
    ("last_reset_time", "datetime64[s]"),
    ("trigger_time", "datetime64[s]"),
    ("amount", np.float32),
    ("price", np.float32),
    ("purchased", np.float32),
    ("ref_price", np.float32),
    ("ratio", np.float32),
    ("discount", np.float32),
    ("start_price", np.float32),
    ("running_allocated", np.float32),
    ("running_spent", np.float32),
    ("running_purchased", np.float32),
    ("running_return", np.float32),
    ("remaining_amount", np.float32),
]

overview_np = [
    ("identifier", np.str_),
    ("ratio", np.float32),
    ("discount", np.float32),
    ("refresh_amount", np.float32),
    ("refresh_interval", "timedelta64[s]"),
    ("delay_min", "timedelta64[s]"),
    ("delay_max", "timedelta64[s]"),
    ("delay_mean", "timedelta64[s]"),
    ("end_running_return", np.float32),
    ("end_discount_running_return", np.float32),
    ("running_return_mean", np.float32),
]

buyback_pa = [
    ("identifier", pa.string()),
    ("start_time", pa.timestamp("s")),
    ("last_reset_time", pa.timestamp("s")),
    ("trigger_time", pa.timestamp("s")),
    ("amount", pa.float32()),
    ("price", pa.float32()),
    ("purchased", pa.float32()),
    ("ref_price", pa.float32()),
    ("ratio", pa.float32()),
    ("discount", pa.float32()),
    ("start_price", pa.float32()),
    ("running_allocated", pa.float32()),
    ("running_spent", pa.float32()),
    ("running_purchased", pa.float32()),
    ("running_return", pa.float32()),
    ("remaining_amount", pa.float32()),
]

overview_pa = [
    ("identifier", pa.string()),
    ("ratio", pa.float32()),
    ("discount", pa.float32()),
    ("refresh_amount", pa.float32()),
    ("refresh_interval", pa.duration("s")),
    ("delay_min", pa.duration("s")),
    ("delay_max", pa.duration("s")),
    ("delay_mean", pa.duration("s")),
    ("end_running_return", pa.float32()),
    ("end_discount_running_return", pa.float32()),
    ("running_return_mean", pa.float32()),
]

settings_pa = [
    ("identifier", pa.string()),
    ("ratios", pa.list_(pa.float32())),
    ("discounts", pa.list_(pa.float32())),
    ("initial_allocations", pa.list_(pa.float32())),
    ("refresh_amounts", pa.list_(pa.float32())),
    ("refresh_intervals", pa.list_(pa.duration("s"))),
    ("run_duration", pa.duration("s")),
    ("asset1", pa.string()),
    ("asset2", pa.string()),
]

DTYPE_CANDLE = np.dtype(candle_np)
DTYPE_BUYBACK = np.dtype(buyback_np)
DTYPE_OVERVIEW = np.dtype(overview_np)

SCHEMA_CANDLE = pa.schema(candle_pa)
SCHEMA_BUYBACK = pa.schema(buyback_pa)
SCHEMA_OVERVIEW = pa.schema(overview_pa)
SCHEMA_SETTINGS = pa.schema(settings_pa)

if __name__ == "__main__":
    print(DTYPE_BUYBACK)
    print(SCHEMA_BUYBACK)
    print(SCHEMA_SETTINGS)
