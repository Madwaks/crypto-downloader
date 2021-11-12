from typing import NoReturn, Union

from injector import singleton, inject

from models.enums import TimeUnits
from models.pair import Pair
from services.importers.quotes import QuotesImporter
from services.repositories.pair import PairsRepository


@singleton
class QuotesPairStorer:
    @inject
    def __init__(
        self, quotes_importer: QuotesImporter, pair_repository: PairsRepository
    ):
        self._pair_repository = pair_repository
        self._quote_importer = quotes_importer

    def store_all_quotes(self, time_unit: TimeUnits):
        available_pair = self._pair_repository.get_available_pairs()
        for pair in available_pair:
            self.store_quotes_for_pair(pair, time_unit)

    def store_quotes_for_pair(
        self, pair: Union[Pair, str], time_unit: TimeUnits
    ) -> NoReturn:
        if isinstance(pair, str):
            pair = self._pair_repository.get_pair_from_symbol(pair)

        objs = self._quote_importer.import_quotes(pair, time_unit=time_unit)
        print(
            f"Successfully load {len(objs)} quotes in {self._quote_importer.json_folder.absolute()}"
        )
