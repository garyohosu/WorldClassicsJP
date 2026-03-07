"""ImageMeta — 画像 YAML sidecar データモデル"""

from dataclasses import dataclass

from .enums import RightsLabel


@dataclass
class ImageMeta:
    source_page_url: str
    file_url: str
    author: str
    rights_label: RightsLabel
    year: int
    rights_verified_at: str

    def __post_init__(self) -> None:
        self.rights_label = RightsLabel(self.rights_label)
