# beatmaps_downloader

## What is this tool for

It can download osu maps from the html table, the main purpose is to automatically download all vocaloid maps from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/

## How to run

1. Export google sheets table from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/ as html

Note: other options do not work (e.g. csv export), since links are stored in separate hidden tabs (e.g. 2025 data). The only way that worked for me was export as html

2. Extract html archive to some folder
3. Install python (if not already installed)
4. Install pandas and requests (if not already installed): `pip3 install pandas requests`
5. Run the script: `python3 download_osu_maps_vocaloid.py {path to download maps to} {path to extracted html files} {other options, use --help for more info}`

e.g. `python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2008 -e 2026 -f STD`

## additional notes

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

- Some maps are not available on beatconnect (looks like mostly explicit ones), I had to manually download them from osu.ppy.sh and copy to the directory with correct naming (`{ranked_year}_{beatmap_id}.osz`). These were maps for the time of writing readme, but there may be more maps in the future:
  - https://osu.ppy.sh/s/1627361
  - https://osu.ppy.sh/s/1767411
  - https://osu.ppy.sh/s/1817101
  - https://osu.ppy.sh/s/1817377
  - https://osu.ppy.sh/s/1818864
  - https://osu.ppy.sh/s/1840853
  - https://osu.ppy.sh/s/1911733
  - https://osu.ppy.sh/s/1922542
  - https://osu.ppy.sh/s/2070848
  - https://osu.ppy.sh/s/2154821
  - https://osu.ppy.sh/s/2194528
  - https://osu.ppy.sh/s/2302431
  - https://osu.ppy.sh/s/2308687
  - https://osu.ppy.sh/s/2353458
- TODO: come up with a better way to download maps rather than using beatconnect
