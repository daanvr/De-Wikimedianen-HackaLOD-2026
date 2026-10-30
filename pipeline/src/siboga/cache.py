"""Local cache: raw responses in one SQLite file, downloaded files in a directory."""
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
import hashlib
import re
import sqlite3

from siboga.models import CachedResponse

_SCHEMA = """
CREATE TABLE IF NOT EXISTS response (
    url TEXT PRIMARY KEY,
    adapter TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status INTEGER NOT NULL,
    content_type TEXT,
    body BLOB
)
"""

# A good response (2xx) is never replaced by a failed attempt.
_UPSERT = """
INSERT INTO response (url, adapter, fetched_at, status, content_type, body)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT (url) DO UPDATE SET
    adapter = excluded.adapter,
    fetched_at = excluded.fetched_at,
    status = excluded.status,
    content_type = excluded.content_type,
    body = excluded.body
WHERE excluded.status BETWEEN 200 AND 299
    OR response.status NOT BETWEEN 200 AND 299
"""

# Something like .jpg, .tiff or .mp3: a letter followed by one to four letters or digits.
_SUFFIX_PATTERN = re.compile(r"^\.[a-z][a-z0-9]{1,4}$")

class Cache:
    """Stores everything that comes from outside, so the site can also be built without internet."""
    def __init__(
        self,
        db_path: Path,
        media_dir: Path
    ):
        self.db_path = Path(db_path)
        self.media_dir = Path(media_dir)
        self.db_path.parent.mkdir(parents = True, exist_ok = True)
        self.media_dir.mkdir(parents = True, exist_ok = True)
        self._connection = sqlite3.connect(self.db_path)
        self._connection.execute(_SCHEMA)
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def get(self, url: str) -> CachedResponse | None:
        row = self._connection.execute(
            "SELECT adapter, body, content_type, fetched_at, status, url FROM response WHERE url = ?",
            (url,)
        ).fetchone()
        if row is None:
            return None
        adapter, body, content_type, fetched_at, status, stored_url = row
        return CachedResponse(
            adapter = adapter,
            body = bytes(body) if body is not None else None,
            content_type = content_type,
            fetched_at = fetched_at,
            status = status,
            url = stored_url
        )

    def get_json(self, url: str) -> dict | list | None:
        response = self.get(url)
        return response.json() if response else None

    def has_media(self, url: str) -> bool:
        return self.media_path(url).is_file()

    def media_path(self, url: str) -> Path:
        name = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self.media_dir / f"{name}{_suffix(url)}"

    def put(self, response: CachedResponse) -> None:
        self._connection.execute(
            _UPSERT,
            (
                response.url,
                response.adapter,
                response.fetched_at,
                response.status,
                response.content_type,
                response.body
            )
        )
        self._connection.commit()

def _suffix(url: str) -> str:
    """The extension of the URL path, in lowercase, or "" if it does not look like an extension."""
    path = unquote(urlsplit(url).path)
    suffix = PurePosixPath(path).suffix.lower()
    return suffix if _SUFFIX_PATTERN.match(suffix) else ""
