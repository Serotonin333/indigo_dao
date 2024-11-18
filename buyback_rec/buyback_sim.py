import numpy as np
from scipy.stats import norm
from dataclasses import dataclass
import pandas as pd
import http.client
import json
from itertools import accumulate
from matplotlib import pyplot as plt
from scipy.stats import gamma
from datetime import datetime

plt.style.use("dark_background")


@dataclass
class Buyback:
    ref_price: float
    ratios: list[float]
    discounts: list[float]

if __name__=="__main__":
    pass