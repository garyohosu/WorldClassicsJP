"""カスタム例外クラス — エラーハンドリングの粒度向上"""


class WorldClassicsJPError(Exception):
    """WorldClassicsJP の基底例外クラス"""
    pass


# ============================================================
# リトライ可能/不可能の分類
# ============================================================


class TemporaryError(WorldClassicsJPError):
    """一時的なエラー（リトライ推奨）"""
    pass


class PermanentError(WorldClassicsJPError):
    """恒久的なエラー（リトライ不可、即座に failed 遷移）"""
    pass


# ============================================================
# ステージ別エラー
# ============================================================


class FetchError(TemporaryError):
    """原文取得エラー（ネットワーク障害等）"""
    pass


class SourceUnavailableError(PermanentError):
    """原文が恒久的に取得不能（exhausted 遷移の条件2）"""
    pass


class PreprocessError(TemporaryError):
    """前処理エラー（LLM 応答異常等）"""
    pass


class TranslationError(TemporaryError):
    """翻訳エラー（Codex CLI 実行失敗、タイムアウト等）"""
    pass


class TranslationFormatError(TemporaryError):
    """翻訳結果の形式エラー（JSON 不正、必須キー欠落）"""
    pass


class QualityCheckError(TemporaryError):
    """品質チェックエラー（LLM 応答異常等）"""
    pass


class QualityCheckFailure(WorldClassicsJPError):
    """品質チェック不合格（リトライ対象）"""
    pass


class PublishError(TemporaryError):
    """公開処理エラー（HTML 生成失敗等）"""
    pass


class GitError(TemporaryError):
    """Git 操作エラー（commit/push 失敗）"""
    pass


class RollbackError(PermanentError):
    """ロールバック失敗（重大な状態不整合）"""
    pass


# ============================================================
# 状態管理エラー
# ============================================================


class StateLockError(WorldClassicsJPError):
    """state.lock 取得失敗（二重起動検出）"""
    pass


class StateCorruptionError(PermanentError):
    """state.json の破損（復旧不能）"""
    pass


# ============================================================
# 設定エラー
# ============================================================


class ConfigError(PermanentError):
    """設定ファイルエラー（必須フィールド欠落、値域違反）"""
    pass


class WorksMasterError(PermanentError):
    """works_master.json のエラー（データ不整合）"""
    pass


# ============================================================
# 使用例
# ============================================================

"""
使用例:

# Translator での使用
try:
    result = subprocess.run(...)
except subprocess.TimeoutExpired as e:
    raise TranslationError("Codex CLI がタイムアウトしました") from e
except subprocess.CalledProcessError as e:
    if "network" in e.stderr.lower():
        raise TranslationError("ネットワークエラー") from e
    else:
        raise PermanentError("Codex CLI が恒久的に失敗") from e

# Pipeline でのハンドリング
try:
    result = self.translator.translate(segment.text)
except TemporaryError as e:
    # リトライ可能
    self.state.translate_retry_count += 1
    logger.warning(f"一時的エラー、リトライします: {e}")
except PermanentError as e:
    # 即座に failed 遷移
    self.state.current_work_status = WorkStatus.FAILED
    logger.error(f"恒久的エラー、処理を中断します: {e}")
"""
