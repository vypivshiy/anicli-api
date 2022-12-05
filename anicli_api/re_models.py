from __future__ import annotations

import builtins
import re
from abc import abstractmethod
from typing import Any, AnyStr, Callable, Dict, Iterable, List, Optional, Pattern, Type, Union

T_BEFORE_EXEC = Union[Callable[[str], str], Dict[str, Callable[[str], str]]]
T_AFTER_EXEC = Union[Callable[[Any], Any], Dict[str, Callable[[Any], Any]]]

__all__ = (
    "ReBaseField",
    "ReField",
    "ReFieldList",
    "ReFieldListDict",
    "parse_many",
)


class ReBaseField:
    """Базовый класс парсера регулярных выражений с конвертацией в словарь

    Базовый принцип работы:
        1. Установить re.Pattern, и имя ключа нового аргумента.

        2. Приоритет преобразований функциями, после нахождения регулярными выражениями result:

        2.1 Если регулярное выражение ничего не нашло, вернёт  {name: default} словарь

        2.2  before_func параметр, если передан

        2.3  before_func_call метод, если объявлен

        2.4 result_type тип (по умолчанию str)

        2.5 after_func_call метод, если объявлен

        2.6 after_func attr, если передан

        3. вернуть {name: result}
    """

    def __init__(
        self,
        pattern: Union[Pattern, AnyStr],
        *,
        name: Optional[str] = None,
        default: Optional[Any] = None,
        type: Type = str,
        before_exec_type: Optional[T_BEFORE_EXEC] = None,
        after_exec_type: Optional[T_AFTER_EXEC] = None,
    ) -> None:
        self.pattern = pattern if isinstance(pattern, Pattern) else re.compile(pattern)

        self.name = self._set_name(name)

        self.result_type = type
        self.before_func = before_exec_type
        self.after_func = after_exec_type
        self.default = default
        self.value = None

    def _set_name(self, name):
        if not name and len(self.pattern.groupindex) > 0:
            return ",".join(self.pattern.groupindex)
        else:
            return name

    @staticmethod
    def _init_lambda_function(
        *,
        value: Any,
        # {"group_name or name": func, ...} or func
        func: Optional[Union[T_BEFORE_EXEC, T_AFTER_EXEC]] = None,
        key: str = "",
    ) -> Any:
        if func:
            if isinstance(func, dict) and func.get(key):
                if not callable(func.get(key)):
                    raise TypeError(f"{func.get(key)} must be callable")
                value = func.get(key)(value)  # type: ignore
            elif callable(func):
                value = func(value)
        return value

    def _enchant_value(self, key: str, value: Any):
        value = self._init_lambda_function(func=self.before_func, key=key, value=value)
        if val := self.before_exec_func_call(key=key, value=value):
            value = val
        value = self._set_type(value)
        if val := self.after_exec_func_call(key=key, value=value):
            value = val
        value = self._init_lambda_function(func=self.after_func, key=key, value=value)
        return value

    @abstractmethod
    def parse(self, text: str) -> Dict[str, Any]:
        ...

    def parse_values(self, text: str) -> List[Any]:
        rez = []
        for val in self.parse(text).values():
            rez.extend(val) if isinstance(val, List) else rez.append(val)

        return rez

    def before_exec_func_call(self, key: str, value: Any):
        ...

    def after_exec_func_call(self, key: str, value: Any):
        ...

    def _set_type(self, value: Any) -> Type[Any]:
        return self.result_type(value)

    def __repr__(self):
        return (
            f"[{self.__class__.__name__}] type={self.result_type} pattern={self.pattern} "
            f"{{{self.name}: {self.value}}}"
        )


class ReField(ReBaseField):
    """Возвращает первый найденный результат, найденный регулярным выражением"""

    def parse(self, text: str) -> Dict[str, Any]:
        if not (result := self.pattern.search(text)):
            if isinstance(self.default, Iterable) and not isinstance(
                self.default, str
            ):  # string is iterable
                return dict(zip(self.name.split(","), self.default))
            else:
                return {self.name: self.default}
        elif result and self.pattern.groupindex:
            rez = result.groupdict()
        elif result:
            rez = dict(zip(self.name.split(","), result.groups()))
        else:
            raise TypeError("Missing name attribute. Add param name or set groupname in pattern")
        for k in rez.keys():
            rez[k] = self._enchant_value(key=k, value=rez[k])
        return rez


class ReFieldList(ReBaseField):
    """Возвращает список всех найденных результатов"""

    def __init__(
        self,
        pattern: Union[Pattern, AnyStr],
        *,
        name: str,
        default: Optional[Iterable[Any]] = None,
        type: Type = str,
        before_exec_type: Optional[Callable] = None,
        after_exec_type: Optional[Callable] = None,
    ) -> None:
        if not default:
            default = []

        if not isinstance(default, Iterable) and not isinstance(default, str):
            raise TypeError(
                f"{self.__class__.__name__} default param must be iterable not {builtins.type(default).__name__}"
            )

        if not isinstance(default, list):
            default = list(default)

        super().__init__(
            pattern,
            name=name,
            default=default,
            type=type,
            before_exec_type=before_exec_type,
            after_exec_type=after_exec_type,
        )

    def parse(self, text: str) -> Dict[str, List]:
        if not (result := self.pattern.findall(text)):
            return {self.name: self.default}  # type: ignore
        for i, el in enumerate(result):
            el = self._enchant_value("", el)
            result[i] = el
        return {self.name: result}


class ReFieldListDict(ReBaseField):
    """Возвращает список словарей найденных выражений"""

    def __init__(
        self,
        pattern: Union[Pattern, AnyStr],
        *,
        name: str,
        default: Optional[Iterable[Any]] = None,
        type: Type = str,
        before_exec_type: Optional[Dict[str, Callable]] = None,
        after_exec_type: Optional[Dict[str, Callable]] = None,
    ) -> None:

        if not default:
            default = []

        if not isinstance(default, Iterable) and not isinstance(default, str):
            raise TypeError(
                f"{self.__class__.__name__} default param must be iterable, not {builtins.type(default)}"
            )

        if not isinstance(default, list):
            default = list(default)

        super().__init__(
            pattern,
            name=name,
            default=default,
            type=type,
            before_exec_type=before_exec_type,
            after_exec_type=after_exec_type,
        )

    def parse(self, text: str) -> Dict[str, List[Any]]:
        if not self.pattern.search(text):
            return {self.name: self.default}  # type: ignore
        if not self.pattern.groupindex:
            raise TypeError("Missing pattern.groupindex value")
        values = []
        for result in self.pattern.finditer(text):
            rez = result.groupdict()
            for k in rez.keys():
                rez[k] = self._enchant_value(k, rez[k])
            values.append(rez)
        return {self.name: values}


def parse_many(text: str, *re_fields: ReBaseField) -> dict[str, Any]:
    """Accumulate all re_fields results to dict

    :param text: target string
    :param re_fields: ReFields classes
    :return: dict with re_fields values
    """
    result = {}
    for re_field in re_fields:
        result.update(re_field.parse(text))
    return result
