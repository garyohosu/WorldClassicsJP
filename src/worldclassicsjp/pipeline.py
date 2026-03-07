"""Pipeline — 日次翻訳パイプラインのオーケストレーター"""

from __future__ import annotations

from .models.enums import Stage, WorkStatus
from .models.state import State
from .preprocessor import Segment
from .translator import TranslationResult
from .quality_checker import QAResult


class Pipeline:
    """
    state.json を基準にパイプラインを実行する。
    各コンポーネントはコンストラクタで注入（DI）する。
    """

    def __init__(
        self,
        run_id: str,
        state: State,
        preprocessor,
        translator,
        quality_checker,
        publisher,
    ) -> None:
        self.run_id         = run_id
        self.state          = state
        self.preprocessor   = preprocessor
        self.translator     = translator
        self.quality_checker = quality_checker
        self.publisher      = publisher

    # ── 翻訳リトライ制御 ─────────────────────────────────────────────

    def execute_translate_with_retry(self, segment: Segment) -> TranslationResult | None:
        """
        翻訳 + 品質チェックを最大 (1 + MAX_TRANSLATE_RETRIES) 回試みる。
        成功した場合は TranslationResult を返し、カウンタをリセットする。
        全試行が失敗した場合は None を返す。
        """
        max_attempts = State.MAX_TRANSLATE_RETRIES + 1  # 初回 1 回 + 再翻訳 2 回

        for attempt in range(max_attempts):
            try:
                result: TranslationResult = self.translator.translate(segment.text)
                qa: QAResult = self.quality_checker.check(segment.text, result.translated_text)

                if qa.status == "pass":
                    self.state.translate_retry_count = 0
                    self.state.consecutive_fail_days  = 0
                    self.state.current_stage = Stage.PUBLISH
                    return result
                else:
                    self.state.translate_retry_count = min(attempt + 1, State.MAX_TRANSLATE_RETRIES)

            except Exception:
                self.state.translate_retry_count = min(attempt + 1, State.MAX_TRANSLATE_RETRIES)

        return None  # 全試行失敗

    def handle_daily_translate_failure(self) -> None:
        """
        当日の翻訳が最終的に失敗した場合に呼ぶ。
        consecutive_fail_days を増加させ、上限に達したら failed に遷移する。
        """
        self.state.consecutive_fail_days += 1
        self.state.current_stage = Stage.TRANSLATE  # ステージを維持

        if self.state.consecutive_fail_days >= State.MAX_CONSECUTIVE_FAIL_DAYS:
            self.state.current_work_status = WorkStatus.FAILED

    def reset_translate_retry_for_next_day(self) -> None:
        """翌日の再試行開始時に translate_retry_count を 0 に戻す"""
        self.state.translate_retry_count = 0

    # ── 公開リトライ制御 ─────────────────────────────────────────────

    def handle_publish_failure(self) -> None:
        """
        公開が失敗した場合に呼ぶ。
        publish_retry_count を増加させ、上限に達したら failed に遷移する。
        """
        self.state.publish_retry_count += 1
        self.state.current_stage = Stage.PUBLISH  # ステージを維持

        if self.state.publish_retry_count >= State.MAX_PUBLISH_RETRIES:
            self.state.current_work_status = WorkStatus.FAILED

    def on_publish_success(self) -> None:
        """公開成功時: publish_retry_count と pre_publish_head をリセットして part を進める"""
        self.state.publish_retry_count = 0
        self.state.pre_publish_head    = ""
        self.state.current_part       += 1
        self.state.current_stage       = Stage.IDLE

    # ── 次作品移行 ────────────────────────────────────────────────────

    def load_next_work(self, works: list) -> None:
        """
        current_work_id より大きい pd_verified=True の作品を昇順で探し、
        見つかれば active へ遷移、なければ exhausted へ遷移する。
        """
        candidates = sorted(
            [w for w in works if w.pd_verified and w.work_id > self.state.current_work_id],
            key=lambda w: w.work_id,
        )
        if candidates:
            nxt = candidates[0]
            self.state.current_work_id     = nxt.work_id
            self.state.next_work_id        = nxt.work_id
            self.state.current_part        = 1
            self.state.current_segment_id  = ""
            self.state.current_stage       = Stage.IDLE
            self.state.current_work_status = WorkStatus.ACTIVE
        else:
            self.state.current_work_status = WorkStatus.EXHAUSTED
            self.state.current_stage       = Stage.IDLE
