import os
import sys

from core.management import BaseCommand


class Command(BaseCommand):
    help = "Loads initial companies into DB"

    @property
    def choices(self) -> list[str]:
        return ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--time-unit", choices=self.choices, type=str, required=True
        )
        parser.add_argument("--pair", type=str, required=False)

    def handle(self, *args, **options):
        sys.path.insert(0, os.getcwd())

        from src.services.quotes_storer import QuotesPairStorer
        from src.models.enums import TimeUnits
        from utils.service_provider import provide

        pair = options["pair"]
        tu = TimeUnits.from_code(options["time_unit"])
        quotes_storer = provide(QuotesPairStorer)
        if not pair:
            quotes_storer.store_all_quotes(time_unit=tu)
        else:
            quotes_storer.store_quotes_for_pair(pair, time_unit=tu)
