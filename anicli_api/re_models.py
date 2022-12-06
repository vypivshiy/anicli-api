"""
Experimental regex parser classes

It was written to convert the results to the desired values through classes without additional logic.

For examples, see examples.example_re_models.py file
"""
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
    """
    Base regex parser class

    How it works:

        - Set re.Pattern, and key name.

        **Priority of transformations by functions, after finding result by regular expressions:**

        - If regexp found nothing, it returns  {name: default}

        **Else:**

        -  **before_func** param, if set

        - **before_func_call method**, if defined

        - **result_type** type (default str)

        - **after_func_call method**, if defined

        - **after_func param**, if set

        - return {name: result}
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
        """
        :param pattern: re.Pattern or regex string
        :param name: name key. Default, try get groupname from pattern
        :param default: default value, if pattern found nothing. Default None
        :param type: convert type founded value. Default str
        :param before_exec_type: function or dict with function exec before set type
        :param after_exec_type: function or dict with function exec after set type
        """
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
        """parse value and convert by the rules"""
        ...

    def parse_values(self, text: str) -> List[Any]:
        """return list of values, without key

        :param text: target text
        :return: list of values
        """
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
    def parse(self, text: str) -> Dict[str, Any]:
        """Returns the first matched result found by the regular expression

        :param text: text target
        :return: dict {name: result or default value}
        """
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
        """Returns a list of all found results

        :param pattern: re.Pattern or regex string
        :param name: key, string
        :param default: default value. Default - empty list []
        :param type: convert type all founded values. Default str
        :param before_exec_type: function or dict with function exec before set type
        :param after_exec_type: function or dict with function exec after set type
        """
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
        """Returns a list of all found results

        :param text: text target
        :return: dict {key: [val_1, val_2 ..., val_n] or {key: default}
        """
        if not (result := self.pattern.findall(text)):
            return {self.name: self.default}  # type: ignore
        for i, el in enumerate(result):
            el = self._enchant_value("", el)
            result[i] = el
        return {self.name: result}


class ReFieldListDict(ReBaseField):
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
        """Returns a list of dictionaries of found expressions

        :param pattern: re.Pattern or regex string. REGEX REQUIRED GROUPS INDEXES
        :param name: key, string
        :param default: default value. Default - empty list []
        :param type: convert type all founded values. Default str
        :param before_exec_type: dict of function {groupname1: func, groupname2: func...} exec before set type
        :param after_exec_type: dict of function {groupname1: func, groupname2: func...} exec before set type
        """
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
        """

        :param text: target text
        :return: dict {name: [{groupname_1: val_1, group_name_2: val_2...}, {groupname_1: val_3, group_name_2: val_4...}...]}
        """
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
