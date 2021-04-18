from injector import singleton, inject

from models.enums import TimeUnits
from models.pair import Pair
from services.factories.quote_pair import QuotesFactory
from services.repositories.quote_pair import QuotesRepository


@singleton
class QuotesPairStorer:
    @inject
    def __init__(
        self, quotes_repository: QuotesRepository, quote_factory: QuotesFactory
    ):
        self._quote_factory = quote_factory
        self._quotes_repository = quotes_repository

    def store_all_quotes(self, time_unit: TimeUnits):
        availale_pair = self._quotes_repository.available_pair
        breakpoint()
        for pair_symbol in availale_pair:
            pair = Pair.objects.get(symbol=pair_symbol)
            self._store_quotes_for_pair_and_tu(pair, time_unit)

    def _store_quotes_for_pair_and_tu(self, pair: Pair, time_unit: TimeUnits):
        objs = self._quotes_repository.get_pair_quotes(pair, time_unit=time_unit)
        quotes = self._quote_factory.build_quote_from_pair(
            pair, time_unit=time_unit, objs=objs
        )
        for quote in quotes:
            quote.save()
        print(f"Successfully load {len(quotes)} quotes")
