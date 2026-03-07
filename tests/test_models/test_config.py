"""Config のテスト"""

import pytest

from worldclassicsjp.models.config import Config


class TestConfigLoad:
    def test_正常なyamlを読み込める(self, config_yaml):
        cfg = Config.load(config_yaml["path"])
        assert cfg.host            == "localhost"
        assert cfg.port            == 11434
        assert cfg.model           == "llama3"
        assert cfg.daily_max_chars == 12000
        assert cfg.current_phase   == 1

    def test_必須フィールドが欠落するとValueError(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("host: localhost\nport: 11434\nmodel: llama3\n")
        with pytest.raises(ValueError, match="daily_max_chars"):
            Config.load(path)

    def test_current_phaseが4以上はValueError(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(
            "host: localhost\nport: 11434\nmodel: llama3\n"
            "daily_max_chars: 12000\ncurrent_phase: 4\n"
        )
        with pytest.raises(ValueError, match="current_phase"):
            Config.load(path)

    def test_current_phaseが0はValueError(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(
            "host: localhost\nport: 11434\nmodel: llama3\n"
            "daily_max_chars: 12000\ncurrent_phase: 0\n"
        )
        with pytest.raises(ValueError, match="current_phase"):
            Config.load(path)

    def test_daily_max_charsが0以下はValueError(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text(
            "host: localhost\nport: 11434\nmodel: llama3\n"
            "daily_max_chars: 0\ncurrent_phase: 1\n"
        )
        with pytest.raises(ValueError, match="daily_max_chars"):
            Config.load(path)

    @pytest.mark.parametrize("phase", [1, 2, 3])
    def test_current_phaseが1_2_3は有効(self, tmp_path, phase):
        path = tmp_path / "config.yaml"
        path.write_text(
            f"host: localhost\nport: 11434\nmodel: llama3\n"
            f"daily_max_chars: 12000\ncurrent_phase: {phase}\n"
        )
        cfg = Config.load(path)
        assert cfg.current_phase == phase
