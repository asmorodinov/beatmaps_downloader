# beatmaps_downloader

## What is this tool for

It can download osu beatmaps from the html table, the main purpose is to automatically download all vocaloid maps from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/.

Also, here is another link to VAT website - https://www.vat.gg/resources/vocaloid-map-database.

But you can also reuse `download_map` function and define your own function for getting beatmap ids.

## Code of conduct

Please use this script responsibly.

At the moment of writing this, there were 1359 vocaloid maps, ~14.9 GB of data with videos included, ~9.07 GB without videos included.

Downloading large amounts of data might potentially overload the server, and you also might get IP blocked temporarily (or potentially even permanently, although this is unlikely).

If you get blocked, requests will likely return 429 HTTP error codes ("too many requests" error). Or you might get a page with a captcha, which the script will fail to parse as an `.osz` format.

If the script gets too many 429 errors too quickly, it will stop itself. In that case, try to resume the script the next day (script will continue to run from the point where you left it).

Also, if too many maps are failing to download (for whatever reason), the script will also stop itself.

Note: errors are written to stderr, and normal output is written to stdout. If you want, you can redirect stderr to a file, e.g. `python3 download_osu_maps_vocaloid.py (your arguments...) 2> stderr.txt`. This might potentially be helpful, if you want to separate errors from the main output, to be able to see them better.

## Features
- Supports multiple download mirrors. Unfortunately, only 2 for now, and `beatconnect.io` asks for captchas often, so basically only 1. This is because most mirror websites (and the official osu website) require authentication, and this is not implemented yet
- Supports automatic retries (for errors that can be retried)
- Supports loading a range of years for maps (`--year_start` included, `--year_end` not included)
- Supports `--no-video` flag (to save disk space and network bandwidth)
- Supports `--filter_mode` parameter, where you can select, which game mode beatmaps you want to download, e.g. STD, TAIKO, MANIA, CATCH (Note: only std format was tested by the author, other formats might not work properly)
- Automatically checks that file is a valid osz archive and extracts metadata to make a name for a file. Note: if artist or title contain forbidden characters (`< > : " / \ | ? *`), then the script will replace them with underscore (`_`) in the filename.
- Tracks download progress in a download history file, so that the script can be stopped and resumed from where it was left off. Beatmaps that were already successfully downloaded are not downloaded again. Note: you can delete a beatmap record from the saved history file, and then the script will try to download the beatmap again. If this beatmap already exists on disk, script will still download it, but save a copy under a different name (it will append `_1`, or `_2`, etc. to the name)
- If the script detects too many errors, it will stop itself
- Multiple instances of a script can be ran in parallel, as long as the years they operate on do not intersect (to avoid race conditions). So, in theory, you can run 19 instances (for each year from 2008 to 2026), for example. But you have to launch each instance yourself, in a different terminal
- Script supports `--delay` parameter, to specify delay between iterations. Note: `delay=5` (default) does not really help with `beatconnect.io` mirror rate limits anyway. And `delay=0` works fine with `catboy.best`. So this is not a super useful parameter in practise, you can probably set it to zero.


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

`beatconnect.io` sometimes will give you captchas to solve, in this case the downloaded file will be an html instead of an osz format, and the script will fail to parse it with a "File is not a zip file" error. After a few of these errors, script will stop itself.

From my experience, it seems like `beatconnect.io` will give you "429 too many requests" errors (and captchas to solve), even with 5 seconds delay (maybe this delay needs to be increased).

`catboy.best` also has a daily limit of downloads, but it is relatively large. If you run into 429 errors, try again next day.

So overall, it looks like `catboy.best` is indeed the best available mirror for now (it has higher priority in the script, so it will be used by default, and script will fallback to `beatconnect.io` in case of errors).

Since `catboy.best` is the default mirror, you can set `-d 0` for a quicker download of beatmaps, but this risks potentially overwhelming the website and getting 429 errors (although this didn't happen to me in practise, it seems that only the daily limit might be a potential issue).

## Additional notes

- You can stop the script via Ctrl+C and continue it later. Beatmap download will be skipped if the beatmap was recorded as already successfully downloaded in a download history file
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

Note: if you run multiple processes in parallel, there might be a higher chance to get "429 too many requests" error.

## The end

If everything worked fine, enjoy your newly downloaded vocaloid osu maps!

In my case, everything seems to be working correctly, when `catboy.best` is selected as a primary mirror website.

Note: I will also likely upload the downloaded beatmaps to the google drive, so that anyone can download them, without any programming knowledge required.
