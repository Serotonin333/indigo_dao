import pyarrow as pa

candle = [
    ("asset1", pa.string()),
    ("asset2", pa.string()),
    ("start_time", pa.timestamp("s")),
    ("low", pa.float32()),
    ("high", pa.float32()),
    ("open", pa.float32()),
    ("close", pa.float32()),
    ("volume", pa.float32()),
]


buyback = [
    ("identifier", pa.string()),  # identifier for the buyback run
    ("start_time", pa.timestamp("s")),
    ("last_reset_time", pa.timestamp("s")),
    ("trigger_time", pa.timestamp("s")),
    ("amount", pa.float32()),
    ("price", pa.float32()),
    ("purchased", pa.float32()),
    ("ref_price", pa.float32()),  # price that the `discount` is referenced against
    (
        "ratio",
        pa.float32(),
    ),  # percentage of the current allocation that was distributed to this `discount`
    (
        "discount",
        pa.float32(),
    ),  # discount from the `ref_price` where a limit order is placed
    ("start_price", pa.float32()),  # starting price of the simulation
    ("running_allocated", pa.float32()),  # running amount allocated
    ("running_spent", pa.float32()),
    ("running_purchased", pa.float32()),
    ("running_return", pa.float32()),
    ("remaining_amount", pa.float32()),
    ("num_discount_buybacks", pa.int32()),
    ("num_discount_refresh", pa.int32()),
    ("num_buybacks", pa.int32()),
    ("num_refresh", pa.int32()),
]

overview = [
    ("identifier", pa.string()),  # identifier for the buyback run
    (
        "ratio",
        pa.float32(),
    ),  # ratio of the amount allocated distributed to this "discount"
    (
        "discount",
        pa.float32(),
    ),  # discount from the current market price at which a limit order is placed
    (
        "delay_min",
        pa.duration("s"),
    ),  # minimum duration from when a limit order was placed at this discount to when it was filled
    (
        "delay_max",
        pa.duration("s"),
    ),  # maximum duration from when a limit order was placed at this discount to when it was filled, NaT if it was never filled
    (
        "delay_mean",
        pa.duration("s"),
    ),  # average duration from when a limit order was placed at this discount to when it was filled
    (
        "end_num_discount_buybacks",
        pa.int32(),
    ),  # number of buybacks that occurred during this simulation at this `discount``
    (
        "end_num_discount_refresh",
        pa.int32(),
    ),  # number of times that new funds were allocated to this `discount` during the simulation
    (
        "end_num_buybacks",
        pa.int32(),
    ),  # total number of buybacks that occurred across all `discount`s during this simulation
    (
        "end_num_refresh",
        pa.int32(),
    ),  # total number of time a set of new funds were allocated across all `discount`s during this simulation
    (
        "end_running_return",
        pa.float32(),
    ),  # value of all funds held vs value of all funds deployed at the end of the simulation (TODO: check exact implementation)
    (
        "end_discount_running_return",
        pa.float32(),
    ),  # value of funds purchased at this `discount` vs value of funds deployed to this `discount` level at the end of the simulation (TODO: check exact implementation
    ("running_return_mean", pa.float32()),  # average return throughout the simulation
    ("price_mean", pa.float32()),  # average price throughout the simulation
    (
        "price_slope",
        pa.float32(),
    ),  # slope of the linear fit of the price in price per day
    (
        "price_slope_ppd",
        pa.float32(),
    ),  # slope of the linear fit of the price in percentage price change per day
    (
        "final_over_start_price",
        pa.float32(),
    ),  # simulation ending price / starting price
    (
        "price_std",
        pa.float32(),
    ),  # standard deviation of the price within the simulation
    (
        "price_rel_std",
        pa.float32(),
    ),  # relative standard deviation of the price within the simulation
]

settings = [
    ("identifier", pa.string()),  # identifier for the buyback run
    (
        "ratios",
        pa.list_(pa.float32()),
    ),  # ratio of the amount allocated distributed to this "discount"
    (
        "discounts",
        pa.list_(pa.float32()),
    ),  # discount from the current market price at which a limit order is placed
    (
        "initial_allocations",
        pa.list_(pa.float32()),
    ),  # starting allocation for this buyback run
    (
        "refresh_amounts",
        pa.list_(pa.float32()),
    ),  # amount added to the buybacks fund at each interval
    (
        "refresh_intervals",
        pa.list_(pa.duration("s")),
    ),  # interval from the last time an amount was "refreshed" to the next refresh
    ("run_duration", pa.duration("s")),  # full duration of the buyback similation
    ("asset1", pa.string()),  # asset 1 for the buyback simulation
    ("asset2", pa.string()),  # asset 2 for the buyback simulation
    (
        "redistribute_on_refresh",
        pa.bool_(),
    ),  # flag that, if True, closes the current open limit orders amd redistributes those funds across all buybacks according to the `ratio`s upon refresh
    ("start_price", pa.float32()),  # asset1:asset2 price at the start of the simulation
]


SCHEMA_CANDLE = pa.schema(candle)
SCHEMA_BUYBACK = pa.schema(buyback)
SCHEMA_OVERVIEW = pa.schema(overview)
SCHEMA_SETTINGS = pa.schema(settings)

if __name__ == "__main__":
    print(SCHEMA_BUYBACK)
    print(SCHEMA_SETTINGS)
