import logging
from pathlib import Path
from typing import Any, Optional

from injector import singleton, inject
from pandas import DataFrame

from core.services.factories.company import CompanyFactory
from core.services.factories.quote import QuoteFactory
from crypto.models.pair import Pair
from crypto.services.client import BinanceClient
from crypto.services.repositories.quote_pair import QuotesPairRepository
from crypto.utils.enums import TimeUnits
from crypto.utils.etc import _retrieve_existing_data

logger = logging.getLogger("django")


@singleton
class PairsImporter:
    @inject
    def __init__(self, client: BinanceClient, company_factory: CompanyFactory):
        self._client = client
        self._company_factory = company_factory

    def import_all_pairs(self):
        data = self._client.get_exchange_info()
        symbols = data["symbols"]
        pairs = [self._build_pair(symbol_info) for symbol_info in symbols]
        self._save_pairs(pairs)

    def _build_pair(self, symbol_info: dict[str, Any]):
        return Pair(
            symbol=symbol_info.get("symbol"),
            base_asset=symbol_info.get("baseAsset"),
            quote_asset=symbol_info.get("quoteAsset"),
            order_types=symbol_info.get("orderTypes"),
        )

    def _save_pairs(self, list_pairs: list[Pair]):
        for pair in list_pairs:
            if not pair.pk:
                pair.save()


@singleton
class QuotesPairImporter:
    @inject
    def __init__(
        self,
        quote_factory: QuoteFactory,
        client: BinanceClient,
        quotes_repository: QuotesPairRepository,
    ):
        self._quote_factory = quote_factory
        self._client = client
        self._quotes_repo = quotes_repository

    def import_all_quotes(self, time_unit: str):
        for pair in Pair.objects.all()[:2]:
            self.import_quotes(pair, TimeUnits.from_code(time_unit))

    def import_quotes(self, pair: Pair, time_unit: TimeUnits):
        csv_file = self._quotes_repo.get_csv_name_for_pair(pair, time_unit)
        json_file = self._quotes_repo.get_json_name_for_pair(pair, time_unit)
        existing_data = _retrieve_existing_data(csv_file)

        data = self._client.get_needed_pair_quotes(pair, time_unit, existing_data)
        if data:
            new_data = self._merge_missing_data(data, existing_data)
            self._save_data_if_needed(new_data, csv_file, json_file)

        logger.info(f"[JSON] {pair.symbol} // {time_unit.value} succeed ")

    def _build_files(self, pair: Pair, time_unit: TimeUnits):
        file_name = f"{pair.symbol}-{time_unit.value}-data"
        filename_csv = self._quotes_repo.csv_folder / f"{file_name}.csv"
        filename_json = self._quotes_repo.json_folder / f"{file_name}.json"
        return filename_csv, filename_json

    def _save_data_if_needed(
        self, new_data: DataFrame, file_name_csv: Path, filename_json: Path
    ):
        if new_data:
            self._save_csv(new_data, file_name_csv)
            self._save_json(filename_json, new_data)

    def _save_csv(self, new_data: DataFrame, file_name: Path):
        new_data.to_csv(file_name, index=False)

    def _save_json(self, file_name_json: Path, new_data: DataFrame):
        file_name_json.write_text(new_data.to_json(orient="records", indent=4))

    def _merge_missing_data(
        self, new_data: DataFrame, existing_data: Optional[DataFrame]
    ):
        if len(existing_data) > 0 and len(new_data) > 0:
            return existing_data.append(new_data)
