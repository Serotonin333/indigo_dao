import numpy as np
from scipy.stats import norm
from dataclasses import dataclass
import pandas as pd
import pyarrow as pa
import http.client
import json
from itertools import accumulate
from matplotlib import pyplot as plt
from scipy.stats import gamma
from datetime import datetime, timedelta
from pyarrow import dataset as ds
from pathlib import Path
import warnings
from dtypes import SCHEMA_BUYBACK

plt.style.use("dark_background")


@dataclass
class Buyback:
    ratios: np.ndarray
    discounts: np.ndarray
    ref_price: float = None
    amount_allocated: float = None
    amount_purchased: float = 0

    def __post_init__(self):
        self.ratios = np.array(self.ratios)
        self.discounts = np.array(self.discounts)
        if np.round(self.ratios.sum(), decimals=3) != 1.0:
            warnings.warn(
                "Input `ratios` do not add up to 1. They will automatically be normalized."
            )
            self.ratios = self.ratios / self.ratios.sum()
        if self.amount_allocated is not None:
            self.amounts = self.amount_allocated * self.ratios
        else:
            self.amounts = np.zeros(self.ratios.shape)
        self._schema = SCHEMA_BUYBACK
        self.history = []
        if (self.discounts > 100).any():
            raise ValueError("Items in `discounts` cannot be greater than 100%")

    def add_amount(self, amount) -> None:
        self.amounts = (
            self.amounts + amount * self.ratios
        )  # add the fractional amount to `amounts`
        self.amount_allocated = (
            self.amount_allocated + amount
        )  # add to the total amount toward buybacks

    def check_do_buyback(
        self, account_index: int, data: pd.DataFrame, append_history: bool = True
    ) -> pa.RecordBatch:
        """Checks if the amount allocated within `account_index` should be used for buybacks within the
        period provided by `data` (which is expected to only contain data within the latest refresh)
        """
        ratio = self.ratios[account_index]
        discount = self.discounts[account_index]
        amount = self.amounts[account_index]
        buyback_price = self.ref_price * (100 - discount) / 100
        price_hit = data[data.loc[:, "low"] < buyback_price]
        if (amount > 0) and len(price_hit):
            buyback_amount = amount
            self.amounts[account_index] = 0
            self.amount_purchased = self.amount_purchased + buyback_amount
            record_dict = {
                "trigger_time": [price_hit.iloc[0]["start_time"]],
                "amount": [buyback_amount],
                "price": [buyback_price],
                "ref_price": [self.ref_price],
                "ratio": [ratio],
                "discount": [discount],
                "running_allocated": [self.amount_allocated],
                "running_purchased": [self.amount_purchased],
            }
            record = pa.record_batch(record_dict, SCHEMA_BUYBACK)
            if append_history:
                self.history.append(record)
        else:
            record = None

        return record

    def simulate_buybacks(
        self,
        data: pd.DataFrame | pa.Table,
        refresh_amounts: float | np.ndarray = None,
        refresh_intervals: timedelta | np.ndarray = None,
    ) -> pa.Table:
        """_summary_

        Args:
            data (pd.DataFrame | pa.Table): Price data used for the buyback simulation. Requires columns `start_time`, `open`, and `low`.
            refresh_amounts (float | np.ndarray, optional): Amount of assets used to add to the buyback pool. If a single value, it is assumed that this amount is allocated for each refresh interval. If `None`, the allocation is set to 0 for each refresh interval. Defaults to None.
            refresh_intervals (timedelta | np.ndarray, optional): Duration from the last allocation refreshment that the next allocation refresh will occur. If a single timedelta, the refresh interval is assumed to be repeated. If `None` allocations are not refreshed at any point and the refresh interval is set to the entire interval spanned by the `data`. Defaults to None.

        Returns:
            _type_: _description_
        """
        if isinstance(data, pa.Table):
            data = data.to_pandas()
        first_timestamp = data.iloc[0]["start_time"]
        full_duration = data.iloc[-1]["start_time"] - first_timestamp

        if refresh_intervals is None:
            refresh_intervals = np.array([full_duration])
        elif not isinstance(refresh_intervals, np.ndarray):
            # if it's a single value explicitly create each refresh time
            refresh_intervals = np.arange(
                refresh_intervals, full_duration, refresh_intervals
            )

        # NOTE: it would be quicker to just require a consistent time delta and use some integer multiple (index) for the refresh interval.
        refresh_timestamps = first_timestamp + refresh_intervals
        refresh_idxs = np.array(
            [
                np.argmin(abs(data.loc[:, "start_time"] - refresh))
                for refresh in refresh_timestamps
            ]
        )
        n_refresh = len(refresh_idxs)

        if refresh_amounts is None:
            refresh_amounts = np.zeros(refresh_intervals.shape)
        elif not isinstance(refresh_amounts, np.ndarray):
            # if it's a single value explicitly create each new allocation
            refresh_amounts = np.ones(refresh_intervals.shape) * refresh_amounts

        for idx, refresh_idx, refresh_amount in list(
            zip(np.arange(n_refresh), refresh_idxs, refresh_amounts)
        ):
            self.ref_price = data.loc[idx, "open"]
            if idx > 0:  # run current allocation first before refreshing
                self.add_amount(refresh_amount)
            # TODO: If we skip the first allocation then we are missing one of the refresh points?
            refresh_view = data.loc[idx:refresh_idx, :]
            for account_index in range(len(self.ratios)):
                self.check_do_buyback(account_index=account_index, data=refresh_view)

        return pa.Table.from_batches(self.history)


def get_breakpoints(
    timestamps: list | np.ndarray | pd.DataFrame,
    window_time: timedelta,
    step_time: timedelta,
):
    """Gets the break point indicies assuming the `timestamps` data is sorted and has a constant time step."""
    if not isinstance(timestamps, pd.DataFrame):
        timestamps = pd.DataFrame(timestamps, columns=["start_time"])

    idx_time = timestamps.iloc[1] - timestamps.iloc[0]
    step_idx = int(window_time / step_time)
    window_idx = int(window_time / idx_time)
    window_start_times = timestamps[:-window_idx:step_idx]
    window_start_idx = window_start_times.index
    return [(start_idx, start_idx + window_idx) for start_idx in window_start_idx]


if __name__ == "__main__":
    run_timescale = timedelta(days=120)  # 4 month windows
    step_size = timedelta(days=5)
    ratios = [0.1, 0.2, 0.3, 0.4]
    discounts = [61.8, 38.2, 23.6, 0]
    initial_allocation = 100_000
    refresh_amount = 10_000
    refresh_interval = timedelta(days=5)
    ds_path = Path.cwd() / "buyback_rec/database"
    dataset = ds.dataset(ds_path)
    df = (
        dataset.to_table()
        .to_pandas()
        .sort_values(by=["asset1", "asset2", "start_time"])
    )
    pairs = df[["asset1", "asset2"]].drop_duplicates().values

    data = []
    for asset1, asset2 in pairs:
        in_pair = (df["asset1"] == asset1) & (df["asset2"] == asset2)
        data.append(df[in_pair].copy().sort_values(by=["start_time"]).reset_index())

    for asset_pair in data:
        break_indicies = get_breakpoints(
            timestamps=asset_pair.start_time,
            window_time=run_timescale,
            step_time=step_size,
        )

        for (
            start,
            stop,
        ) in break_indicies:  # simulate a buyback startegy over each period
            buyback = Buyback(
                ratios=ratios, discounts=discounts, amount_allocated=initial_allocation
            )
            buyback.simulate_buybacks(
                asset_pair.loc[start:stop, :].copy(),
                refresh_amounts=refresh_amount,
                refresh_intervals=refresh_interval,
            )

    # create a
