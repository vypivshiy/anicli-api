from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from scrape_schema import Parsel


def crop_to_parts(field: "Parsel", text: str) -> List[str]:
    return field.getall().sc_parse(text)
