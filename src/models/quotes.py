from dataclasses import dataclass, field
from typing import Optional

from models.pair import Pair
from src.models.enums import TimeUnits


@dataclass
class Quotes:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    pair: Pair = field(default_factory=Pair)
    quote_av: Optional[float] = None
    trades: Optional[int] = None
    tb_base_av: Optional[float] = None
    tb_quote_av: Optional[float] = None
    time_unit: Optional[TimeUnits] = field(default_factory=TimeUnits)
