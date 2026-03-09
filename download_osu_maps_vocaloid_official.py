import argparse
import requests
import re
import pandas as pd
import zipfile
import io
import sys
import random
from pathlib import Path
from time import sleep


too_many_requests_counter = 0.0
too_many_requests_limit = 2

failed_maps_counter = 0.0
failed_maps_limit = 3

html_response_counter = 0.0
html_response_limit = 2

SLEEP_TIME_IN_CASE_OF_BLOCK = 60 * 60  # one hour

session = requests.Session()
osu_session_cookie = open("osu_session.txt", "r").read().strip()
session.cookies.set("osu_session", osu_session_cookie, domain="osu.ppy.sh")


def sleep_with_countdown(total_amount, interval):
    slept = 0

    while slept < total_amount:
        percentage = 100 * (slept / total_amount)

        time_left = total_amount - slept
        time_to_sleep = min(time_left, interval)

        print(f"Sleep progress: {percentage:.2f}%, time left: {time_left}s", end='\r')
        sleep(time_to_sleep)
        slept += time_to_sleep

    print("Waking up from sleep")


def get_with_retry(beatmapset_id, no_video, num_retries=7):
    global too_many_requests_counter
    global html_response_counter
    global session

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        'Referer': f'https://osu.ppy.sh/beatmapsets/{beatmapset_id}',
    }

    url = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}/download"
    if no_video:
        url += "?noVideo=1"

    for i in range(num_retries):
        print(f"\tRequested {url}")

        response = session.get(url, headers=headers)

        sleep_time = int(30 * (2 ** i) * (0.5 + random.random()))

        if "text/html" in response.headers.get('Content-Type', ''):
            html_response_counter += 1

            if html_response_counter > html_response_limit:
                # add extra randomized sleep time just in case (2.5 - 7.5 minutes, 5 minutes on average)
                current_sleep_time = SLEEP_TIME_IN_CASE_OF_BLOCK + int(5 * 60 * (0.5 + random.random()))

                print(f"Going to sleep for {current_sleep_time}s, since it looks like we are getting blocked right now (got html instead of .osz)", file=sys.stderr)
                sleep_with_countdown(current_sleep_time, 15)
                continue

            content = response.content
            with open("response.html", "wb") as file:
                file.write(content)

            print(f"\tGot html instead of .osz, let's sleep for {sleep_time}s and then retry")
            sleep(sleep_time)
            continue
        elif response.status_code == 200:
            html_response_counter *= 0.95  # lower the counter a little bit, but don't fully reset it

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

        if response.status_code == 429:
            too_many_requests_counter += 1
            if too_many_requests_counter > too_many_requests_limit:
                # add extra randomized sleep time just in case (2.5 - 7.5 minutes, 5 minutes on average)
                current_sleep_time = SLEEP_TIME_IN_CASE_OF_BLOCK + int(5 * 60 * (0.5 + random.random()))

                print(f"Going to sleep for {current_sleep_time}s, since it looks like we are getting blocked right now (got 429 error code)", file=sys.stderr)
                sleep_with_countdown(current_sleep_time, 15)
                continue
        elif response.status_code == 200:
            too_many_requests_counter *= 0.95  # lower the counter a little bit, but don't fully reset it

        if response.status_code in retriable_error_codes:
            print(f"\tGot error code {response.status_code} while requesting url {url}, going to sleep for {sleep_time}s and then retry", file=sys.stderr)
            sleep(sleep_time)
            continue
        elif response.status_code in non_retriable_error_codes:
            # does not make sense to retry
            print(f"\tGot error code {response.status_code} while requesting url {url}", file=sys.stderr)
            return None
        else:
            response.raise_for_status()
            return response

    print(f"\tStill got an error while requesting url {url}, even after {num_retries} attempts", file=sys.stderr)
    return None


def sanitize_name(name):
    # Replace forbidden characters with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def process_and_save(content, beatmap_id, year, directory, history_file):
    try:
        # Treat content as zip and find first .osu file
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            osu_files = sorted([f for f in z.namelist() if f.endswith(".osu")])
            if not osu_files:
                print(f"Failed parsing beatmap {beatmap_id} as zip archive, no .osu files found inside", file=sys.stderr)
                return False, False, False

            with z.open(osu_files[0]) as f:
                text = f.read().decode('utf-8', errors='ignore')

            title_m = re.search(r"^Title:(.*)$", text, re.MULTILINE)
            artist_m = re.search(r"^Artist:(.*)$", text, re.MULTILINE)

            orig_title = title_m.group(1).strip() if title_m else "Unknown Title"
            orig_artist = artist_m.group(1).strip() if artist_m else "Unknown Artist"

        # Check for invalid characters
        forbidden_pattern = r'[<>:"/\\|?*]'
        has_invalid = bool(re.search(forbidden_pattern, f"{orig_artist}{orig_title}"))

        if has_invalid:
            print(f"Beatmap {beatmap_id} has name which contains forbidden characters, going to sanitize it", file=sys.stderr)

        # Sanitize
        sanitized_title = sanitize_name(orig_title)
        sanitized_artist = sanitize_name(orig_artist)

        # Handle Duplicates and Save
        year_dir = Path(directory) / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{beatmap_id} {sanitized_artist} - {sanitized_title}"
        final_name = f"{base_name}.osz"

        # Increment suffix if filename exists
        counter = 1
        is_duplicate = False
        while (year_dir / final_name).exists():
            is_duplicate = True
            final_name = f"{base_name}_{counter}.osz"
            counter += 1

        with open(year_dir / final_name, "wb") as f:
            f.write(content)

        print(f"Saved beatmap as \"{final_name}\"")

        # History Record
        with open(history_file, "a", encoding="utf-8") as h:
            # Note: this is not the actual file name, it has original artist and title, not sanitized
            h.write(f"{beatmap_id} {orig_artist} - {orig_title}\n")

        return True, is_duplicate, has_invalid
    except Exception as e:
        print(f"Failed parsing beatmap {beatmap_id} as zip archive, got error: {e}", file=sys.stderr)
        return False, False, False


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

    print(f"Year {year}: parsed {len(maps)} maps")
    return maps


def parse_history_file(path):
    downloaded_ids = set()

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if " " in line:
                    downloaded_ids.add(line.split(" ")[0].strip())

    return downloaded_ids


def download_map(beatmap, delay, no_video):
    try:
        print(f"Downloading {beatmap}")

        # sleep before downloading to avoid "429 too many requests" errors
        # Note: osu actually has an hourly based limit, not a limit per minute, or per second
        # Note: osu!supporters have more lenient download limits
        sleep(delay)

        response = get_with_retry(beatmap, no_video)

        if response is None:
            print(f"Failed to download {beatmap}", file=sys.stderr)
            return None

        result = response.content

        print(f"Downloaded {beatmap}")
        return result

    except Exception as e:
        print(f"Error occured while downloading beatmap {beatmap}: {e}", file=sys.stderr)
        return None


def download_maps(download_directory, html_directory, year_start=2008, year_end=2026, filter_mode="STD", delay=5, no_video=False):
    global failed_maps_counter

    total_maps = 0
    downloaded_maps = 0
    already_downloaded = 0
    failed_to_download = []
    duplicate_maps = 0
    has_invalid_chars_maps = 0

    maps = {}

    for year in range(year_start, year_end):
        maps[year] = parse_maps_from_html(html_directory, year, filter_mode)
        total_maps += len(maps[year])

    try:
        print(f"Total maps: {total_maps}")
        input("Start download? (press any key to continue, or Ctrl+C to cancel)")

        Path(download_directory).mkdir(parents=True, exist_ok=True)

        for year, year_maps in maps.items():
            history_file_path = Path(download_directory) / f"{year}_downloaded_maps.txt"
            downloaded_ids = parse_history_file(history_file_path)

            for beatmap in year_maps:
                if beatmap in downloaded_ids:
                    print(f"{beatmap} was already downloaded, skip download")
                    downloaded_maps += 1
                    already_downloaded += 1
                    downloaded_ids.add(beatmap)
                else:
                    map_failed = False

                    content = download_map(beatmap, delay, no_video)

                    if content is None:
                        map_failed = True
                    else:
                        ok, is_dup, has_invalid = process_and_save(content, beatmap, year, download_directory, history_file_path)
                        if ok:
                            downloaded_maps += 1
                            downloaded_ids.add(beatmap)

                        map_failed = not ok

                        if is_dup:
                            duplicate_maps += 1

                        if has_invalid:
                            has_invalid_chars_maps += 1

                    if map_failed:
                        failed_to_download.append(beatmap)
                        failed_maps_counter += 1
                    else:
                        failed_maps_counter *= 0.95  # lower the counter a little bit, but don't fully reset it

                    if failed_maps_counter > failed_maps_limit:
                        print("Too many maps are failing to download, suspecting some captcha errors, or server is unavailable", file=sys.stderr)

                        print("Failed to download following maps:", file=sys.stderr)
                        print(*failed_to_download, sep="\n", file=sys.stderr)
                        exit(3)

                failed_maps = len(failed_to_download)
                percentage = "{:.2f}%".format((downloaded_maps + failed_maps) * 100 / total_maps)

                print(f"Year {year}, current progress: {percentage} (downloaded maps: {downloaded_maps}, failed maps: {failed_maps}, downloaded + failed: {downloaded_maps + failed_maps}, total_maps: {total_maps})")
    except KeyboardInterrupt:
        print("\nInterrupted...")

    # Final Statistics
    print("\n" + "="*30)
    print("Execution Summary:")
    print(f"Successfully downloaded: {downloaded_maps}")
    print(f"Skipped (already in history): {already_downloaded}")
    print(f"Filename duplicates handled: {duplicate_maps}")
    print(f"Maps with invalid characters in metadata replaced: {has_invalid_chars_maps}")

    print(f"Total failed: {len(failed_to_download)}")

    if failed_to_download:
        print("Failed to download following maps:", file=sys.stderr)
        print(*failed_to_download, sep="\n", file=sys.stderr)
        exit(4)


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
