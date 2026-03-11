import os
import re
import zipfile
import argparse
from pathlib import Path

from download_osu_maps_vocaloid import sanitize_name


def get_metadata_from_osz(file_path):
    """
    Extract Artist and Title from the first .osu file found in the zip.
    """
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            osu_files = [f for f in z.namelist() if f.endswith('.osu')]
            if not osu_files:
                return None, None

            # Read the first .osu file to get metadata
            with z.open(osu_files[0]) as f:
                content = f.read().decode('utf-8', errors='ignore')

                # Search for metadata using multiline regex
                title_m = re.search(r"^Title:(.*)$", content, re.MULTILINE)
                artist_m = re.search(r"^Artist:(.*)$", content, re.MULTILINE)

                title = title_m.group(1).strip() if title_m else "Unknown Title"
                artist = artist_m.group(1).strip() if artist_m else "Unknown Artist"

                return artist, title
    except Exception as e:
        print(f"  [!] Error reading: \n{file_path.name} \nDetails: \n{e}")
        return None, None


def get_id_from_record(record):
    """
    Helper to extract the leading integer ID from a history record line.
    """
    try:
        return int(record.split(' ')[0])
    except (ValueError, IndexError):
        return 0


def main():
    parser = argparse.ArgumentParser(description="Osu! Beatmap Renamer & Sanitizer")
    parser.add_argument("path", help="Path to your beatmaps root folder")
    parser.add_argument("-a", "--apply", action="store_true", help="Actually rename files")
    parser.add_argument("-u", "--update-history", action="store_true", help="Update {year}_downloaded_maps.txt")
    parser.add_argument("-s", "--year-start", type=int, help="Filter: Start year")
    parser.add_argument("-e", "--year-end", type=int, help="Filter: End year")
    args = parser.parse_args()

    mode_text = "LIVE RENAME MODE" if args.apply else "DRY RUN MODE"
    print(f"Current Mode: {mode_text}")
    print("="*30)

    # 1. Collect all files first
    files_to_process = []
    print(f"Scanning directory: {args.path}")

    # Structure: { 2021: ["ID Artist - Title", ...], ... }
    history_data = {}

    for entry in os.scandir(args.path):
        if entry.is_dir():
            try:
                folder_year = int(entry.name)
                if args.year_start and folder_year < args.year_start:
                    continue
                if args.year_end and folder_year > args.year_end:
                    continue

                history_data[folder_year] = []

                for filename in os.listdir(entry.path):
                    if not filename.endswith(".osz"):
                        continue

                    match_id = re.match(r'^(\d+)', filename)
                    if not match_id:
                        continue

                    beatmap_id = match_id.group(1)

                    files_to_process.append({
                        "year": folder_year,
                        "filename": filename,
                        "full_path": Path(entry.path) / filename,
                        "beatmap": beatmap_id
                    })
            except ValueError:
                continue

    count_total = len(files_to_process)
    print(f"Total files found: {count_total}\n")

    count_renamed = 0
    count_skipped = 0
    duplicates_found = 0

    for index, item in enumerate(files_to_process, 1):
        filename = item["filename"]
        file_path = item["full_path"]
        beatmap_id = item["beatmap"]
        year = item["year"]

        print(f"[{index} / {count_total}] Checking filename: '{filename}'")

        # Extract real metadata from inside .osz
        artist, title = get_metadata_from_osz(file_path)
        if not artist or not title:
            continue

        history_data[year].append(f"{beatmap_id} {artist} - {title}\n")

        # Sanitize and build expected name
        s_artist = sanitize_name(artist)
        s_title = sanitize_name(title)

        base_expected = f"{beatmap_id} {s_artist} - {s_title}"
        target_name = f"{base_expected}.osz"

        # Compare and rename
        if filename != target_name:
            count_renamed += 1

            if not args.apply:
                continue

            folder_path = file_path.parent

            new_path = folder_path / target_name
            new_path_tmp = new_path + ".tmp"

            if new_path_tmp.exists():
                count_skipped += 1
                print(f"Tmp file '{new_path_tmp}' already exists, please remove it before running command again")
                continue

            # First: move to .tmp file
            print(f"Renaming from '{file_path}' to '{new_path_tmp}'")
            os.rename(file_path, new_path_tmp)

            # Second: try to move from .tmp

            # Check for duplicates/collisions in the folder
            is_duplicate = False

            counter = 1
            while os.path.exists(os.path.join(folder_path, target_name)):
                target_name = f"{base_expected}_{counter}.osz"
                counter += 1
                is_duplicate = True

            if is_duplicate:
                duplicates_found += 1

            print(f"Renaming from '{new_path_tmp}' to '{target_name}'")
            os.rename(new_path_tmp, os.path.join(folder_path, target_name))

    if args.update_history:
        if not args.apply:
            print("\n[!] Skipping history update: \nHistory update requires --apply mode.")
        else:
            print("\nUpdating history files with original metadata...")
            for year, records in history_data.items():
                if not records:
                    continue

                history_filename = f"{year}_downloaded_maps.txt"
                # history file is usually in the root of beatmaps folder
                history_path = os.path.join(args.path, history_filename)

                # Sort records by the beatmap_id converted to integer
                sorted_records = sorted(records, key=get_id_from_record)

                with open(history_path, "w", encoding="utf-8") as f:
                    # Sort records to keep history file organized
                    f.writelines(sorted_records)
                print(f"[✓] Updated: {history_filename}")

    print("\n" + "="*30)
    print("Execution Finished:")
    print(f"Total files checked: {count_total}")
    print(f"Files to be renamed (or already renamed), also includes skipped files: {count_renamed}")
    print(f"Duplicates found: {duplicates_found}")
    print(f"Count skipped: {count_skipped}")

    if not args.apply:
        if count_renamed > 0:
            print("\nAction Required: \nRun with --apply to perform the actual renaming.")

if __name__ == "__main__":
    main()
