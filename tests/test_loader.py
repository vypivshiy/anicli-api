import pytest

from anicli_api.loader import ExtractorLoader
from tests.fixtures.mock_loader import mock_loader

FAKE_WRONG_EXTRACTOR = "tests.fixtures.fake_extractor_bad"


@pytest.mark.parametrize(
    "module",
    [
        "math",
        "urllib",
        "json",
        "csv",
        FAKE_WRONG_EXTRACTOR,
        "anicli_api.base",
        "anicli_api.__template_extractor__",
    ],
)
def test_wrong_load_extractor(module: str):
    with pytest.raises(AttributeError):
        ExtractorLoader.load(module_name=module)


@pytest.mark.parametrize(
    "module",
    [
        "extractors.123foobarbaz",
        "extractors.__foooooooooooo",
        "extractors._asd12f3gsdfg23",
        "why what",
    ],
)
def test_not_exist_load_extractor(module: str):
    with pytest.raises(ModuleNotFoundError):
        ExtractorLoader.load(module_name=module)


@pytest.mark.parametrize(
    "module",
    [
        "anicli_api.extractors.animego.py",
        "anicli_api.extractors.animego",
        "tests.fixtures.fake_extractor",
    ],
)
def test_success_import_extractor(module):
    ExtractorLoader.load(module_name=module)


def test_extractor_tester():
    ExtractorLoader.run_test("tests.fixtures.fake_extractor")


def test_all_extractor_loader(mock_loader):
    mock_loader.run_test_all()
