import os
from typing import Type, Optional
from typing import TypeVar

from injector import Injector, Binder
from conf import settings, LazySettings

T = TypeVar("T")


_injector: Optional[Injector] = None


def _configure_crypto_quots(binder: Binder, settings: LazySettings):
    from services.repositories.quote_pair import QuotesRepository
    from pathlib import Path
    binder.bind(
        QuotesRepository.Configuration,
        QuotesRepository.Configuration(
            file_folder_path=Path(os.getenv("CRYPTO_QUOTES_FOLDER", "data/"))
        ),
    )


def _configure(binder: Binder):
    _configure_crypto_quots(binder, settings)


def _create_injector():
    global _injector
    if _injector is None:
        _injector = Injector(_configure)


def provide(clazz: Type[T]) -> T:
    _create_injector()

    return _injector.get(clazz)
