import sys
import json


def main():
    with open("./custom_components/xplora_watch/manifest.json") as json_file:
        data = json.load(json_file)
        print(data['version'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
