import json
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Optional

from injector import singleton, inject
from pandas import DataFrame, read_csv

from models.enums import TimeUnits
from models.pair import Pair
from models.quote import Quote
from services.client import BinanceClient
from services.factories.quote_pair import QuotesFactory

from utils.etc import create_folder_and_parents

logger = getLogger()


@singleton
class QuotesImporter:
    @dataclass
    class Configuration:
        file_folder_path: Path

    @inject
    def __init__(
        self,
        configuration: Configuration,
        quote_factory: QuotesFactory,
        client: BinanceClient,
    ):
        self._config = configuration
        self._quote_factory = quote_factory
        self._client = client

        create_folder_and_parents(self.json_folder)
        create_folder_and_parents(self.csv_folder)

    @property
    def json_folder(self) -> Path:
        return self._config.file_folder_path / "json"

    @property
    def csv_folder(self) -> Path:
        return self._config.file_folder_path / "csv"

    def import_quotes(self, pair: Pair, time_unit: TimeUnits) -> list[Quote]:
        csv_file = self.get_csv_name_for_pair(pair, time_unit)
        json_file = self.get_json_name_for_pair(pair, time_unit)
        existing_data = self._retrieve_existing_data(csv_file)
        data = self._client.get_needed_pair_quotes(pair, time_unit, existing_data)

        if data is not None:
            new_data = self._merge_missing_data(data, existing_data)
            self._save_csv(data, csv_file)
        else:
            new_data = existing_data
        new_data.drop_duplicates(["timestamp"], inplace=True)
        quotes = self._quote_factory.build_from_dataframe(new_data, pair, time_unit)
        self._save_json(json_file, quotes)
        logger.info(f"[JSON] {pair.symbol} // {time_unit.value} succeed ")
        return quotes

    def _build_files(self, pair: Pair, time_unit: TimeUnits):
        file_name = f"{pair.symbol}-{time_unit.value}-data"
        filename_csv = self._quotes_repo.csv_folder / f"{file_name}.csv"
        filename_json = self._quotes_repo.json_folder / f"{file_name}.json"
        return filename_csv, filename_json

    def _save_csv(self, new_data: DataFrame, file_name: Path):
        new_data.to_csv(file_name, index=False)

    def _save_json(self, file_name_json: Path, list_quotes: list[Quote]):
        existing_quotes = (
            json.loads(file_name_json.read_text()) if file_name_json.exists() else []
        )
        existing_quotes_ts = [quote.get("timestamp") for quote in existing_quotes]

        file_name_json.write_text(
            json.dumps(
                [
                    quote.to_dict()
                    for quote in list_quotes
                    if quote.timestamp not in existing_quotes_ts
                ]
                + existing_quotes,
                indent=4,
            )
        )

    def _merge_missing_data(
        self, new_data: DataFrame, existing_data: Optional[DataFrame]
    ):
        if len(existing_data) > 0 and len(new_data) > 0:
            return existing_data.append(new_data)
        return new_data

    @staticmethod
    def _retrieve_existing_data(file_path: Path) -> DataFrame:
        if file_path.exists():
            data_df = read_csv(file_path)
        else:
            data_df = DataFrame()
        return data_df

    def get_csv_name_for_pair(self, pair: Pair, time_unit: TimeUnits) -> Path:
        file_name = f"{pair.symbol}-{time_unit.value}-data"
        return self.csv_folder / f"{file_name}.csv"

    def get_json_name_for_pair(self, pair: Pair, time_unit: TimeUnits) -> Path:
        file_name = f"{pair.symbol}-{time_unit.value}-data"
        return self.json_folder / f"{file_name}.json"
