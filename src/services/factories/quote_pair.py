from injector import inject, singleton

from models.enums import TimeUnits
from models.pair import Pair
from models.quotes import Quotes

QuotePairJSON = dict[str, any]


@singleton
class QuotesFactory:
    @inject
    def __init__(self):
        pass

    def build_quote_from_pair(
        self, pair: Pair, time_unit: TimeUnits, objs: list[QuotePairJSON]
    ) -> list[Quotes]:
        return [
            Quotes(
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
