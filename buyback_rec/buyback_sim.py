import numpy as np
from dataclasses import dataclass
import pandas as pd
import pyarrow as pa
import json
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from pyarrow import dataset as ds
from pyarrow import parquet as pq
from pathlib import Path
import warnings
from dtypes import SCHEMA_BUYBACK, SCHEMA_OVERVIEW, SCHEMA_SETTINGS
from uuid import uuid4
import scipy

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
        self.n_discount_refresh = np.zeros((len(self.discounts),))
        self.n_refresh = 0
        self.n_discount_buybacks = np.zeros((len(self.discounts),))
        self.n_buybacks = 0
        self._schema = SCHEMA_BUYBACK
        self.history = []
        if (self.discounts > 100).any():
            raise ValueError("Items in `discounts` cannot be greater than 100%")

    @property
    def open_amount(self) -> float:
        return self.amounts.sum()

    def add_amount_proportionally(self, amount: float):
        """Adds an amount split proportionally among all discounts"""
        amounts = amount * self.ratios
        indicies = np.arange(len(amounts))
        self.add_amounts(amounts=amounts, indicies=indicies)

    def add_amounts(self, amounts: list[float], indicies: list[int]) -> None:
        """Adds a given amount to each discount index."""
        for idx, amount in list(zip(indicies, amounts)):
            self.amounts[idx] = (
                self.amounts[idx] + amount
            )  # add the fractional amount to `amounts`
            self.amount_allocated = (
                self.amount_allocated + amount
            )  # add to the total amount toward buybacks
            self.n_discount_refresh[idx] += 1
            self.n_refresh += 1

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
            self.n_discount_buybacks[account_index] += 1
            self.n_buybacks += 1
            spent = amount
            purchased = spent / buyback_price
            self.amounts[account_index] = 0
            self.amount_spent = self.amount_spent + spent
            self.amount_purchased = self.amount_purchased + purchased
            record_dict = {
                "identifier": [str(self.identifier)],
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
                "num_discount_buybacks": [self.n_discount_buybacks[account_index]],
                "num_discount_refresh": [self.n_discount_refresh[account_index]],
                "num_buybacks": [self.n_buybacks],
                "num_refresh": [self.n_refresh],
            }
            record = pa.record_batch(record_dict, SCHEMA_BUYBACK)
            if append_history:
                self.history.append(record)
        else:
            record = None

        return record

    def simulate_buybacks(
        self,
        price_data: pd.DataFrame | pa.Table,
        refresh_amounts: float | np.ndarray = None,
        refresh_intervals: timedelta | np.ndarray = None,
        redistribute_on_refresh: bool = False,
    ) -> pa.Table:
        """Method to run a simulation of the buyback structure using the input price candlestick `price_data`. Optionally, additional allocations for buybacks may be added at points during the simulation as specified by the `refresh_amounts` and `refresh_intervals` arrays. If a single value is passed for these arguments it is assumed that the amount specified is repeated every refresh interval until the end date of the simulation. Additionally, a flag can enable the pending limit orders to be withdrawn and resubmitted/redistributed along with the refresh amount if `redistribute_on_refresh` is set to True.

        Args:
            data (pd.DataFrame | pa.Table): Price data used for the buyback simulation. Requires columns `start_time`, `open`, and `low`.
            refresh_amounts (float | np.ndarray, optional): Amount of assets used to add to the buyback pool. If a single value, it is assumed that this amount is allocated for each refresh interval. If `None`, the allocation is set to 0 for each refresh interval. Defaults to None.
            refresh_intervals (timedelta | np.ndarray, optional): Duration from the last allocation refreshment that the next allocation refresh will occur. If a single timedelta, the refresh interval is assumed to be repeated. If `None` allocations are not refreshed at any point and the refresh interval is set to the entire interval spanned by the `data`. Defaults to None.
            redistribute_on_refresh (bool, optional): Flag, if set to True will gather all amounts in pending orders and redistribute according to the `ratios` each refresh interval. Defaults to False

        Returns:
            pa.Table: Table containing the history of buybacks transacted
        """
        if isinstance(price_data, pa.Table):
            price_data = price_data.to_pandas()
        first_timestamp = price_data.iloc[0]["start_time"]
        full_duration = price_data.iloc[-1]["start_time"] - first_timestamp

        if refresh_intervals is None:
            refresh_intervals = np.array([full_duration])
        elif not isinstance(refresh_intervals, np.ndarray):
            # if it's a single value explicitly create each refresh time
            refresh_intervals = np.arange(
                refresh_intervals, full_duration + refresh_intervals, refresh_intervals
            )

        # NOTE: it would be quicker to just require a consistent time delta and use some integer multiple (index) for the refresh interval.
        refresh_timestamps = first_timestamp + refresh_intervals
        refresh_idxs = np.array(
            [
                np.argmin(abs(price_data.loc[:, "start_time"] - refresh))
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

        # TODO: there is potentially a case here where there is some time less than the refresh interval that isn't accounted for
        for start_idx, refresh_idx, refresh_amount in list(
            zip(start_idxs, refresh_idxs, refresh_amounts)
        ):
            run_start_time = price_data.iloc[0]["start_time"]
            run_start_price = price_data.iloc[0]["open"]
            self.ref_price = price_data.loc[start_idx, "open"]
            refresh_view = price_data.loc[start_idx:refresh_idx, :]
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
            self.add_amount_proportionally(refresh_amount)

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


def get_price_statistics(data: pd.DataFrame):
    price_data = data[["open", "close", "high", "low"]]
    row_price_means = price_data.values.mean(axis=1)

    date_deltas = (
        data["start_time"] - data["start_time"][0]
    )  # TODO: is resolution always milliseconds?
    stacked_dates = np.tile(date_deltas.astype("int64"), 4)
    stacked_prices = price_data.values.flatten()
    price_std = stacked_prices.std()
    price_mean = stacked_prices.mean()
    stacked_prices_perc = (stacked_prices - stacked_prices[0]) / stacked_prices[0]
    price_rel_std = stacked_prices_perc.std()

    regression = scipy.stats.linregress(stacked_dates, stacked_prices)
    price_slope = regression.slope * 1e3 * 86400  # milliseconds to days
    regression_perc = scipy.stats.linregress(stacked_dates, stacked_prices_perc)
    price_slope_ppd = regression_perc.slope * 1e3 * 86400 * 100  # in % per day
    final_over_start_price = data["close"].values[-1] - data["open"].values[0]
    return (
        price_mean,
        price_slope,
        price_slope_ppd,
        final_over_start_price,
        price_std,
        price_rel_std,
    )


def buyback_overview(result: pd.DataFrame, data: pd.DataFrame) -> pa.RecordBatch:
    metadata = decode_metadata(result.schema.metadata)
    ratios = metadata["ratios"]
    discounts = metadata["discounts"]

    result = result.to_pandas()
    identifiers = result["identifier"].drop_duplicates()

    id_list = []
    running_return_mean = []
    end_running_return = []
    ratio_list = []
    discount_list = []
    delay_min = []
    delay_max = []
    delay_mean = []
    end_discount_running_return = []
    end_n_discount_buybacks = []
    end_n_discount_refresh = []
    end_n_buybacks = []
    end_n_refresh = []

    (
        price_mean,
        price_slope,
        price_slope_ppd,
        final_over_start_price,
        price_std,
        price_rel_std,
    ) = get_price_statistics(data)

    price_means = []
    price_slopes = []
    price_slopes_ppd = []
    final_over_start_prices = []
    price_stds = []
    price_rel_stds = []
    # don't do `for (ident, ratio), subtable in result.groupby(["identifier", "ratio"]):` because we want metadata from the orders that didn't execute too
    for ident in identifiers:  # group metadata for each backtest run
        for r_idx, ratio in enumerate(ratios):
            # will have duplicates across all discounts
            id_list.append(ident)
            running_return_mean.append(result["running_return"].mean())
            end_running_return.append(result["running_return"].iloc[-1])

            # unique to each discount
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
                end_n_discount_buybacks.append(None)
                end_n_discount_refresh.append(None)

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
                end_n_discount_buybacks.append(
                    subtable["num_discount_buybacks"].values[-1]
                )
                end_n_discount_refresh.append(
                    subtable["num_discount_refresh"].values[-1]
                )

            end_n_buybacks.append(result["num_buybacks"].max())
            end_n_refresh.append(result["num_refresh"].max())

            # add price statistics
            price_means.append(price_mean)
            price_slopes.append(price_slope)
            price_slopes_ppd.append(price_slope_ppd)
            final_over_start_prices.append(final_over_start_price)
            price_stds.append(price_std)
            price_rel_stds.append(price_rel_std)

    overview = {
        "identifier": id_list,
        "ratio": ratio_list,
        "discount": discount_list,
        "delay_min": delay_min,
        "delay_max": delay_max,
        "delay_mean": delay_mean,
        "end_num_discount_buybacks": end_n_discount_buybacks,
        "end_num_discount_refresh": end_n_discount_refresh,
        "end_num_buybacks": end_n_buybacks,
        "end_num_refresh": end_n_refresh,
        "end_running_return": end_running_return,
        "end_discount_running_return": end_discount_running_return,
        "running_return_mean": running_return_mean,
        "price_mean": price_means,
        "price_slope": price_slopes,
        "price_slope_ppd": price_slopes_ppd,
        "final_over_start_price": final_over_start_prices,
        "price_std": price_stds,
        "price_rel_std": price_rel_stds,
    }
    return pa.record_batch(overview, schema=SCHEMA_OVERVIEW)


def make_settings_record(
    ratios: float | list | np.ndarray,
    discounts: float | list | np.ndarray,
    initial_allocations: float | list | np.ndarray,
    refresh_amounts: float | list | np.ndarray,
    refresh_intervals: float | list | np.ndarray,
    run_duration: timedelta | np.timedelta64,
    asset1: str,
    asset2: str,
    redistribute_on_refresh: bool,
    start_price: float,
    identifier: str | None = None,
) -> pa.RecordBatch:
    if np.isscalar(ratios):
        ratios = [float(ratios)]
    if np.isscalar(discounts):
        discounts = [float(discounts)]
    if np.isscalar(initial_allocations):
        initial_allocations = [float(initial_allocations)]
    if np.isscalar(refresh_amounts):
        refresh_amounts = [float(refresh_amounts)]
    if isinstance(refresh_intervals, (timedelta, np.timedelta64)):
        refresh_intervals = [refresh_intervals]

    if identifier is not None:
        identifier = uuid4()
    return pa.record_batch(
        {
            "identifier": [str(identifier)],
            "ratios": [ratios],
            "discounts": [discounts],
            "initial_allocations": [initial_allocations],
            "refresh_amounts": [refresh_amounts],
            "refresh_intervals": [refresh_intervals],
            "run_duration": [run_duration],
            "asset1": [asset1],
            "asset2": [asset2],
            "redistribute_on_refresh": [redistribute_on_refresh],
            "start_price": [start_price],
        },
        schema=SCHEMA_SETTINGS,
    )


def simple_buyback_sim(
    ratios: list,
    discounts: list,
    initial_allocation: float,
    refresh_amount: float,
    refresh_interval_days: int,
    sim_len_days: int,
    step_days: int,
    sim_start_price: float | None = None,
    redistribute_on_refresh: bool = False,
    invert_pair: bool = False,
    save_to_db: bool = False,
):
    run_window = timedelta(days=sim_len_days)  # 4 month windows
    step_size = timedelta(days=step_days)
    refresh_interval = timedelta(days=refresh_interval_days)
    db_path = Path.cwd() / "buyback_rec/database"
    candles_path = db_path / "candlestick_data"
    id_path = db_path / "sim_ids"
    overviews_path = db_path / "overviews"
    records_path = db_path / "sim_records"
    candles = ds.dataset(candles_path)
    df = (
        candles.to_table()
        .to_pandas()
        .sort_values(by=["asset1", "asset2", "start_time"])
    )
    if invert_pair:
        df.loc[:, ["low", "high", "open", "close"]] = (
            1 / df.loc[:, ["high", "low", "open", "close"]].values  # swap high/low
        )
    pairs = df[["asset1", "asset2"]].drop_duplicates().values

    data = []
    settings = []
    results = []
    overviews = []
    for asset1, asset2 in pairs:
        in_pair = (df["asset1"] == asset1) & (df["asset2"] == asset2)
        data.append(
            df[in_pair].copy().sort_values(by=["start_time"]).reset_index(drop=True)
        )

    for asset_pair in data:
        break_indicies = get_breakpoints(
            timestamps=asset_pair.start_time,
            window_time=run_window,
            step_time=step_size,
        )

        for (
            start,
            stop,
        ) in break_indicies:  # simulate a buyback startegy over each period
            identifier = uuid4()
            buyback = Buyback(
                identifier=identifier,
                ratios=ratios,
                discounts=discounts,
                amount_allocated=initial_allocation,
            )
            window_data = asset_pair.loc[start:stop, :].copy().reset_index(drop=True)
            if sim_start_price is not None:
                scale_factor = sim_start_price / window_data["open"].iloc[0]
                window_data[["low", "high", "open", "close"]] = (
                    window_data[["low", "high", "open", "close"]] * scale_factor
                )

            start_price = window_data["open"].iloc[0]
            settings_record = make_settings_record(
                ratios=ratios,
                discounts=discounts,
                initial_allocations=initial_allocation,
                refresh_amounts=refresh_amount,
                refresh_intervals=refresh_interval,
                run_duration=run_window,
                asset1=asset_pair["asset1"].iloc[0],
                asset2=asset_pair["asset2"].iloc[0],
                redistribute_on_refresh=redistribute_on_refresh,
                identifier=identifier,
                start_price=start_price,
            )
            results.append(
                buyback.simulate_buybacks(
                    window_data,
                    refresh_amounts=refresh_amount,
                    refresh_intervals=refresh_interval,
                    redistribute_on_refresh=redistribute_on_refresh,
                )
            )

            settings.append(settings_record)
            overview = buyback_overview(result=results[-1], data=window_data)
            overviews.append(overview)

    results = pa.concat_tables(results)
    settings = pa.Table.from_batches(settings)
    overviews = pa.Table.from_batches(overviews)

    if save_to_db:
        pq.write_to_dataset(table=results, root_path=records_path)
        pq.write_to_dataset(table=overviews, root_path=overviews_path)
        pq.write_to_dataset(table=settings, root_path=id_path)

    return results, settings, overviews


if __name__ == "__main__":
    results, settings, overviews = simple_buyback_sim(
        ratios=[0.4, 0.3, 0.2, 0.1],
        discounts=[0, 23.6, 38.2, 61.8],
        initial_allocation=100_000,
        refresh_amount=10_000,
        refresh_interval_days=5,
        sim_len_days=120,
        step_days=5,
        redistribute_on_refresh=True,
        save_to_db=True,
        sim_start_price=1,
        invert_pair=False,
    )

    print()
