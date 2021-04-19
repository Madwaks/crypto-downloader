import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from injector import singleton, inject

from models.enums import TimeUnits
from models.pair import Pair
from services.importers.quotes import QuotesImporter


@singleton
class QuotesRepository:
    @dataclass
    class Configuration:
        file_folder_path: Path

    @inject
    def __init__(self, configuration: Configuration, quote_importer: QuotesImporter):
        self._config = configuration
        self._quote_importer = quote_importer

    @property
    def available_tu(self) -> list[TimeUnits]:
        return [
            TimeUnits.from_code(file_name.name.split("-")[1])
            for file_name in self.json_folder.iterdir()
        ]

    def get_pair_quotes(self, pair: Pair, time_unit: TimeUnits) -> list[dict[str, Any]]:
        path_to_file = self._quote_importer.get_json_name_for_pair(pair, time_unit)
        if path_to_file.exists():
            return json.loads(path_to_file.read_text())
        return self._quote_importer.import_quotes(pair, time_unit)
