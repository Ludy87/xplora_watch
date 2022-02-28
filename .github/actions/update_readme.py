import os
from pyxplora_api import pyxplora_api as PXA

country_code = "+49"
phonenumber = os.environ['PHONENUMBER']
password = os.environ['PASSWORD']
userlang = "de-DE"
timezone = "Europe/Berlin"

controller = PXA.PyXploraApi(country_code, phonenumber, password, userlang, timezone)

with open("countries.md", "w") as text_file:
    text_file.write("| country name | country code |\n")
    text_file.write("|--------------|--------------|\n")
    text_file.write("| Denmark | 45 |\n")
    for country in controller.handler.countries()["countries"]:
        text_file.write(f"| {country['name']} | {country['code']} |\n")
