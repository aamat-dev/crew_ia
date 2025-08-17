# apps/orchestrator/bootstrap.py
import os
from core.storage.file_adapter import FileAdapter
from core.storage.postgres_adapter import PostgresAdapter
from core.storage.composite_adapter import CompositeAdapter

def make_storage():
    file_ad = FileAdapter(root=".runs")  # ton adapter existant
    pg_ad = PostgresAdapter(os.getenv("DATABASE_URL"))  # postgresql+asyncpg://...
    return CompositeAdapter([file_ad, pg_ad])

# objet global que le reste de l’app peut importer
STORAGE = make_storage()
