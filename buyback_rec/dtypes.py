import pyarrow as pa

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
    ("num_discount_buybacks", pa.int32()),
    ("num_discount_refresh", pa.int32()),
    ("num_buybacks", pa.int32()),
    ("num_refresh", pa.int32()),
]

overview_pa = [
    ("identifier", pa.string()),
    ("ratio", pa.float32()),
    ("discount", pa.float32()),
    ("delay_min", pa.duration("s")),
    ("delay_max", pa.duration("s")),
    ("delay_mean", pa.duration("s")),
    ("end_num_discount_buybacks", pa.int32()),
    ("end_num_discount_refresh", pa.int32()),
    ("end_num_buybacks", pa.int32()),
    ("end_num_refresh", pa.int32()),
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
    ("redistribute_on_refresh", pa.bool_()),
    ("start_price", pa.float32()),
]


SCHEMA_CANDLE = pa.schema(candle_pa)
SCHEMA_BUYBACK = pa.schema(buyback_pa)
SCHEMA_OVERVIEW = pa.schema(overview_pa)
SCHEMA_SETTINGS = pa.schema(settings_pa)

if __name__ == "__main__":
    print(SCHEMA_BUYBACK)
    print(SCHEMA_SETTINGS)
