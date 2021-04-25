from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import DataClassJsonMixin
from dataclasses_json.core import Json

from models.pair import Pair
from models.enums import TimeUnits


@dataclass
class Quote(DataClassJsonMixin):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: str
    pair: Pair = field(default_factory=Pair)
    time_unit: Optional[TimeUnits] = field(default_factory=TimeUnits)

    def to_dict(self, encode_json=False) -> dict[str, Json]:
        asdict = super(Quote, self).to_dict()
        asdict["time_unit"] = self.time_unit.value
        return asdict
