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
import itertools

plt.style.use("dark_background")


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


@dataclass
class Buyback:
    identifier: str
    ratios: np.ndarray
    discounts: np.ndarray
    ref_price: float = None
    amount_allocated: float = None

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
        self.amount_spent = 0
        self.amount_purchased = 0
        self._schema = SCHEMA_BUYBACK
        self.history = []
        if (self.discounts > 100).any():
            raise ValueError("Items in `discounts` cannot be greater than 100%")

    @property
    def open_amount(self) -> float:
        return self.amounts.sum()

    def add_amount(self, amount) -> None:
        self.amounts = (
            self.amounts + amount * self.ratios
        )  # add the fractional amount to `amounts`
        self.amount_allocated = (
            self.amount_allocated + amount
        )  # add to the total amount toward buybacks

    def redistribute_amount(self) -> None:
        """Gathers all `amounts` remaining in pending orders and redistributes  according to `ratios`."""
        self.amounts = self.open_amount * self.ratios

    def check_do_buyback(
        self,
        account_index: int,
        data: pd.DataFrame,
        run_start_time: np.timedelta64 | None = None,
        run_start_price: float | None = None,
        append_history: bool = True,
    ) -> pa.RecordBatch:
        """Checks if the amount allocated within `account_index` should be used for buybacks within the
        period provided by `data` (which is expected to only contain data within the latest refresh)
        """
        if run_start_time is None:
            run_start_time = data.iloc[0]["start_time"]
        if run_start_price is None:
            run_start_price = data.iloc[0]["open"]
        ratio = self.ratios[account_index]
        discount = self.discounts[account_index]
        amount = self.amounts[account_index]
        buyback_price = self.ref_price * (100 - discount) / 100
        price_hit = data[data.loc[:, "low"] < buyback_price]
        if (amount > 0) and len(price_hit):
            spent = amount
            purchased = spent / buyback_price
            self.amounts[account_index] = 0
            self.amount_spent = self.amount_spent + spent
            self.amount_purchased = self.amount_purchased + purchased
            record_dict = {
                "identifier": [self.identifier],
                "start_time": [run_start_time],
                "last_reset_time": [data.iloc[0]["start_time"]],
                "trigger_time": [price_hit.iloc[0]["start_time"]],
                "amount": [spent],
                "price": [buyback_price],
                "purchased": [purchased],
                "ref_price": [self.ref_price],
                "ratio": [ratio],
                "discount": [discount],
                "start_price": [run_start_price],
                "running_allocated": [self.amount_allocated],
                "running_spent": [self.amount_spent],
                "running_purchased": [self.amount_purchased],
                "running_return": [
                    self.amount_purchased * buyback_price / self.amount_spent
                ],
                "remaining_amount": [self.open_amount],
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
        redistribute_on_refresh: bool = False,
    ) -> pa.Table:
        """_summary_

        Args:
            data (pd.DataFrame | pa.Table): Price data used for the buyback simulation. Requires columns `start_time`, `open`, and `low`.
            refresh_amounts (float | np.ndarray, optional): Amount of assets used to add to the buyback pool. If a single value, it is assumed that this amount is allocated for each refresh interval. If `None`, the allocation is set to 0 for each refresh interval. Defaults to None.
            refresh_intervals (timedelta | np.ndarray, optional): Duration from the last allocation refreshment that the next allocation refresh will occur. If a single timedelta, the refresh interval is assumed to be repeated. If `None` allocations are not refreshed at any point and the refresh interval is set to the entire interval spanned by the `data`. Defaults to None.
            redistribute_on_refresh (bool, optional): Flag, if set to True will gather all amounts in pending orders and redistribute according to the `ratios` each refresh interval. Defaults to False

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
        start_idxs = np.roll(refresh_idxs, shift=1)
        start_idxs[0] = 0

        if refresh_amounts is None:
            refresh_amounts = np.zeros(refresh_intervals.shape)
        elif not isinstance(refresh_amounts, np.ndarray):
            # if it's a single value explicitly create each new allocation
            refresh_amounts = np.ones(refresh_intervals.shape) * refresh_amounts

        for start_idx, refresh_idx, refresh_amount in list(
            zip(start_idxs, refresh_idxs, refresh_amounts)
        ):
            run_start_time = data.iloc[0]["start_time"]
            run_start_price = data.iloc[0]["open"]
            self.ref_price = data.loc[start_idx, "open"]
            refresh_view = data.loc[start_idx:refresh_idx, :]
            for account_index in range(len(self.ratios)):
                self.check_do_buyback(
                    account_index=account_index,
                    data=refresh_view,
                    run_start_time=run_start_time,
                    run_start_price=run_start_price,
                )

            # Refresh allocations for next buyback
            if redistribute_on_refresh:
                self.redistribute_amount()
            self.add_amount(refresh_amount)

        metadata = {
            "ratios": self.ratios,
            "discounts": self.discounts,
            "refresh_amounts": refresh_amounts,
            "refresh_intervals": refresh_intervals,
        }

        for key, value in metadata.items():
            if np.issubdtype(value.dtype, np.timedelta64):
                value = list(value.astype("timedelta64[s]").astype(int))
            metadata[key] = json.dumps(value, cls=NpEncoder)

        self._schema = self._schema.with_metadata(metadata)
        return pa.Table.from_batches(self.history, schema=self._schema)


def get_breakpoints(
    timestamps: list | np.ndarray | pd.DataFrame,
    window_time: timedelta,
    step_time: timedelta,
):
    """Gets the break point indicies assuming the `timestamps` data is sorted and has a constant time step."""
    if not isinstance(timestamps, pd.DataFrame):
        timestamps = pd.DataFrame(timestamps, columns=["start_time"])

    idx_time = (timestamps.iloc[1] - timestamps.iloc[0]).iloc[0]
    step_idx = int(window_time / step_time)
    window_idx = int(window_time / idx_time)
    window_start_times = timestamps[:-window_idx:step_idx]
    window_start_idx = window_start_times.index
    return [(start_idx, start_idx + window_idx) for start_idx in window_start_idx]


def decode_metadata(metadata):
    decoded = {}
    for key, value in metadata.items():
        d_key = key.decode("utf-8")
        d_value = np.array(json.loads(value)).astype(np.float32)
        if d_key == "refresh_intervals":
            d_value = d_value.astype("timedelta64[s]")
        decoded[d_key] = d_value
    return decoded


def buyback_overview(result: pa.Table):
    metadata = decode_metadata(result.schema.metadata)
    ratios = metadata["ratios"]
    discounts = metadata["discounts"]
    refresh_amounts = metadata["refresh_amounts"]
    refresh_intervals = metadata["refresh_intervals"]

    result = result.to_pandas()
    identifiers = result["identifier"].drop_duplicates()

    id_list = []
    ratio_list = []
    discount_list = []
    delay_min = []
    delay_max = []
    delay_mean = []
    end_discount_running_return = []
    # don't do `for (ident, ratio), subtable in result.groupby(["identifier", "ratio"]):` because we want metadata from the orders that didn't execute too
    for ident in identifiers:  # group metadata for each backtest run
        for r_idx, ratio in enumerate(ratios):
            id_list.append(ident)
            ratio_list.append(ratio)
            discount_list.append(discounts[r_idx])
            idxs = result[
                (result["ratio"] == ratio) & (result["identifier"] == ident)
            ].index
            subtable = result.loc[idxs, :]
            if not len(subtable):
                delay_min.append(None)
                delay_max.append(None)
                delay_mean.append(None)
                end_discount_running_return.append(None)
            else:
                subtable["trigger_delay"] = (
                    subtable["trigger_time"] - subtable["start_time"]
                )
                subtable["discount_running_spent"] = subtable["amount"].cumsum()
                subtable["discount_running_purchased"] = subtable["purchased"].cumsum()
                subtable["discount_running_return"] = (
                    subtable["discount_running_purchased"]
                    * subtable["price"]
                    / subtable["discount_running_spent"]
                )

                desc = subtable.describe()
                delay_min.append(desc.loc["min", "trigger_delay"])
                delay_max.append(desc.loc["max", "trigger_delay"])
                delay_mean.append(desc.loc["mean", "trigger_delay"])
                end_discount_running_return.append(
                    subtable["discount_running_return"].values[-1]
                )

    # aggregate metadata for all groups

    overview = {
        "identifier": id_list,
        "ratio": ratio_list,
        "discount": discount_list,
        "delay_min": delay_min,
        "delay_max": delay_max,
        "delay_mean": delay_mean,
        "end_discount_running_return": end_discount_running_return,
    }
    overview = pa.table(overview)


if __name__ == "__main__":
    counter = itertools.count()
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
    results = []
    for asset1, asset2 in pairs:
        in_pair = (df["asset1"] == asset1) & (df["asset2"] == asset2)
        data.append(
            df[in_pair].copy().sort_values(by=["start_time"]).reset_index(drop=True)
        )

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
                identifier=str(next(counter)),
                ratios=ratios,
                discounts=discounts,
                amount_allocated=initial_allocation,
            )
            results.append(
                buyback.simulate_buybacks(
                    asset_pair.loc[start:stop, :].copy().reset_index(drop=True),
                    refresh_amounts=refresh_amount,
                    refresh_intervals=refresh_interval,
                    redistribute_on_refresh=True,
                )
            )
            buyback_overview(result=results[-1])
