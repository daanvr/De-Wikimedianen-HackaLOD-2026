"""Which fields a record shows, per content type. See pipeline/fields.toml."""
from dataclasses import dataclass
from pathlib import Path
import re
import tomllib

from siboga.config import PIPELINE_DIR
from siboga.models import FieldType

ISO_DATE = re.compile(r"-?\d{4}(-\d{2}(-\d{2})?)?")

@dataclass
class FieldCatalog:
    profiles: dict[str, list[str]]
    types: dict[str, FieldType]

    def is_valid(
        self,
        key: str,
        value: str
    ) -> bool:
        if self.types[key] == FieldType.DATE:
            return ISO_DATE.fullmatch(value) is not None
        return bool(value.strip())

def load_fields(path: Path = PIPELINE_DIR / "fields.toml") -> FieldCatalog:
    with path.open("rb") as file:
        data = tomllib.load(file)
    types = {key: FieldType(value) for key, value in data["fields"].items()}
    profiles = {content_type: list(keys) for content_type, keys in data["contenttypes"].items()}
    for content_type, keys in profiles.items():
        unknown = [key for key in keys if key not in types]
        if unknown:
            raise ValueError(f"{path}: contenttype {content_type} gebruikt onbekende velden {unknown}")
    return FieldCatalog(profiles = profiles, types = types)
