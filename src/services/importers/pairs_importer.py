import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from injector import singleton, inject

from models.pair import Pair
from services.client import BinanceClient
from services.factories.pair import PairFactory
from utils.etc import create_folder_and_parents

logger = logging.getLogger("")


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
        create_folder_and_parents(self._config.file_folder_path)

    @property
    def pair_file_path(self):
        return self._config.file_folder_path / "available_pairs.json"

    def import_all_pairs(self) -> list[Pair]:
        data = self._client.get_exchange_info()
        symbols = data["symbols"]

        pairs = [self._build_pair(symbol_info) for symbol_info in symbols]
        if not self.pair_file_path.exists():
            self.pair_file_path.touch()

        self.pair_file_path.write_text(
            json.dumps([pair.to_dict() for pair in pairs], indent=4)
        )

        print(f"Successfully downloaded {len(pairs)} at {self.pair_file_path.absolute()}.")

        return pairs

    def _build_pair(self, symbol_info: dict[str, Any]):
        return self._pair_factory.build_pair_from_dict(symbol_info)
