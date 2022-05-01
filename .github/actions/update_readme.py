import json

with open("countries.md", "w") as text_file:
    text_file.write("| country name | country code |\n")
    text_file.write("|--------------|--------------|\n")
    with open(".github/actions/country.json", "r") as json_file:
        countries = json.loads(json_file.read())
        for country in countries:
            text_file.write(f"| {country['name']} | {country['code']} |\n")
