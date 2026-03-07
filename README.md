# beatmaps_downloader

## What is this tool for

It can download osu maps from the html table, the main purpose is to automatically download all vocaloid maps from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/.

Also, here is another link to VAT website - https://www.vat.gg/resources/vocaloid-map-database.

But you can also reuse `download_map` function and define your own function for getting beatmap ids.

## How to run

1. Export google sheets table from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/ as html

Note: other options do not work (e.g. csv export), since links are stored in separate hidden tabs (e.g. 2025 data). The only way that worked for me was export as html

2. Extract html archive to some folder
3. Install python (if not already installed)
4. Install pandas, requests and lxml (if not already installed): `pip3 install pandas requests lxml`
5. Run the script: `python3 download_osu_maps_vocaloid.py {path to download maps to} {path to extracted html files} {other options, use --help for more info}`

e.g. `python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2008 -e 2026 -f STD`

Note: there is an option `-d` which adds delay between map downloads (5 seconds by default). This is to help avoid overloading mirror websites, and also to avoid getting "429 too many requests" errors.

Note: there is another option `-n` which downloads maps without video, to save disk space and network bandwidth (it is not enabled by default, so by default video is included, if available).

## Info about mirror websites

- `https://nerinyan.moe/d/{beatmap}` - does not work (via simple `requests.get()` call), asks to enable javascript
- `https://osu.direct/api/d/{beatmap}` - does not work, 403 error code
- `https://osu.ppy.sh/beatmapsets/{beatmap}/download` - works, but requires authentication
- `https://beatconnect.io/b/{beatmaps}` - sometimes returns 404 (map not found)
- `https://catboy.best/d/{beatmaps}` - works, but sometimes downloads older map which has to be updated later within the osu!lazer

`beatconnect.io` sometimes will give you captchas to solve, in this case the downloaded file will be around ~10KB in size. You can delete these files, and then try to download maps again later.

From my experience, it seems like `beatconnect.io` will give you "429 too many requests" errors (and captchas to solve), even with 5 seconds delay (maybe it needs to be increased).
And `catboy.best` does not give "429 too many requests" errors, even with 0 seconds delay.

So overall, it looks like `catboy.best` is indeed the best available mirror for now (it has higher priority in the script, so it will be used by default, and script will fallback to `beatconnect.io` in case of errors).

Since `catboy.best` is the default mirror, you can set `-d 0` for a quicker download of beatmaps, but this risks overwhelming the website and getting 429 errors.

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
python3 download_osu_maps_vocaloid.py ~/vocaloid ~/vocaloid_table -s 2024 -e 2027
```

Note: if you run multiple processes in parallel, there might be a higher chance to get "429 too many requests error".
