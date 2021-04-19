import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from injector import singleton, inject

from models.pair import Pair
from services.client import BinanceClient
from services.factories.pair import PairFactory

logger = logging.getLogger("django")


@singleton
class PairsImporter:
    @dataclass
    class Configuration:
        file_folder_path: Path

    @inject
    def __init__(
        self, config: Configuration, client: BinanceClient, pair_factory: PairFactory
    ):
        self._client = client
        self._pair_factory = pair_factory
        self._config = config

    @property
    def pair_file_path(self):
        return self._config.file_folder_path / "available_pairs.json"

    def import_all_pairs(self) -> list[Pair]:
        data = self._client.get_exchange_info()
        symbols = data["symbols"]
        pairs = [self._build_pair(symbol_info).to_dict() for symbol_info in symbols]
        self.pair_file_path.write_text(json.dumps(pairs, indent=4))
        return pairs

    def _build_pair(self, symbol_info: dict[str, Any]):
        return self._pair_factory.build_pair_from_dict(symbol_info)
