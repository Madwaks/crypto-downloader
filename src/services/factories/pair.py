from typing import Any

from injector import singleton

from models.pair import Pair

QuotePairJSON = dict[str, any]


@singleton
class PairFactory:
    def build_pair_from_dict(self, symbol_info: dict[str, Any]):
        return Pair(
            symbol=symbol_info.get("symbol"),
            base_asset=symbol_info.get("baseAsset"),
            quote_asset=symbol_info.get("quoteAsset"),
            order_types=symbol_info.get("orderTypes"),
        )
