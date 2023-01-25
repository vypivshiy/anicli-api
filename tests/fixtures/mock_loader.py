from pathlib import Path

import pytest

from anicli_api.loader import ExtractorLoader


@pytest.fixture
def mock_loader(monkeypatch):
    class FakeLoader(ExtractorLoader):
        @classmethod
        def load_all(cls):
            return [cls.load("tests.fixtures.fake_extractor.py")]

    return FakeLoader
