from anicli_api.re_models import ReField, ReFieldList, ReFieldListDict
"""
HOW TO regex Guides/Lessons, tools

https://regex101.com
https://docs.python.org/3/howto/regex.html

https://www.youtube.com/watch?v=xp1vX15inBg&list=PLyb_C2HpOQSDxe5Y9viJ0JDqGUCetboxB
https://www.youtube.com/watch?v=VU60rEXaOXk&list=PLGKQkV4guDKH1TpfM-FvPGLUyjsPGdXOg

# russian
https://www.youtube.com/watch?v=1SWGdyVwN3E&list=PLA0M1Bcd0w8w8gtWzf9YkfAxFCgDb09pA  
"""

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


if __name__ == '__main__':
    field_1 = ReField(r"(H.*llo w.*rld)",
                      name="hw",
                      default="goodbye world!")

    print(field_1.parse(sample_text))  # {'hw': 'Hello world'}
    print(field_1.parse(sample_text_2))  # {'hw': 'goodbye world!'}

    field_2 = ReFieldList(r"(H.*llo w.*rld)",
                          name="hw_list")
    print(field_2.parse(sample_text))  # {'hw_list': ['Hello world', 'Hiollo wiorld', 'Haaaaaaaaallo woooooorld']}
    print(field_2.parse(sample_text_2))  # {'hw_list': []}

    field_3 = ReFieldListDict(r"var\d=(?P<count>\d+).*// (?P<name>\w+)",
                              name="somethings",
                              after_exec_type={"count": int,
                                               "name": lambda s: s.title()})  # modify after search

    print(field_3.parse(sample_text))
    # {'somethings': [{'count': 100, 'name': 'Cookies'},
    # {'count': 1000, 'name': 'Beer'},
    # {'count': 9102, 'name': 'Smartphone'}]}
    print(field_3.parse_values(sample_text))
    # [{'count': 100, 'name': 'Cookies'},
    # {'count': 1000, 'name': 'Beer'},
    # {'count': 9102, 'name': 'Smartphone'}]

    field_3 = ReFieldListDict(r"var\d=(?P<count>\d+).*// (?P<name>\w+)",
                              name="somethings",
                              after_exec_type={"count": lambda i: int(i)//2,  # div count group to 2
                                               "name": lambda s: f"A half {s.title()}"})  # modify after search
    print(field_3.parse(sample_text))
    # {'somethings': [
    # {'count': 50, 'name': 'A half Cookies'},
    # {'count': 500, 'name': 'A half Beer'},
    # {'count': 4551, 'name': 'A half Smartphone'}]}
