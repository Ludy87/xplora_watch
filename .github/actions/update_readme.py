"""update countries.md file."""
import json

with open("countries.md", "w", encoding="utf8") as text_file:
    text_file.write("| country name | country code |\n")
    text_file.write("|--------------|--------------|\n")
    with open(".github/actions/country.json", encoding="utf8") as json_file:
        countries = json.loads(json_file.read())
        text_file.writelines(f"| {country['name']} | {country['code']} |\n" for country in countries)
