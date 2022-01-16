import math
import os
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from time import sleep
from typing import Any

from injector import inject
import requests
from binance.client import Client
from injector import singleton
from pandas import to_datetime, DataFrame

from models.enums import TimeUnits
from models.pair import Pair

logger = getLogger("django")

@singleton
class CryptoComClient:
    BASE_URL = "https://api.crypto.com/v2/public"

    @dataclass
    class Configuration:
        api_key: str = os.getenv("CRYPTOCOM_API_KEY")
        api_secret: str = os.getenv("CRYPTOCOM_API_SECRET")

    @inject
    def __init__(self, config: Configuration):
        self._config = config

    def get_available_instruments(self):
        req = requests.get(f"{self.BASE_URL}/get-instruments")
        return req.json().get("result")

@singleton
class BinanceClient(Client):
    @dataclass
    class Configuration:
        api_key: str = os.getenv("BINANCE_API_KEY")
        api_secret: str = os.getenv("BINANCE_API_SECRET")

    PUBLIC_API_VERSION = "v3"

    @inject
    def __init__(self, config: Configuration):
        self._config = config

        super(BinanceClient, self).__init__(
            api_key=self._config.api_key, api_secret=self._config.api_secret
        )

    def get_needed_pair_quotes(
        self, pair: Pair, time_unit: "TimeUnits", existing_data: DataFrame
    ):
        oldest_point, newest_point = self._get_minutes_of_new_data(
            pair.symbol, time_unit.value, existing_data
        )
        delta_min = (newest_point - oldest_point).total_seconds() / 60
        available_data = math.ceil(delta_min / time_unit.binsize)
        logger.info(
            f"Downloading {delta_min} minutes of new data available for {pair.symbol}, i.e. {available_data} instances of {time_unit.value} data."
        )
        if delta_min < 1:
            return
        klines = self.get_historical_klines(
            pair.symbol,
            time_unit.value,
            oldest_point.strftime("%d %b %Y %H:%M:%S"),
            newest_point.strftime("%d %b %Y %H:%M:%S"),
        )
        return self._build_dataframe(klines)

    def _build_dataframe(self, klines: list[dict[str, Any]]):
        data = DataFrame(
            klines,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_av",
                "trades",
                "tb_base_av",
                "tb_quote_av",
                "ignore",
            ],
        )
        return data

    def _get_minutes_of_new_data(
        self, symbol: str, time_unit: "TimeUnits", data: DataFrame
    ):
        if len(data) > 0:
            old = datetime.fromtimestamp(data["timestamp"].iloc[-1] / 1000)
        else:
            old = datetime.strptime("1 Jan 2017", "%d %b %Y")
        new = to_datetime(
            self.get_klines(symbol=symbol, interval=time_unit)[-1][0], unit="ms"
        )
        sleep(0.5)
        return old, new
