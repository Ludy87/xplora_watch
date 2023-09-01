"""Get version from manifest.json file."""
import json
import sys


def main():
    """main."""
    with open("./custom_components/xplora_watch/manifest.json", encoding="utf8") as json_file:
        data = json.load(json_file)
        print(data["version"])  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
