# beatmaps_downloader

## What is this tool for

It can download osu maps from the html table, the main purpose is to automatically download all vocaloid maps from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/

But you can also reuse `download_map` function and define your own function for getting beatmap ids.

## How to run

1. Export google sheets table from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/ as html

Note: other options do not work (e.g. csv export), since links are stored in separate hidden tabs (e.g. 2025 data). The only way that worked for me was export as html

2. Extract html archive to some folder
3. Install python (if not already installed)
4. Install pandas and requests (if not already installed): `pip3 install pandas requests`
5. Run the script: `python3 download_osu_maps_vocaloid.py {path to download maps to} {path to extracted html files} {other options, use --help for more info}`

e.g. `python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2008 -e 2026 -f STD`

## Info about mirror websites

- `https://nerinyan.moe/d/{beatmap}` - does not work (via simple `requests.get()` call), asks to enable javascript
- `https://osu.direct/api/d/{beatmap}` - does not work, 403 error code
- `https://osu.ppy.sh/beatmapsets/{beatmap}/download` - works, but requires authentication
- `https://beatconnect.io/b/{beatmaps}` - sometimes returns 404 (map not found)
- `https://catboy.best/d/{beatmaps}` - works, but sometimes downloads older map which has to be updated later within the osu!lazer


## Additional notes

- You can stop the script via Ctrl+C and continue it later. Map download will be skipped if file already exists on disk
- When new maps get added to the list, you can update html table and download only new ones via script (since already downloaded maps are skipped)
- You can run multiple processes in parallel to speed up download, just make sure that years don't intersect

e.g.
```
python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2008 -e 2012
python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2012 -e 2016
python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2016 -e 2020
python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2020 -e 2024
python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2024 -e 2026
```

