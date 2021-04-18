import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from injector import singleton, inject

from models.enums import TimeUnits
from models.pair import Pair
from services.factories.quote_pair import QuotesFactory


@singleton
class QuotesRepository:
    @dataclass
    class Configuration:
        file_folder_path: Path

    @inject
    def __init__(
        self, quote_pair_factory: QuotesFactory, configuration: Configuration
    ):
        self._config = configuration
        self._quote_pair_factory = quote_pair_factory

    @property
    def json_folder(self) -> Path:
        return self._config.file_folder_path / "json"

    @property
    def csv_folder(self) -> Path:
        return self._config.file_folder_path / "csv"

    @property
    def available_tu(self) -> list[TimeUnits]:
        return [
            TimeUnits.from_code(file_name.name.split("-")[1])
            for file_name in self.json_folder.iterdir()
        ]

    @property
    def available_pair(self) -> list[str]:
        return [
            file_name.name.split("-")[0] for file_name in self.json_folder.iterdir()
        ]

    def get_pair_quotes(self, pair: Pair, time_unit: TimeUnits) -> list[dict[str, Any]]:
        path_to_file = self._get_file_from_pair_and_tu(pair, time_unit)
        objs = json.loads(path_to_file.read_text())
        return objs

    def get_csv_name_for_pair(self, pair: Pair, time_unit: TimeUnits) -> Path:
        file_name = f"{pair.symbol}-{time_unit.value}-data"
        return self.csv_folder / f"{file_name}.csv"

    def get_json_name_for_pair(self, pair: Pair, time_unit: TimeUnits) -> Path:
        file_name = f"{pair.symbol}-{time_unit.value}-data"
        return self.json_folder / f"{file_name}.json"

    def _get_file_from_pair_and_tu(self, pair: Pair, time_unit: TimeUnits) -> Path:
        return self.json_folder / f"{pair.symbol}-{time_unit.value}-data.json"
