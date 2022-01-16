from typing import Any

from injector import singleton

from models.pair import Pair

QuotePairJSON = dict[str, any]


@singleton
class PairFactory:
    def build_pair_from_dict(self, symbol_info: dict[str, Any]):
        return Pair(
            symbol=symbol_info.get("symbol") or symbol_info.get("instrument_name").replace("_", ""),
            base_asset=symbol_info.get("baseAsset") or symbol_info.get("base_currency"),
            quote_asset=symbol_info.get("quoteAsset") or symbol_info.get("quote_currency"),
            order_types=symbol_info.get("orderTypes"),
        )
