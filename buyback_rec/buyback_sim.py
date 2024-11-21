import numpy as np
from scipy.stats import norm
from dataclasses import dataclass
import pandas as pd
import http.client
import json
from itertools import accumulate
from matplotlib import pyplot as plt
from scipy.stats import gamma
from datetime import datetime, timedelta
from pyarrow import dataset as ds
from pathlib import Path

plt.style.use("dark_background")


@dataclass
class Buyback:
    ref_price: float
    ratios: list[float]
    discounts: list[float]

def get_breakpoints(timestamps: list | np.ndarray | pd.DataFrame, timescale: timedelta, step: timedelta):
    idx_time = timestamps.iloc[1] - timestamps.iloc[0]
    step_idx = int(timescale / step)
    start_times = [time for time in timestamps[::step_idx] if time + timescale < timestamps[-1]]
    end_times = [start + timescale for start in start_times]

    return start_times, end_times

if __name__=="__main__":
    run_timescale = timedelta(days=120)  # 4 month windows
    step_size = timedelta(days=5)
    ds_path = Path.cwd() / "buyback_rec/database"
    dataset = ds.dataset(ds_path)
    df = dataset.to_table().to_pandas().sort_values(by=["asset1", "asset2", "start_time"])
    pairs = df[["asset1", "asset2"]].drop_duplicates().values
    
    data = []
    for asset1, asset2 in pairs:
        in_pair = (df["asset1"] == asset1) & (df["asset2"] == asset2)
        data.append(df[in_pair])
    
    for d in data:
        print(get_breakpoints(timestamps=d.start_time, timescale=run_timescale, step=step_size))
    # create a 