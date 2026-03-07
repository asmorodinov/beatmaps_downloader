import argparse
import requests
import re

import pandas as pd

from pathlib import Path
from time import sleep


MIRRORS = [
    ("https://catboy.best/d/{}", "https://catboy.best/d/{}n"),
    ("https://beatconnect.io/b/{}", "https://beatconnect.io/b/{}/?novideo=1"),
]


def get_with_retry(url, num_retries=7):
    for i in range(num_retries):
        print(f"\trequested {url}")
        response = requests.get(url)

        retriable_error_codes = [
            408,  # request timeout
            429,  # too many requests
            500,  # internal server error
            502,  # bad gateway
            503,  # service unavailable
            504,  # gateway timeout
        ]
        
        non_retriable_error_codes = [
            400,  # bad request
            401,  # unauthorized
            403,  # forbidden
            404,  # not found
            405,  # method not allowed
            409,  # conflict
            422,  # unprocessable entity
        ]

        if response.status_code in retriable_error_codes:
            print(f"\tgot error code {response.status_code} while requesting url {url}, going to sleep for {2 ** i}s and then retry")
            sleep(2 ** i)
            continue
        elif response.status_code in non_retriable_error_codes:
            # does not make sense to retry
            print(f"\tgot error code {response.status_code} while requesting url {url}")
            return None
        else:
            response.raise_for_status()
            return response


def download_map(directory, year, beatmap, delay, no_video):
    path = Path(directory) / f"{year}_{beatmap}.osz"

    if path.is_file():
        # file was already downloaded previously => skip download
        print(f"{beatmap} was already downloaded, skip download")
        return True

    print(f"downloading {beatmap}")

    # sleep before downloading to avoid "429 too many requests" errors
    sleep(delay)

    for mirror, mirror_no_video in MIRRORS:
        if no_video:
            selected_mirror = mirror_no_video
        else:
            selected_mirror = mirror

        response = get_with_retry(selected_mirror.format(beatmap))

        if response is None:
            if (mirror, mirror_no_video) == MIRRORS[-1]:
                print(f"failed to download {beatmap}") # this was the last mirror available
            else:
                print(f"\tfailed to download {beatmap}, going to try another mirror")
        else:
            break

    if response is None:
        return False

    try:
        with path.open("wb") as f:
            for buff in response:
                f.write(buff)
    except KeyboardInterrupt:
        print(f"removing partially written file {path}")
        path.unlink()
        exit(1)

    print(f"downloaded {beatmap}")
    return True


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


def download_maps(download_directory, html_directory, year_start=2008, year_end=2026, filter_mode="STD", delay=5, no_video=False):
    total_maps = 0
    downloaded_maps = 0
    failed_maps = 0

    maps = {}

    failed_to_download = []

    for year in range(year_start, year_end):
        maps[year] = parse_maps_from_html(html_directory, year, filter_mode)
        total_maps += len(maps[year])

    for year, year_maps in maps.items():
        for beatmap in year_maps:
            if download_map(download_directory, year, beatmap, delay, no_video):
                downloaded_maps += 1
            else:
                failed_to_download.append(beatmap)
                failed_maps += 1

            percentage = "{:.2f}%".format((downloaded_maps + failed_maps) * 100 / total_maps)

            print(f"current progress: {percentage} (downloaded maps: {downloaded_maps}, failed maps: {failed_maps}, downloaded + failed: {downloaded_maps + failed_maps}, total_maps: {total_maps})")

    if failed_to_download:
        print("failed to download followings maps:")
        print(*failed_to_download, sep="\n")
        exit(2)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("download_directory")
    parser.add_argument("html_directory")
    parser.add_argument("-s", "--year_start", type=int, default=2008, help="start year (inclusive)")
    parser.add_argument("-e", "--year_end", type=int, default=2026, help="end year (non-inclusive)")
    parser.add_argument("-f", "--filter_mode", type=str, choices=["STD", "TAIKO", "MANIA", "CATCH"], default="STD", help="filter game mode")
    parser.add_argument("-d", "--delay", type=int, default=5, help="delay between iterations (to not get ip blocked)")
    parser.add_argument("-n", "--no-video", action='store_true', help="don't include video, if set (to save disk space and network bandwidth)")

    args = parser.parse_args()

    download_maps(**vars(args))


if __name__ == "__main__":
    main()
