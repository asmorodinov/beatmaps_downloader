import os
import json
import hashlib
import zipfile
import argparse
import time
import re
import requests
from ossapi import Ossapi


def load_secrets(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def get_md5(data):
    return hashlib.md5(data).hexdigest()


def extract_version_from_osu(text):
    match = re.search(r'^Version:(.*)$', text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    else:
        return None


def download_beatmapset(set_id, session_token, save_path, no_video):
    url = f"https://osu.ppy.sh/beatmapsets/{set_id}/download"

    if no_video:
        url += "?noVideo=1"

    session = requests.Session()
    session.cookies.set("osu_session", session_token, domain="osu.ppy.sh")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        'Referer': f'https://osu.ppy.sh/beatmapsets/{set_id}',
    }

    try:
        response = session.get(url, stream=True, headers=headers)

        if "text/html" in response.headers.get('Content-Type', ''):
            return False

        if response.status_code == 429:
            print("Got too many requests error, let's stop for now")
            exit(1)

        response.raise_for_status()

        if response.status_code == 200:
            temp_path = save_path + ".tmp"

            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    f.write(chunk)

            if os.path.exists(save_path):
                os.remove(save_path)
            os.rename(temp_path, save_path)

            return True
    except Exception as e:
        print(f"Got exception for beatmapset {set_id}: {e}")
        pass

    return False


def check_beatmapset_integrity(api, file_path, set_id):
    try:
        remote_set = api.beatmapset(set_id)
        # Map remote versions to their checksums: { "Insane": "md5..." }
        remote_map = {bm.version: bm.checksum for bm in remote_set.beatmaps}

        with zipfile.ZipFile(file_path, 'r') as z:
            # We use a dictionary of original filenames for case-sensitive lookup
            # Path separators are normalized to '/' as per ZIP standard
            files_in_zip = {info.filename.replace('\\', '/'): info for info in z.infolist()}

            local_osu_files = [f for f in z.namelist() if f.endswith('.osu')]
            if not local_osu_files:
                return False, "No .osu files in archive"

            local_versions_found = {}

            for osu_filename in local_osu_files:
                with z.open(osu_filename) as f:
                    content_bytes = f.read()
                    content_text = content_bytes.decode('utf-8')

                    # 1. MD5 Integrity Check
                    local_ver = extract_version_from_osu(content_text)
                    local_hash = get_md5(content_bytes)

                    if not local_ver:
                        return False, f"Could not find Version line in {osu_filename}"
                    if local_ver not in remote_map:
                        return False, f"Extra/Unknown version: [{local_ver}]"
                    if local_hash != remote_map[local_ver]:
                        return False, f"Hash mismatch for version: [{local_ver}]"

                    # Helper to check asset existence (CASE SENSITIVE) and size
                    def verify_asset(filename, asset_type):
                        if not filename:
                            return False, "Empty filename"

                        # Remove quotes and normalize slashes, but KEEP CASE
                        clean_name = filename.strip('"').strip().replace('\\', '/')

                        # Strict case-sensitive check
                        if clean_name not in files_in_zip:
                            return False, f"Missing {asset_type} (Case Sensitive): {clean_name}"

                        # Check for 0-byte files
                        if files_in_zip[clean_name].file_size == 0:
                            return False, f"Empty (0 KB) {asset_type}: {clean_name}"

                        return True, ""

                    # 2. Audio Filename Check
                    audio_match = re.search(r'^AudioFilename\s*:\s*(.+)$', content_text, re.MULTILINE)
                    if audio_match:
                        ok, err = verify_asset(audio_match.group(1).strip(), "audio")
                        if not ok:
                            return False, f"{err} (in diff: {local_ver})"

                    # 3. [Events] Section (BG and Video)
                    events_section = re.search(r'\[Events\]\s*(.*?)(?=\n\[|$)', content_text, re.DOTALL)
                    if events_section:
                        events_text = events_section.group(1)

                        # Backgrounds (Type 0)
                        bg_matches = re.findall(r'^0\s*,[^,]+,\s*("[^"]+"|[^",]+)', events_text, re.MULTILINE)
                        for bg in bg_matches:
                            ok, err = verify_asset(bg, "background")
                            if not ok: return False, f"{err} (in diff: {local_ver})"

                        # Videos (Type 1 or Video)
                        vid_matches = re.findall(r'^(?:Video|1)\s*,[^,]+,\s*("[^"]+"|[^",]+)', events_text, re.MULTILINE)
                        for vid in vid_matches:
                            ok, err = verify_asset(vid, "video")
                            if not ok: return False, f"{err} (in diff: {local_ver})"

                    local_versions_found[local_ver] = local_hash

            # Check if any official versions are missing locally
            if len(local_versions_found) != len(remote_map):
                missing = set(remote_map.keys()) - set(local_versions_found.keys())
                return False, f"Missing versions: {list(missing)}"

        return True, "OK"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    parser = argparse.ArgumentParser(description="Osu! Validator")
    parser.add_argument("path", help="Path to beatmaps")
    parser.add_argument("-d", "--download", action="store_true", help="Auto-download")

    parser.add_argument("-s", "--year_start", type=int, help="Start year (inclusive)")
    parser.add_argument("-e", "--year_end", type=int, help="End year (non-inclusive)")
    parser.add_argument("-n", "--no-video", action='store_true', help="don't include video, if set (to save disk space and network bandwidth)")

    args = parser.parse_args()

    keys = load_secrets("secret_keys.json")
    api = Ossapi(keys['client_id'], keys['client_secret'])
    osu_session = open("osu_session.txt", "r").read().strip() if args.download else None

    # Step 1: Collect all files first for progress tracking
    all_files = []
    for entry in os.scandir(args.path):
        if entry.is_dir():
            try:
                folder_year = int(entry.name)

                # Apply year filter
                if args.year_start and folder_year < args.year_start:
                    continue
                if args.year_end and folder_year >= args.year_end:
                    continue

                # Scan .osz files in this folder
                for f in os.listdir(entry.path):
                    if f.endswith(".osz"):
                        try:
                            sid = int(f.split(' ')[0])
                            all_files.append((os.path.join(entry.path, f), sid))
                        except:
                            continue
            except ValueError:
                # Skip folders that are not years
                continue

    total = len(all_files)
    if total == 0:
        print("No files found matching the criteria.")
        return

    invalid_ids = []
    fixed_ids = []
    not_fixed_ids = []
    downloaded_count = 0
    start_time = time.time()

    print(f"Found {total} files. Starting validation...\n")

    try:
        for index, (full_path, set_id) in enumerate(all_files, 1):
            valid, msg = check_beatmapset_integrity(api, full_path, set_id)
            progress = f"[{index}/{total}]"

            if not valid:
                print(f"{progress} INVALID ID {set_id}: {msg}")
                invalid_ids.append(set_id)
                if args.download:
                    if download_beatmapset(set_id, osu_session, full_path, args.no_video):
                        print(f"      [✓] Updated successfully")
                        fixed_ids.append(set_id)
                        downloaded_count += 1
                        time.sleep(1) # Rate limit protection
                    else:
                        not_fixed_ids.append(set_id)
                        print(f"      [X] Failed to update file")
            else:
                print(f"{progress} VALID ID {set_id}")

            time.sleep(0.2) # API breath room

    except KeyboardInterrupt:
        print("Interrupted...")

    # Final Stats
    duration = time.time() - start_time
    with open("invalid_ids.txt", "w") as f:
        f.write("\n".join(map(str, invalid_ids)))

    with open("fixed_ids.txt", "w") as f:
        f.write("\n".join(map(str, fixed_ids)))

    with open("not_fixed_ids.txt", "w") as f:
        f.write("\n".join(map(str, not_fixed_ids)))

    print("\n" + "="*30)
    print("FINAL STATISTICS")
    print("="*30)
    print(f"Total processed: {index}")
    print(f"Invalid found:   {len(invalid_ids)}")
    if args.download:
        print(f"Updated:         {downloaded_count}")
        print(f"Failed to DL:    {len(invalid_ids) - downloaded_count}")
    print(f"Time taken:      {duration/60:.1f} minutes")
    print(f"Invalid IDs saved to: invalid_ids.txt")

if __name__ == "__main__":
    main()