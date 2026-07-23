"""Zdroje firiem (leadov)."""
from .base import Source
from .seed import SeedSource
from .atlasfiriem import AtlasFiriemSource
from .search import SearchSource

# Registrácia zdrojov dostupných z CLI.
SOURCES: dict[str, type[Source]] = {
    "seed": SeedSource,
    "atlasfiriem": AtlasFiriemSource,
    "search": SearchSource,
}
