from injector import singleton
from pandas import DataFrame, Series

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
            lambda row: self._build_quote_from_row(row, pair, time_unit), axis=1
        ).to_list()

    @staticmethod
    def _build_quote_from_row(row: Series, pair: Pair, time_unit: TimeUnits):
        return Quote(
            timestamp=row.get("timestamp"),
            open=row.get("open"),
            close=row.get("close"),
            high=row.get("high"),
            low=row.get("low"),
            volume=float(row.get("volume")),
            close_time=row.get("close_time"),
            pair=pair,
            time_unit=time_unit,
        )

    def build_quote_from_pair(
        self, pair: Pair, time_unit: TimeUnits, objs: list[QuotePairJSON]
    ) -> list[Quote]:
        return [
            Quote(
                timestamp=obj.get("timestamp"),
                open=obj.get("open"),
                close=obj.get("close"),
                high=obj.get("high"),
                low=obj.get("low"),
                volume=float(obj.get("volume")),
                close_time=obj.get("close_time"),
                pair=pair,
                time_unit=time_unit,
            )
            for obj in objs
        ]
