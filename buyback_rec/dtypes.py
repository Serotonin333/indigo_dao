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
    ("trigger_time", "datetime64[s]"),
    ("amount", np.float32),
    ("price", np.float32),
    ("purchased", np.float32),
    ("ref_price", np.float32),
    ("ratio", np.float32),
    ("discount", np.float32),
    ("running_allocated", np.float32),
    ("running_spent", np.float32),
    ("running_purchased", np.float32),
    ("remaining_amount", np.float32),
]

buyback_pa = [
    ("trigger_time", pa.timestamp("s")),
    ("amount", pa.float32()),
    ("price", pa.float32()),
    ("purchased", pa.float32()),
    ("ref_price", pa.float32()),
    ("ratio", pa.float32()),
    ("discount", pa.float32()),
    ("running_allocated", pa.float32()),
    ("running_spent", pa.float32()),
    ("running_purchased", pa.float32()),
    ("remaining_amount", pa.float32()),
]


DTYPE_CANDLE = np.dtype(candle_np)
DTYPE_BUYBACK = np.dtype(buyback_np)

SCHEMA_CANDLE = pa.schema(candle_pa)
SCHEMA_BUYBACK = pa.schema(buyback_pa)

if __name__ == "__main__":
    print(DTYPE_BUYBACK)
    print(SCHEMA_BUYBACK)
