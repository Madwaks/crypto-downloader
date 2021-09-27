import os
from pathlib import Path
from typing import Type, Optional
from typing import TypeVar

from injector import Injector, Binder

T = TypeVar("T")


_injector: Optional[Injector] = None
data_folder = Path(os.getenv("CRYPTO_QUOTES_FOLDER", "data/"))


def _configure_crypto_quots(binder: Binder):
    from services.repositories.quotes import QuotesRepository

    binder.bind(
        QuotesRepository.Configuration,
        QuotesRepository.Configuration(file_folder_path=data_folder),
    )

    from services.importers.quotes import QuotesImporter

    binder.bind(
        QuotesImporter.Configuration,
        QuotesImporter.Configuration(file_folder_path=data_folder),
    )


def _configure_crypto_pairs(binder: Binder):
    from services.repositories.pair import PairsRepository

    binder.bind(
        PairsRepository.Configuration,
        PairsRepository.Configuration(file_folder_path=data_folder),
    )

    from services.importers.pairs_importer import PairsImporter

    binder.bind(
        PairsImporter.Configuration,
        PairsImporter.Configuration(file_folder_path=data_folder),
    )


def _configure(binder: Binder):
    _configure_crypto_quots(binder)
    _configure_crypto_pairs(binder)


def _create_injector():
    global _injector
    if _injector is None:
        _injector = Injector(_configure)


def provide(clazz: Type[T]) -> T:
    _create_injector()

    return _injector.get(clazz)
