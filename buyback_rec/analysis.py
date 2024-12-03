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


plt.style.use("dark_background")


def load_datasets():
    db_path = Path.cwd() / "buyback_rec/database"
    id_path = db_path / "sim_ids"
    overviews_path = db_path / "overviews"
    records_path = db_path / "sim_records"

    ids = ds.dataset(id_path, format="parquet")
    overviews = ds.dataset(overviews_path, format="parquet")
    records = ds.dataset(records_path, format="parquet")

    return ids, overviews, records


if __name__ == "__main__":
    ids, overviews, records = load_datasets()
    ov_df = overviews.to_table().to_pandas()
    r_df = records.to_table().to_pandas()

    ends = r_df.sort_values(
        by=["identifier", "running_allocated"], ascending=[False, False]
    ).drop_duplicates(subset=["identifier", "discount"])
    print(
        ends[
            [
                "identifier",
                "ratio",
                "discount",
                "running_allocated",
                "running_purchased",
            ]
        ]
    )

    ends.plot(x="remaining_amount", y="running_return", kind="scatter")
    plt.show()
    # ov_df.plot(x="end_num_buybacks", y="end_running_return", kind="scatter")
    # plt.show()

    # ov_df.plot(x="end_num_buybacks", y="running_return_mean", kind="scatter")
    # plt.show()

    # ov_df.plot(x="discount", y="end_discount_running_return", kind="scatter")
    # plt.show()
