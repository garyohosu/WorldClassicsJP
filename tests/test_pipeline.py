"""パイプライン のテスト"""

import pytest

from worldclassicsjp.models.enums import Stage, WorkStatus
from worldclassicsjp.models.state import State
from worldclassicsjp.models.works_master import WorksMaster
from worldclassicsjp.models.enums import LengthClass, SourceType
from worldclassicsjp.pipeline import Pipeline
from worldclassicsjp.preprocessor import Segment
from worldclassicsjp.translator import TranslationResult
from worldclassicsjp.quality_checker import QAResult


# -- フィクスチャ --


def make_state(work_id: int = 1, publish_retry: int = 0, fail_days: int = 0,
               translate_retry: int = 0) -> State:
    s = State.init_default(min_work_id=work_id)
    s.current_stage = Stage.TRANSLATE
    s.publish_retry_count = publish_retry
    s.consecutive_fail_days = fail_days
    s.translate_retry_count = translate_retry
    return s


def make_segment(text: str = "Hello world.") -> Segment:
    return Segment(segment_id="part-001", part_number=1, text=text, char_count=len(text))


def make_work(work_id: int, pd_verified: bool = True) -> WorksMaster:
    slug = "work-" + str(work_id)
    title = "Work " + str(work_id)
    return WorksMaster(
        work_id=work_id,
        work_slug=slug,
        title=title,
        title_ja=title + " (日本語)",
        author_name="Author",
        author_name_ja="著者",
        author_slug="author",
        source_type=SourceType.TEXT_URL,
        source_url="https://example.com",
        death_year=1900,
        pd_verified=pd_verified,
        length_class=LengthClass.MEDIUM,
    )


class FakeTranslatorSuccess:
    def translate(self, text: str) -> TranslationResult:
        return TranslationResult(
            translated_text="翻訳済みテキスト",
            summary="要約",
            keywords=["キーワード"],
        )


class FakeTranslatorFail:
    def translate(self, text: str) -> TranslationResult:
        raise RuntimeError("翻訳失敗")


class FakeQCPass:
    def check(self, original: str, translated: str) -> QAResult:
        return QAResult(status="pass", score=0.95)


class FakeQCFail:
    def check(self, original: str, translated: str) -> QAResult:
        return QAResult(status="fail", score=0.3, issues=["問題あり"])


def make_pipeline(state: State, translator=None, qc=None) -> Pipeline:
    return Pipeline(
        run_id="test-run",
        state=state,
        preprocessor=None,
        translator=translator or FakeTranslatorSuccess(),
        quality_checker=qc or FakeQCPass(),
        publisher=None,
    )


# -- execute_translate_with_retry --


class TestExecuteTranslateWithRetry:
    def test_翻訳成功でTranslationResultを返す(self):
        state = make_state()
        pipeline = make_pipeline(state)
        result = pipeline.execute_translate_with_retry(make_segment())
        assert result is not None
        assert result.translated_text == "翻訳済みテキスト"

    def test_成功後にtranslate_retry_countが0にリセットされる(self):
        state = make_state(translate_retry=1)
        pipeline = make_pipeline(state)
        pipeline.execute_translate_with_retry(make_segment())
        assert state.translate_retry_count == 0

    def test_成功後にconsecutive_fail_daysが0にリセットされる(self):
        state = make_state(fail_days=1)
        pipeline = make_pipeline(state)
        pipeline.execute_translate_with_retry(make_segment())
        assert state.consecutive_fail_days == 0

    def test_QCがfailし続けるとNoneを返す(self):
        state = make_state()
        pipeline = make_pipeline(state, qc=FakeQCFail())
        result = pipeline.execute_translate_with_retry(make_segment())
        assert result is None

    def test_翻訳が失敗し続けるとNoneを返す(self):
        state = make_state()
        pipeline = make_pipeline(state, translator=FakeTranslatorFail())
        result = pipeline.execute_translate_with_retry(make_segment())
        assert result is None

    def test_全失敗後にretry_countがMAXになる(self):
        state = make_state()
        pipeline = make_pipeline(state, qc=FakeQCFail())
        pipeline.execute_translate_with_retry(make_segment())
        assert state.translate_retry_count == State.MAX_TRANSLATE_RETRIES + 1


# -- handle_daily_translate_failure --


class TestHandleDailyTranslateFailure:
    def test_consecutive_fail_daysが増加する(self):
        state = make_state(fail_days=0)
        pipeline = make_pipeline(state)
        pipeline.handle_daily_translate_failure()
        assert state.consecutive_fail_days == 1

    def test_上限に達するとfailedになる(self):
        state = make_state(fail_days=State.MAX_CONSECUTIVE_FAIL_DAYS - 1)
        pipeline = make_pipeline(state)
        pipeline.handle_daily_translate_failure()
        assert state.current_work_status == WorkStatus.FAILED

    def test_上限未満はfailedにならない(self):
        state = make_state(fail_days=0)
        pipeline = make_pipeline(state)
        pipeline.handle_daily_translate_failure()
        assert state.current_work_status != WorkStatus.FAILED


# -- handle_publish_failure --


class TestHandlePublishFailure:
    def test_publish_retry_countが増加する(self):
        state = make_state(publish_retry=0)
        pipeline = make_pipeline(state)
        pipeline.handle_publish_failure()
        assert state.publish_retry_count == 1

    def test_上限以上でfailedになる(self):
        state = make_state(publish_retry=State.MAX_PUBLISH_RETRIES - 1)
        pipeline = make_pipeline(state)
        pipeline.handle_publish_failure()
        assert state.current_work_status == WorkStatus.FAILED

    def test_上限未満はfailedにならない(self):
        state = make_state(publish_retry=0)
        pipeline = make_pipeline(state)
        pipeline.handle_publish_failure()
        assert state.current_work_status != WorkStatus.FAILED


# -- on_publish_success --


class TestOnPublishSuccess:
    def test_publish_retry_countがリセットされる(self):
        state = make_state(publish_retry=2)
        pipeline = make_pipeline(state)
        pipeline.on_publish_success()
        assert state.publish_retry_count == 0

    def test_pre_publish_headがクリアされる(self):
        state = make_state()
        state.pre_publish_head = "a" * 40
        pipeline = make_pipeline(state)
        pipeline.on_publish_success()
        assert state.pre_publish_head == ""

    def test_current_partが1増える(self):
        state = make_state()
        state.current_part = 1
        pipeline = make_pipeline(state)
        pipeline.on_publish_success()
        assert state.current_part == 2

    def test_ステージがIDLEになる(self):
        state = make_state()
        pipeline = make_pipeline(state)
        pipeline.on_publish_success()
        assert state.current_stage == Stage.IDLE


# -- load_next_work --


class TestLoadNextWork:
    def test_次の作品が見つかれば_work_idが更新される(self):
        state = make_state(work_id=1)
        pipeline = make_pipeline(state)
        works = [make_work(1), make_work(2)]
        pipeline.load_next_work(works)
        assert state.current_work_id == 2

    def test_次の作品が見つかればstatusがactiveになる(self):
        state = make_state(work_id=1)
        pipeline = make_pipeline(state)
        works = [make_work(1), make_work(2)]
        pipeline.load_next_work(works)
        assert state.current_work_status == WorkStatus.ACTIVE

    def test_次の作品が見つかればpartが1にリセットされる(self):
        state = make_state(work_id=1)
        state.current_part = 5
        pipeline = make_pipeline(state)
        works = [make_work(1), make_work(2)]
        pipeline.load_next_work(works)
        assert state.current_part == 1

    def test_pd_verified_FalseはスキップされるExhaustedになる(self):
        state = make_state(work_id=1)
        pipeline = make_pipeline(state)
        works = [make_work(1), make_work(2, pd_verified=False)]
        pipeline.load_next_work(works)
        assert state.current_work_status == WorkStatus.EXHAUSTED

    def test_候補がなければexhaustedになる(self):
        state = make_state(work_id=99)
        pipeline = make_pipeline(state)
        works = [make_work(1), make_work(2)]
        pipeline.load_next_work(works)
        assert state.current_work_status == WorkStatus.EXHAUSTED

    def test_複数候補のうち最小のwork_idが選ばれる(self):
        state = make_state(work_id=1)
        pipeline = make_pipeline(state)
        works = [make_work(1), make_work(5), make_work(3)]
        pipeline.load_next_work(works)
        assert state.current_work_id == 3
