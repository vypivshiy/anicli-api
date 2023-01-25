"""Dynamic import extractor form **anicli_api/extractors** directory"""

import importlib
import logging
import pathlib
from abc import ABC, abstractmethod
from typing import Protocol, Type, cast

from anicli_api.base import *

logger = logging.getLogger("anicli-api.loader")

__all__ = (
    "ModuleExtractor",
    "BaseExtractorLoader",
    "ExtractorLoader",
)

# check Extractor signature
VALID_CLASSES = (
    "Extractor",
    "SearchResult",
    "Ongoing",
    "AnimeInfo",
    "Episode",
    "Video",
    "TestCollections",
)


class ModuleExtractor(Protocol):
    """Protocol typehint for dynamic import extractor"""

    Extractor: Type[BaseAnimeExtractor]
    SearchResult: Type[BaseSearchResult]
    Ongoing: Type[BaseOngoing]
    AnimeInfo: Type[BaseAnimeInfo]
    Episode: Type[BaseEpisode]
    Video: Type[BaseVideo]
    TestCollections: Type[BaseTestCollections]


class BaseExtractorLoader(ABC):
    @classmethod
    @abstractmethod
    def load(cls, *, module_name: str):
        ...


class ExtractorLoader(BaseExtractorLoader):
    """Dynamic loader extractor modules

    Modules must match the template extractors.__template__.py
    """

    @staticmethod
    def _extractor_path() -> str:
        if __name__ == "__main__":
            logger.debug("Load from `extractors` path")
            return "extractors"
        logger.debug("Load from `anicli_api.extractors` path")
        return "anicli_api.extractors"

    @staticmethod
    def _validate(extractor: ModuleExtractor, module_name: str):
        logger.debug("Validate %s %s", extractor, module_name)
        for cls in ModuleExtractor.__dict__["__annotations__"].keys():
            try:
                getattr(extractor, cls)
            except AttributeError as exc:
                logger.error(exc)
                raise AttributeError(
                    f"Module '{module_name}' has no class '{cls}'. It's a real Extractor?"
                ) from exc

    @staticmethod
    def _import(module_name: str) -> ModuleExtractor:
        try:
            module = importlib.import_module(module_name, package=None)
            extractor = cast(ModuleExtractor, module)
        except ModuleNotFoundError as e:
            logger.error(e)
            raise ModuleNotFoundError(f"'{module_name}' not found") from e
        return extractor

    @classmethod
    def get_extractors_names(cls) -> List[str]:
        extractors_path = cls._extractor_path()
        return [
            str(file).replace(".py", "").replace("/", ".").replace("\\", ".")
            for file in pathlib.Path(extractors_path).iterdir()
            if file.name.endswith(".py") and cls._check_module_name(file.name.replace(".py", ""))
        ]

    @classmethod
    def load(cls, module_name: str) -> ModuleExtractor:
        """import module extractor

        - Throw ModuleNotFoundError exception, if module not found
        - Throw AttributeError exception, if module is a not valid extractor


        :param module_name: module path
        :return: ModuleExtractor
        :raise: ModuleNotFoundError - module not found; AttributeError - is a not extractor
        """
        if module_name.endswith(".py"):
            module_name = module_name.replace(".py", "")

        if cls._check_module_name(module_name):
            module = cls._import(module_name)
            cls._validate(module, module_name)
            return module

        # try import. If error with module_name, throw ModuleNotFoundError
        cls._import(module_name)
        raise AttributeError(f"'{module_name}' is not Extractor")

    @classmethod
    def load_all(cls) -> List[ModuleExtractor]:
        """import **all** extractors from anicli_api/extractors directory

        :return: List[ModuleExtractor]
        """
        modules = []
        for module_name in cls.get_extractors_names():
            module = cls.load(module_name)
            modules.append(module)
        return modules

    @staticmethod
    def _check_module_name(module: str) -> bool:
        return not module.startswith("_") and not module.endswith("_") and module != "base"

    @staticmethod
    def _test_module(module: ModuleExtractor, throw_exception: bool = True) -> None:
        test_class = module.TestCollections
        for attr in test_class.__dict__.keys():
            if attr.startswith("test"):
                logger.debug("MODULE %s RUN %s", module.__str__().split("/")[-1], attr)
                try:
                    getattr(test_class(), attr)()
                except AssertionError as e:
                    if throw_exception:
                        raise e
                    else:
                        logger.error(e)
                else:
                    logger.debug("[OK] %s %s", module.__str__().split("/")[-1], attr)

    @classmethod
    def run_test(cls, module_name: str, *, throw_exception: bool = True) -> None:
        """run TestCollections class in extractors

        :param module_name: extractor path
        :param throw_exception: Throw exception, if test failed. If flag is False, print logging.error message
        :return:
        """
        logger.info("load %s extractor, throw_exception=%s", module_name, throw_exception)
        module = cls.load(module_name)
        cls._test_module(module, throw_exception)

    @classmethod
    def run_test_all(cls, *, throw_exception: bool = True) -> None:
        """run TestCollections in all extractors from anicli_api/extractors directory

        :param throw_exception: Throw exception, if test failed. If flag is False, print logging.error message
        :return:
        """
        logger.info("load full test extractors, throw_exception=%s", throw_exception)
        for module in cls.load_all():
            cls._test_module(module, throw_exception)
