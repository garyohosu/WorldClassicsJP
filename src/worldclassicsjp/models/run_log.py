"""RunLog — /logs/YYYY/MM/DD/{run_id}.json 実行ログ"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunLog:
    run_id: str
    date: str
    stage: str
    status: str
    errors: list = field(default_factory=list)

    def append(self, entry: dict) -> None:
        """エラーエントリを追記する"""
        self.errors.append(entry)

    def save(self, path: Path) -> None:
        """ログファイルを保存する（親ディレクトリを自動生成）"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "run_id": self.run_id,
                    "date": self.date,
                    "stage": self.stage,
                    "status": self.status,
                    "errors": self.errors,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
