from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Pair(DataClassJsonMixin):
    symbol: str
    base_asset: str
    quote_asset: str
    order_types: Optional[list[str]] = field(default_factory=list)

    def __str__(self) -> str:
        return self.symbol
