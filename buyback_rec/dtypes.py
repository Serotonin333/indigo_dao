import numpy as np
import pyarrow as pa

candle_np = [
    ("asset1", np.str_),
    ("asset2", np.str_),
    ("start_time", "datetime64[s]"),
    ('low', np.float32),
    ('high', np.float32),
    ('open', np.float32),
    ('close', np.float32),
    ('volume', np.float32),
]

candle_pa = [
    ("asset1", pa.string()),
    ("asset2", pa.string()),
    ("start_time", pa.timestamp('s')),
    ('low', pa.float32()),
    ('high', pa.float32()),
    ('open', pa.float32()),
    ('close', pa.float32()),
    ('volume', pa.float32()),
]

DTYPE_CANDLE = np.dtype(candle_np)
SCHEMA_CANDLE = pa.schema(candle_pa)

if __name__=="__main__":
    print(DTYPE_CANDLE)
    print(SCHEMA_CANDLE)