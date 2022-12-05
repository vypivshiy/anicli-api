from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict, parse_many

sample_text = """
Hello world
Hiollo wiorld
Haaaaaaaaallo woooooorld! asasfaassfasfas
Hellollollollo Woorlorlrld
var1=100  // cookies
var2=1000  // beer
var3=9102.000  // smartphone
"""

sample_text_2 = "string with empty regex results"


if __name__ == "__main__":
    field_1 = ReField(
        r"(H.*llo w.*rld)", name="hw", default="goodbye world!"  # brackets required!
    )

    print(field_1.parse(sample_text))  # {'hw': 'Hello world'}
    print(field_1.parse(sample_text_2))  # {'hw': 'goodbye world!'}

    field_10 = ReField(r"(?P<digit>\d+)", type=int)
    print(field_10.parse(sample_text))  # {'digit': 1}
    field_2 = ReFieldList(r"(H.*llo w.*rld)", name="hw_list")
    print(
        field_2.parse(sample_text)
    )  # {'hw_list': ['Hello world', 'Hiollo wiorld', 'Haaaaaaaaallo woooooorld']}
    print(field_2.parse(sample_text_2))  # {'hw_list': []}

    field_3 = ReFieldListDict(
        r"var\d=(?P<count>\d+).*// (?P<name>\w+)",
        name="somethings",
        after_exec_type={"count": int, "name": lambda s: s.title()},
    )  # modify after search

    print(field_3.parse(sample_text))
    # {'somethings': [{'count': 100, 'name': 'Cookies'},
    # {'count': 1000, 'name': 'Beer'},
    # {'count': 9102, 'name': 'Smartphone'}]}
    print(field_3.parse_values(sample_text))  # return list values
    # [{'count': 100, 'name': 'Cookies'},
    # {'count': 1000, 'name': 'Beer'},
    # {'count': 9102, 'name': 'Smartphone'}]

    field_4 = ReFieldListDict(
        r"var\d=(?P<count>\d+).*// (?P<name>\w+)",
        name="somethings_half",
        after_exec_type={
            "count": lambda i: int(i) // 2,  # div count group to 2
            "name": lambda s: f"A half {s.title()}",
        },
    )  # modify after search
    print(field_4.parse(sample_text))
    # {'somethings_half': [
    # {'count': 50, 'name': 'A half Cookies'},
    # {'count': 500, 'name': 'A half Beer'},
    # {'count': 4551, 'name': 'A half Smartphone'}]}

    # concatenate all field results function
    print(parse_many(sample_text, field_1, field_2, field_3, field_4))
    # {'hw': 'Hello world',
    # 'hw_list': ['Hello world', 'Hiollo wiorld', 'Haaaaaaaaallo woooooorld'],
    # 'somethings': [
    # {'count': 100, 'name': 'Cookies'},
    # {'count': 1000, 'name': 'Beer'},
    # {'count': 9102, 'name': 'Smartphone'}],
    # 'somethings_half': [
    # {'count': 50, 'name': 'A half Cookies'},
    # {'count': 500, 'name': 'A half Beer'},
    # {'count': 4551, 'name': 'A half Smartphone'}]}
