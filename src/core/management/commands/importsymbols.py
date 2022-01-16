import os
import sys

from core.management import BaseCommand


class Command(BaseCommand):
    help = "Download symbolfiles"

    @property
    def choices(self):
        return ["binance", "cryptocom"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--provider", choices=self.choices, type=str, nargs="?", const="cryptocom"
        )

    def handle(self, *args, **options):
        sys.path.insert(0, os.getcwd())

        from services.importers.pairs_importer import PairsImporter
        from services.client import BinanceClient
        from services.client import CryptoComClient
        from utils.service_provider import build

        service_mapping = {"binance": BinanceClient, "cryptocom": CryptoComClient}
        pair_importer = build(PairsImporter, client=build(service_mapping.get(options["provider"])))

        pair_importer.import_all_pairs()
