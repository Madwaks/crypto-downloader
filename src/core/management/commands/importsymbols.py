import os
import sys

from core.management import BaseCommand


class Command(BaseCommand):
    help = "Download symbolfiles"

    def handle(self, *args, **options):
        sys.path.insert(0, os.getcwd())

        from services.importers.pairs_importer import PairsImporter
        from utils.service_provider import provide

        pair_importer = provide(PairsImporter)

        pair_importer.import_all_pairs()
