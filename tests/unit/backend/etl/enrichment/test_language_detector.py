from collections import OrderedDict
from types import SimpleNamespace

import pytest

from app.etl.enrichment import language_detector as module
from app.etl.enrichment.language_detector import (
    LanguageDetector,
    clean_text_for_detection,
)
from app.shared.languages import DEFAULT_LANGUAGE_CODE, LanguageCode


class TestCleanTextForDetection:
    def test_empty_text_is_returned_unchanged(self):
        assert clean_text_for_detection("") == ""

    def test_none_like_empty_value_is_returned_unchanged(self):
        assert clean_text_for_detection("") == ""

    def test_removes_german_gender_suffixes(self):
        text = "Softwareentwickler (m/w/d)"
        assert clean_text_for_detection(text) == "Softwareentwickler"

    def test_removes_multiple_german_suffixes(self):
        text = "Developer (m/w/d) und Manager (w/m/d)"
        assert clean_text_for_detection(text) == "Developer und Manager"

    def test_normalizes_extra_whitespace(self):
        text = "Senior   Software   Engineer"
        assert clean_text_for_detection(text) == "Senior Software Engineer"


class TestLanguageDetectorHelpers:
    @pytest.fixture
    def detector(self):
        return LanguageDetector()

    def test_get_cache_key_is_case_insensitive(self, detector):
        assert detector._get_cache_key("Python Developer") == detector._get_cache_key(
            "python developer"
        )

    def test_get_cache_key_is_stable(self, detector):
        first = detector._get_cache_key("Senior Software Engineer")
        second = detector._get_cache_key("Senior Software Engineer")

        assert first == second
        assert len(first) == 40

    def test_should_detect_rejects_empty_text(self, detector):
        assert detector._should_detect("") is False

    def test_should_detect_rejects_whitespace(self, detector):
        assert detector._should_detect("   ") is False

    def test_should_detect_rejects_short_text(self, detector):
        assert detector._should_detect("abcd") is False

    def test_should_detect_accepts_minimum_length_text(self, detector):
        assert detector._should_detect("abcde") is True

    def test_should_detect_accepts_longer_text(self, detector):
        assert detector._should_detect("Software Engineer") is True

    def test_cache_get_returns_none_for_missing_key(self, detector):
        result = detector._cache_get("missing")

        assert result is None
        assert detector._cache_misses == 1
        assert detector._cache_hits == 0

    def test_cache_set_and_get_records_hit(self, detector):
        value = (LanguageCode.ENGLISH, 0.95)

        detector._cache_set("key", value)
        result = detector._cache_get("key")

        assert result == value
        assert detector._cache_hits == 1
        assert detector._cache_misses == 0

    def test_cache_get_updates_lru_order(self, detector):
        detector._cache = OrderedDict(
            [
                ("first", (LanguageCode.ENGLISH, 0.9)),
                ("second", (LanguageCode.FRENCH, 0.8)),
            ]
        )

        detector._cache_get("first")

        assert list(detector._cache.keys()) == ["second", "first"]

    def test_cache_set_updates_existing_entry(self, detector):
        detector._cache_set("key", (LanguageCode.ENGLISH, 0.5))
        detector._cache_set("key", (LanguageCode.FRENCH, 0.9))

        assert detector._cache["key"] == (LanguageCode.FRENCH, 0.9)
        assert len(detector._cache) == 1

    def test_cache_set_evicts_oldest_entry(self, detector):
        detector.MAX_CACHE_SIZE = 2

        detector._cache_set("first", (LanguageCode.ENGLISH, 0.9))
        detector._cache_set("second", (LanguageCode.FRENCH, 0.8))
        detector._cache_set("third", (LanguageCode.GERMAN, 0.7))

        assert "first" not in detector._cache
        assert "second" in detector._cache
        assert "third" in detector._cache
        assert detector._cache_evictions == 1

    def test_to_language_code_converts_supported_language(self, detector):
        result = detector._to_language_code(module.Language.ENGLISH)

        assert result == LanguageCode.ENGLISH

    def test_to_language_code_returns_none_for_invalid_language(self, detector):
        invalid_language = SimpleNamespace(
            iso_code_639_1=SimpleNamespace(name="not_a_real_language")
        )

        assert detector._to_language_code(invalid_language) is None

    def test_to_language_code_returns_none_when_iso_code_missing(self, detector):
        invalid_language = SimpleNamespace()

        assert detector._to_language_code(invalid_language) is None


class TestConfidence:
    @pytest.fixture
    def detector(self):
        return LanguageDetector()

    def test_get_confidence_returns_zero_point_five_when_no_values(self, detector):
        detector.detector = SimpleNamespace(
            compute_language_confidence_values=lambda text: []
        )

        assert detector._get_confidence("some text") == 0.5

    def test_get_confidence_returns_highest_value(self, detector):
        detector.detector = SimpleNamespace(
            compute_language_confidence_values=lambda text: [
                SimpleNamespace(value=0.25),
                SimpleNamespace(value=0.91),
                SimpleNamespace(value=0.60),
            ]
        )

        assert detector._get_confidence("some text") == 0.91

    def test_get_confidence_returns_default_when_detector_raises(self, detector):
        def raise_error(text):
            raise RuntimeError("confidence failure")

        detector.detector = SimpleNamespace(
            compute_language_confidence_values=raise_error
        )

        assert detector._get_confidence("some text") == 0.5


class TestCacheUtilities:
    @pytest.fixture
    def detector(self):
        return LanguageDetector()

    def test_clear_cache_resets_cache_and_statistics(self, detector):
        detector._cache_set("key", (LanguageCode.ENGLISH, 0.9))
        detector._cache_get("key")
        detector._cache_get("missing")
        detector._cache_evictions = 2

        detector.clear_cache()

        assert detector.get_cache_size() == 0
        assert detector._cache_hits == 0
        assert detector._cache_misses == 0
        assert detector._cache_evictions == 0

    def test_get_cache_size_returns_current_size(self, detector):
        assert detector.get_cache_size() == 0

        detector._cache_set("one", (LanguageCode.ENGLISH, 0.9))
        detector._cache_set("two", (LanguageCode.FRENCH, 0.8))

        assert detector.get_cache_size() == 2

    def test_get_cache_stats_returns_zero_hit_rate_when_unused(self, detector):
        stats = detector.get_cache_stats()

        assert stats["size"] == 0
        assert stats["max_size"] == detector.MAX_CACHE_SIZE
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_rate"] == 0.0

    def test_get_cache_stats_calculates_hit_rate(self, detector):
        detector._cache_set("key", (LanguageCode.ENGLISH, 0.9))

        detector._cache_get("key")
        detector._cache_get("missing")

        stats = detector.get_cache_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0
        assert stats["size"] == 1


class TestDetection:
    @pytest.fixture
    def detector(self):
        return LanguageDetector()

    def test_detect_internal_returns_default_for_short_text(self, detector):
        result = detector._detect_internal("abcd")
        assert result == (DEFAULT_LANGUAGE_CODE, 0.0)

    def test_detect_internal_returns_cached_result(self, detector):
        cached = (LanguageCode.FRENCH, 0.88)
        detector._cache_set(detector._get_cache_key("Bonjour tout le monde"), cached)

        result = detector._detect_internal("Bonjour tout le monde")

        assert result == cached
        assert detector._cache_hits == 1

    def test_detect_internal_handles_no_detected_language(self, detector):
        detector.detector = SimpleNamespace(
            detect_language_of=lambda text: None
        )

        result = detector._detect_internal("some sufficiently long text")

        assert result == (DEFAULT_LANGUAGE_CODE, 0.0)
        assert detector.get_cache_size() == 1

    def test_detect_internal_handles_unsupported_language(self, detector):
        detector.detector = SimpleNamespace(
            detect_language_of=lambda text: SimpleNamespace(
                iso_code_639_1=SimpleNamespace(name="not_a_real_language")
            ),
            compute_language_confidence_values=lambda text: [],
        )

        result = detector._detect_internal("some sufficiently long text")

        assert result == (DEFAULT_LANGUAGE_CODE, 0.0)
        assert detector.get_cache_size() == 1

    def test_detect_internal_successfully_detects_language(self, detector):
        detector.detector = SimpleNamespace(
            detect_language_of=lambda text: module.Language.ENGLISH,
            compute_language_confidence_values=lambda text: [
                SimpleNamespace(value=0.94),
            ],
        )

        result = detector._detect_internal("This is an English sentence")

        assert result == (LanguageCode.ENGLISH, 0.94)
        assert detector.get_cache_size() == 1

    def test_detect_internal_handles_detector_exception(self, detector):
        def raise_error(text):
            raise RuntimeError("detector failure")

        detector.detector = SimpleNamespace(
            detect_language_of=raise_error,
        )

        result = detector._detect_internal("some sufficiently long text")

        assert result == (DEFAULT_LANGUAGE_CODE, 0.0)
        assert detector.get_cache_size() == 1

    def test_detect_returns_language_only(self, detector):
        detector._detect_internal = lambda text: (LanguageCode.GERMAN, 0.91)

        assert detector.detect("German text") == LanguageCode.GERMAN

    def test_detect_with_confidence_returns_both_values(self, detector):
        expected = (LanguageCode.SPANISH, 0.87)
        detector._detect_internal = lambda text: expected

        assert detector.detect_with_confidence("Spanish text") == expected

    def test_is_english_returns_true_for_english(self, detector):
        detector.detect = lambda text: LanguageCode.ENGLISH

        assert detector.is_english("English text") is True

    def test_is_english_returns_false_for_non_english(self, detector):
        detector.detect = lambda text: LanguageCode.FRENCH

        assert detector.is_english("French text") is False

    def test_is_english_with_confidence_returns_values(self, detector):
        detector.detect_with_confidence = lambda text: (
            LanguageCode.ENGLISH,
            0.96,
        )

        assert detector.is_english_with_confidence("English text") == (True, 0.96)

    def test_is_english_with_confidence_returns_false_for_non_english(self, detector):
        detector.detect_with_confidence = lambda text: (
            LanguageCode.FRENCH,
            0.91,
        )

        assert detector.is_english_with_confidence("French text") == (False, 0.91)

    def test_get_supported_languages_returns_language_codes(self, detector):
        languages = detector.get_supported_languages()

        assert isinstance(languages, tuple)
        assert "en" in languages
        assert "fr" in languages
        assert len(languages) > 0

class TestConvenienceFunctions:
    def test_get_detector_creates_singleton(self, monkeypatch):
        fake_detector = object()
        monkeypatch.setattr(module, "_detector", None)
        monkeypatch.setattr(module, "LanguageDetector", lambda: fake_detector)

        first = module.get_detector()
        second = module.get_detector()

        assert first is fake_detector
        assert second is fake_detector

    def test_detect_language_delegates_to_singleton(self, monkeypatch):
        fake_detector = SimpleNamespace(
            detect=lambda text: LanguageCode.ENGLISH
        )
        monkeypatch.setattr(module, "get_detector", lambda: fake_detector)

        assert module.detect_language("English text") == LanguageCode.ENGLISH

    def test_is_english_delegates_to_singleton(self, monkeypatch):
        fake_detector = SimpleNamespace(
            is_english=lambda text: True
        )
        monkeypatch.setattr(module, "get_detector", lambda: fake_detector)

        assert module.is_english("English text") is True

    def test_detect_language_with_confidence_delegates_to_singleton(
        self, monkeypatch
    ):
        expected = (LanguageCode.FRENCH, 0.89)
        fake_detector = SimpleNamespace(
            detect_with_confidence=lambda text: expected
        )
        monkeypatch.setattr(module, "get_detector", lambda: fake_detector)

        assert module.detect_language_with_confidence("French text") == expected

    def test_clear_language_cache_delegates_to_singleton(self, monkeypatch):
        called = False

        def clear_cache():
            nonlocal called
            called = True

        fake_detector = SimpleNamespace(clear_cache=clear_cache)
        monkeypatch.setattr(module, "get_detector", lambda: fake_detector)

        module.clear_language_cache()

        assert called is True

    def test_get_language_cache_stats_delegates_to_singleton(self, monkeypatch):
        expected = {
            "size": 1,
            "max_size": 5000,
            "used_percent": 0.02,
            "hits": 1,
            "misses": 2,
            "evictions": 0,
            "hit_rate": 33.33,
        }

        fake_detector = SimpleNamespace(
            get_cache_stats=lambda: expected
        )
        monkeypatch.setattr(module, "get_detector", lambda: fake_detector)

        assert module.get_language_cache_stats() == expected

class TestDetectorInitialization:
    def test_build_detector_raises_runtime_error_when_builder_fails(
        self, monkeypatch
    ):
        detector = LanguageDetector.__new__(LanguageDetector)

        class FailingBuilder:
            @classmethod
            def from_languages(cls, *languages):
                raise RuntimeError("builder failure")

        monkeypatch.setattr(module, "LanguageDetectorBuilder", FailingBuilder)

        with pytest.raises(
            RuntimeError,
            match="Language detector initialization failed",
        ):
            detector._build_detector()

class TestLinguaImportFallback:
    def test_module_raises_import_error_when_lingua_is_unavailable(
        self, monkeypatch
    ):
        import builtins
        import importlib.util
        from pathlib import Path

        original_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name == "lingua":
                raise ImportError("lingua unavailable")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", blocked_import)

        module_path = Path(module.__file__)

        spec = importlib.util.spec_from_file_location(
            "language_detector_without_lingua",
            module_path,
        )

        fallback_module = importlib.util.module_from_spec(spec)

        # Prevent the module's final ImportError temporarily so we can
        # exercise the fallback classes themselves.
        monkeypatch.setattr(
            fallback_module,
            "__name__",
            "language_detector_without_lingua",
        )

        with pytest.raises(ImportError):
            spec.loader.exec_module(fallback_module)

    def test_fallback_builder_methods_are_executable(self):
        import ast
        from pathlib import Path

        source_path = Path(module.__file__)
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        fallback_classes = [
            node
            for node in tree.body
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
        ]

        # The fallback classes are inside the `else` branch of the
        # TYPE_CHECKING conditional.
        else_body = fallback_classes[0].orelse

        class_nodes = [
            node
            for node in else_body
            if isinstance(node, ast.Try)
        ][0].handlers[0].body

        fallback_class_nodes = [
            node
            for node in class_nodes
            if isinstance(node, ast.ClassDef)
            and node.name in {"LanguageDetectorBuilder", "ConfidenceValue", "Language"}
        ]

        fallback_module = ast.Module(
            body=fallback_class_nodes,
            type_ignores=[],
        )

        namespace = {}
        compiled = compile(
            fallback_module,
            filename=str(source_path),
            mode="exec",
        )
        exec(compiled, namespace)

        builder = namespace["LanguageDetectorBuilder"]
        detector = builder.from_languages("en", "fr")

        assert isinstance(detector, builder)
        assert detector.build() is None