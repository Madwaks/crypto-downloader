from injector import singleton
from pandas import DataFrame, Series
from typing import Union
from models.enums import TimeUnits
from models.pair import Pair
from models.quote import Quote

QuotePairJSON = dict[str, any]


@singleton
class QuotesFactory:
    def build_from_dataframe(
        self, data: DataFrame, pair: Pair, time_unit: TimeUnits
    ) -> list[Quote]:
        return data.apply(
            lambda row: self.build_quote_from_dict(row, pair, time_unit), axis=1
        ).to_list()

    def build_quote_from_pair(
        self, pair: Pair, time_unit: TimeUnits, objs: list[QuotePairJSON]
    ) -> list[Quote]:
        return [self.build_quote_from_dict(obj) for obj in objs]

    def build_quote_from_dict(
        self, row: Union[Series, dict], pair: Pair, time_unit: TimeUnits
    ) -> Quote:
        return Quote(
            timestamp=self.format_timestamp(row.get("timestamp")),
            open=float(row.get("open")),
            close=float(row.get("close")),
            high=float(row.get("high")),
            low=float(row.get("low")),
            volume=float(row.get("volume")),
            close_time=self.format_timestamp(row.get("close_time")),
            pair=pair,
            time_unit=time_unit,
        )

    @staticmethod
    def format_timestamp(timestamp: str):
        return str(timestamp).split(".")[0]
