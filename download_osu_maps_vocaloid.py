import argparse
import requests
import re

import pandas as pd

from pathlib import Path
from time import sleep


# HOW TO RUN:

# 1. Export google sheets table from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/ as html!
#    Note: other options do not work (e.g. csv export), since links are stored in separate hidden tabs (e.g. 2025 data). The only way that worked for me was export as html
# 2. Extract html archive to some folder
# 3. Mofify DIRECTORY and HTML_DIRECTORY below
# 4. Install python (if not already installed)
# 5. Install pandas and requests (if not already installed): `pip3 install pandas requests`
# 6. Run the script: `python3 download_osu_maps_vocaloid.py {path to download maps to} {path to extracted html files} {other options, use --help for more info}`
#    e.g. `python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2008 -e 2026 -f STD``

# NOTES:
# - You can stop the script via Ctrl+C and continue it later
# -


# only retries 500 error codes
def get_with_retry(url, num_retries=10):
    for i in range(num_retries):
        response = requests.get(url)

        if response.status_code == 500:
            print(f"got error code {response.status_code} while requesting url {url}, going to sleep for 1s and then retry")
            sleep(1)
            continue
        else:
            response.raise_for_status()
            return response


def download_map(directory, year, beatmap):
    path = Path(directory) / f"{year}_{beatmap}.osz"

    if path.is_file():
        # file was already downloaded previously => skip download
        print(f"{beatmap} was already downloaded, skip download")
        return

    print(f"downloading {beatmap}")

    response = get_with_retry(f"https://beatconnect.io/b/{beatmap}")

    try:
        with path.open("wb") as f:
            for buff in response:
                f.write(buff)
    except KeyboardInterrupt:
        print(f"removing partially written file {path}")
        path.unlink()
        exit(1)

    print(f"downloaded {beatmap}")


def parse_maps_from_html(directory, year, filter_mode="STD"):
    path = f"{directory}/{year} data.html"

    maps = []

    with open(path, 'r') as f:
        df = pd.read_html(f, skiprows=1)[0]

        for row in df.itertuples(index=False):
            link = row.LINK
            mode = row.MODE

            if link is None or mode != filter_mode:
                continue

            match = re.search("https://osu.ppy.sh/s/([0-9]+)", link)
            assert match is not None

            maps.append(match.group(1))

    print(f"year {year}: parsed {len(maps)} maps")
    return maps


def download_maps(download_directory, html_directory, year_start=2008, year_end=2026, filter_mode="STD"):
    total_maps = 0
    downloaded_maps = 0
    maps = {}

    for year in range(year_start, year_end):
        maps[year] = parse_maps_from_html(html_directory, year, filter_mode)
        total_maps += len(maps[year])

    for year, year_maps in maps.items():
        for beatmap in year_maps:
            download_map(download_directory, year, beatmap)
            downloaded_maps += 1

            percentage = "{:.2f}%".format(downloaded_maps * 100 / total_maps)

            print(f"current progress: {percentage} ({downloaded_maps} / {total_maps})")


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("download_directory")
    parser.add_argument("html_directory")
    parser.add_argument("-s", "--year_start", type=int, default=2008, help="start year (inclusive)")
    parser.add_argument("-e", "--year_end", type=int, default=2026, help="end year (non-inclusive)")
    parser.add_argument("-f", "--filter_mode", type=str, choices=["STD", "TAIKO", "MANIA", "CATCH"], default="STD", help="filter game mode")
    args = parser.parse_args()

    download_maps(**vars(args))


if __name__ == "__main__":
    main()
