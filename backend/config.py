"""Path constants and env-var configuration."""
import os

BEETS_CONFIG_PATH = os.environ.get("BEETS_CONFIG_PATH", "/beets/config/config.yaml")
BEETS_LIBRARY_PATH = os.environ.get("BEETS_LIBRARY_PATH", "/beets/db/library.db")
MUSIC_ROOT = os.environ.get("MUSIC_ROOT", "/data/media/music")
DOWNLOADS_ROOT = os.environ.get("DOWNLOADS_ROOT", "/data/downloads/completed/music")

NAVIDROME_URL = os.environ.get("NAVIDROME_URL", "http://navidrome:4533")
NAVIDROME_ADMIN_USER = os.environ.get("NAVIDROME_ADMIN_USER", "")
NAVIDROME_ADMIN_PASS = os.environ.get("NAVIDROME_ADMIN_PASS", "")
