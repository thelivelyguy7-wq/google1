import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    db_path: Path = field(default_factory=lambda: Path(os.environ.get("DE_DB_PATH", ROOT / "data" / "discovery.db")))
    model: str = os.environ.get("DE_MODEL", "claude-opus-5")
    effort: str = os.environ.get("DE_EFFORT", "medium")          # per-chunk extraction; raise for harder corpora
    synthesis_effort: str = os.environ.get("DE_SYNTHESIS_EFFORT", "high")
    concurrency: int = int(os.environ.get("DE_CONCURRENCY", "4"))
    chunk_chars: int = int(os.environ.get("DE_CHUNK_CHARS", "3500"))
    author_salt: str = os.environ.get("DE_AUTHOR_SALT", "discovery-engine-local-salt")
    min_sample_for_percent: int = int(os.environ.get("DE_MIN_SAMPLE", "30"))
    # How outputs describe where the data came from:
    #   "auto"    – say when records are flagged as generated (banners, caveats)
    #   "neutral" – name the dataset only, and make no claim either way
    # The per-record `is_synthetic` field is unaffected; this controls presentation.
    provenance: str = os.environ.get("DE_PROVENANCE", "auto")


settings = Settings()
