import json
from dataclasses import dataclass
from pathlib import Path

from injector import singleton, inject

from models.pair import Pair
from services.importers.pairs_importer import PairsImporter


@singleton
class PairsRepository:
    @dataclass
    class Configuration:
        file_folder_path: Path

    @inject
    def __init__(self, configuration: Configuration, pair_importer: PairsImporter):
        self._config = configuration
        self._pair_importer = pair_importer

    @property
    def pair_file_path(self):
        return self._config.file_folder_path / "available_pairs.json"

    def get_available_pairs(self) -> list[Pair]:
        stored_pairs = json.loads(self.pair_file_path.read_text())
        if stored_pairs:
            return [Pair.from_dict(val) for val in stored_pairs]
        else:
            return self._pair_importer.import_all_pairs()

    def get_pair_from_symbol(self, pair_symbol: str):
        return [
            pair for pair in self.get_available_pairs() if pair.symbol == pair_symbol
        ][0]
