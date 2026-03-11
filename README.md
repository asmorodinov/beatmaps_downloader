# beatmaps_downloader

## What is this tool for

The script parses beatmap ids from the google docs spreadsheet, saved as html.

Then, it can download these beatmap ids from the main [osu.ppy.sh](https://osu.ppy.sh) website, or from mirrors such as [catboy.best](https://catboy.best), or [beatconnect.io](https://beatconnect.io).

My original purpose was to automatically download all (ranked) vocaloid maps from this reddit [post](https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/) (here is another link to the VAT's website - [database](https://www.vat.gg/resources/vocaloid-map-database)).

You can redefine beatmap ids selection (e.g. load them from a txt file instead of parsing html), and then reuse the rest of the script, if you want, to download other beatmaps (but this requires code modification, right now html parsing is hardcoded).

Note: I use the words "beatmap" and "beatmapset" interchangeably, technically more correct is to refer to them as beatmapsets, but beatmaps is just shorter to write.

## Code of conduct

Please use this script responsibly.

At the moment of writing this, there were 1359 vocaloid maps (in STD mode), ~14.9 GB of data with videos included, ~9.07 GB without videos included.

Downloading large amounts of data might potentially overload the server, and you also might get IP blocked temporarily (or potentially even permanently, although this is unlikely).

This script only downloads at most one beatmapset at a time, per running process, so it probably does not create a huge load to the servers, unless you spawn a lot of processes. And it only makes sense to spawn one process per year of data, at most (otherwise, you will run into race condition issues).

Also script automatically starts sleeping for ~hour, if it detects too many errors, and then automatically wakes up and continues running (in case of the main `osu.ppy.sh` website). In case of mirrors (e.g. `catboy.best`), it will just stop itself, and you have to resume it the next day.

So overall, I would say that this script is relatively safe to use, if you do it responsibly and carefully.
But just keep this issue in mind, if you decide to modify the script.

## Supported features
- Loading from [osu.ppy.sh](https://osu.ppy.sh), [catboy.best](https://catboy.best), or [beatconnect.io](https://beatconnect.io)
    - Note: it is recommended to use the main website, as it contains the most up-to-date data, but sometimes it also makes sense to use mirrors (e.g. to have less strict download limits per hour and not have to authenticate yourself). And in some cases, the main website beatmap's version is actually invalid, or has a wrong hash, compared to the mirror beatmap's version
- Integrity checks for downloaded beatmaps (and redownload if broken)
- Automatic error retrying (for errors that can be retried)
- Download history is tracked in a separate `.txt` file (for each year separately). If you stop the script, then after running it again, it will skip downloading beatmaps that are already present in the download history file. So the script can just continue where it left off
    - Note: you can delete a beatmap record from the download history file, and then the script will try to download the beatmap again. If this beatmap already exists on disk, script will still download it, but save it to a file under a different name (it will append `_1`, or `_2`, etc. to the name), and the original will not be overwritten
- You can specify a range of years, to filter beatmaps.
- Multiple scripts can be run in parallel (e.g. in different terminals), but the years of the beatmaps they operate on, must not intersect, otherwise you will run into race condition issues
    - So, for example, you can run a separate process for each year from 2008 to 2026
    - But generally, it is recommended to limit amount of processes to ~4, to not create too much load on the server
- You can filter for different osu! modes (STD, Taiko, Mania, Catch)
- You can specify `--no-video` flag, to download beatmaps with videos excluded from them (to save disk space and network bandwidth, and speed up download process).
- (Optional) Delay between iterations, to reduce load to the server
- Automatically renames files, if artist or title contain invalid filename characters (`< > : " / \ | ? *`), it just replaces those characters with underscore (`_`), but keeps the original name in the download history file.


## How to run

### 1. Download table as html

#### 1.1
Export google sheets table from https://www.reddit.com/r/osugame/comments/1c1k8wu/ranked_vocaloid_maps_database/ as html

Note: other options do not work (e.g. csv export), since links are stored in separate hidden tabs (e.g. 2025 data). The only way that worked for me was export as html

#### 1.2
Extract html archive to some folder (e.g. `~/vocaloid_table`, if on linux, or `%USERPROFILE%\\Downloads\\vocaloid_table`, if on Windows).

### 2. Install python (if not already installed)

Lookup a guide on google

### 3. Install dependencies (if not already installed)

`pip3 install pandas requests lxml ossapi`

Note:
- pandas, requests, lxml for the main script
- ossapi for integrity checks

### 4. Run the script (you have two possible options to run)

### 4.1. For `osu.ppy.sh` (recommended)

#### 4.1.1. Copy your osu session cookie (prerequisite)

- Login into osu in your browser
- Right click and select "View code"
- Go to Application -> Storage -> Cookies
- Find `osu_session` cookie, copy URL-decoded value, paste it into `osu_session.txt` file (in the same directory as the script you are about to run)

> [!WARNING]
> Do not share your osu_session cookie with anyone, otherwise they will be able to impersonate as you.

#### 4.1.2. Run the script

`python3 download_osu_maps_vocaloid_official.py {path to download maps to} {path to extracted html files} {other options, use --help for more info}`

### 4.2. For `catboy.best` and `beatconnect.io`

You can just run the script, no authentication required.

`python3 download_osu_maps_vocaloid.py {path to download maps to} {path to extracted html files} {other options, use --help for more info}`

### 4.3 Script options

In general, simply use `--help` to learn about available options, but I will also describe them here.

* `-s {YEAR_START}` - start year for beatmaps filtering
* `-e {YEAR_END}` - end year for beatmaps filtering (not included in the result, so the effective range is `[start, start + 1, ..., end - 1]`). For example, `-s 2008 -e 2012` would specify years `2008, 2009, 2010, 2011`
    - It is recommended to run multiple processes in parallel, where each process covers a range of approximately 4 years (e.g. `[2008, 2012)` case mentioned above)
        - This does not overload the server too much, but also speeds up the download
    - For gamemodes where there are less maps (i.e. any mode except for STD), you can just use one process with `-s 2008 -e 2027`
    - If you don't care about or already have downloaded old maps, you can select only the last year, for example `-s 2026 -e 2027` (or any other single year, if you want).
    - If `{YEAR_START} == {YEAR_END}`, this would result in an empty range (so you probably don't want this)
* `-f {MODE}` - game mode to filter (available options are `STD, TAIKO, MANIA, CATCH`)
* `-n` - download maps with videos excluded (optional, not enabled by default)
* `-d {DELAY}` - specify delay in seconds between iterations, 5 seconds by default
    - Note: in most cases, this can be set to zero, but default is 5, to be a bit more safe

### 4.3. Script example

`python3 download_osu_maps_vocaloid_official.py ~/vocaloid_maps_no_video_official ~/vocaloid_table -s 2008 -e 2027 -f STD -d 5 -n`

### 4.4. [Optional] Check files integrity

If you want, you can check files integrity (e.g. `.osu` md5 hashes, missing audio, background or video).

This is especially useful, if you downloaded beatmaps from mirrors, since they often can have outdated or invalid files (this is especially true for `catboy.best`).

To do this, you first need to get your client_id and client_secret for the osu! API.

Also, you need to install `ossapi` (which was already mentioned in the [dependencies](#3-install-dependencies-if-not-already-installed) section)

#### 4.4.1 Copy osu api client_id and client_secret (prerequisite)

1. Login to [osu.ppy.sh](https://osu.ppy.sh/)
2. Click on your profile on top-right, then click Settings
3. Scroll to the bottom
4. Above Github, there is an OAuth section
5. At the bottom of OAuth, click "New OAuth Application"
6. Application name: put any name (e.g. beatmap downloader)
7. Application Callback URLs: you can keep this empty
8. Click "Register application"
9. Click "Show client secret".
10. Copy client_id and client_secret, save them in a `secret_keys.json` file in the following format (this file should be in the same directory as `integrity_checker.py` script):
```
{
    "client_id": {put your client id here, integer value},
    "client_secret": "{put your client secret here, string value}"
}
```

#### 4.4.2. Check (and optionally try to fix) files integrity

`python3 integrity_checker.py {directory with beatmaps} {other options, use --help for more info}`

Options:
- `-s`, `-e` - same as above, they are used to filter beatmaps based on year
- `-i {file with ids}` - only check beatmaps that have ids that are present in this file (in a simple txt format, separated by newlines)
- `-d` - if set, try to automatically download and replace `.osz` files, if they are detected as invalid (here `osu.ppy.sh` is considered as the source of truth for download, even if sometimes it's also not perfect itself)
    - Note: if file was not downloaded, it will not be checked. Only existing files are checked
- `-n` - if `-d` is set and this option is set, then when replacing files, they will be downloaded with videos excluded

Example:
`python3 integrity_checker.py ~/vocaloid_maps_no_video_official -s 2008 -e 2027 -n -i ids_to_check.txt`

#### 4.4.3 What is actually validated
- Using osu api, test that local difficulties names (.osu files inside .osz) match with the online version of the beatmap
- MD5 hashes for .osu files are also checked (if they don't match online ones, it's an error)
- If a diff contains references to media (i.e. audio, background, video), then this media file must be present in an archive and must have non-zero size
- If media file exists, but has a different case, this is a warning (this will work on windows, but is a potential issue on other OS, although lazer seems to handle it even with case-insensetive filenames)
- If video is not present, but `-n` flag is set, this is ignored
- In general, missing video or background is a warning, but missing audio is a critical issue (error)

#### 4.4.4 What is not validated

Storyboards and custom hitsounds and other custom map skin elements are not checked, because it is kind of complicated to implement.

I rely on the fact that since we are downloading from the official `osu.ppy.sh` website, we can (somewhat) trust that it's output is correct.

#### 4.4.5 End goal
The goal is to have 0 warnings and 0 errrors in the end. Unfortunately, sometimes `osu.ppy.sh` downloads invalid or outdated files, and you have to redownload them from somewhere else (e.g. `catboy.best`) yourself.

But those cases are relatively rare (1 or 2 cases for me).

A non-matching case (lower vs higher) for filenames is a common warning, and can be essentially ignored (maybe it should not even be included in the report).

A missing video or a background is relatively common, for now I decided to just ignore those cases (there were not a lot of them).


### 4.5. [Optional] Cleanup after files have been redownloaded by integrity_checker.py

`integrity_checker.py` redownloads invalid `.osz` files, but it does not rename them, or update the download history file.

Sometimes, after `.osz` files are redownloaded, their metadata (artist and title) changes, so ideally, their filenames should be updated, and the download history files should be updated too.

If you don't care about this, then you can just skip this step, but you can also run this script to rename the files and update download history files:

`python3 check_filenames.py {directory with beatmaps} {other options, use --help for more info}`

Options:
- `-a` - if set, rename files. If not (default), only print information about files to be changed (dry-run)
- `-u` - update download history files (only works if `-a` is also set)
- `-s`, `-e` - year start and year end, as usual, for filtering

It is recommended to first run without `-a` and without `-u` (dry-run), and then decide if you actually want to rename the files.

Example:
`python3 check_filenames.py ~/vocaloid_maps_no_video_official -s 2008 -e 2027`

## Info about mirror websites

- `https://nerinyan.moe/d/{beatmap}` - does not work (via simple `requests.get()` call), asks to enable javascript
- `https://osu.direct/api/d/{beatmap}` - does not work, 403 error code
- `https://osu.ppy.sh/beatmapsets/{beatmap}/download` - works, but requires authentication (still, the recommended option). Has hourly download limits
- `https://beatconnect.io/b/{beatmaps}` - sometimes returns 404 (map not found), has strict download limits (a few maps per minute)
- `https://catboy.best/d/{beatmaps}` - works, but sometimes downloads older map which has to be updated via an official source. Has daily download limits

As mentioned above, `osu.ppy.sh` is the recommended option. If you want to have larger download limits, or don't want to login to your osu account and copy session cookie, you can use mirrors.

By default, `catboy.best` has higher priority, because `beatconnect.io` has very strict download limits, before it starts requiring to solve captchas (which the script fails to do and stops itself). `beatconnect.io` is used as a fallback option, in case `catboy.best` download fails.

`catboy.best` has high download daily limits (at the moment), probably around 2000 maps, but I don't know the exact value. But this comes at a price of being not a very reliable source of maps. In my case, around ~100 maps were flagged as invalid, out of ~1359 osu!std maps.

Note: if you have osu!supporter, `osu.ppy.sh` provides a bit more lenient download limits. In my case (I do have an osu!supporter), I was able to download ~750 maps, before hitting hourly limit (I don't know the exact value here too, and I am sure it might change in the future).

The nice thing (already mentioned above), is that in case of `osu.ppy.sh`, the script is resilient to errors that are caused by hitting the download quota limits, it will just sleep and wait until the quota is refreshed, and then retry (unless max_retries limit is reached, but it should start sleeping before that happens). This is currently implemented only for the `osu.ppy.sh` script version, for mirrors the script will stop itself and you have to restart the script later manually.

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

Note: don't run too many processes in parallel, or you might risk overloading the server (and potentially even flagged for too many requests per second).
At least, use the delay parameter, if you run multiple processes in parallel.

## The end

If everything worked fine, enjoy your newly downloaded vocaloid osu maps! (or other beatmaps that you wanted to download)

In my case, everything seems to be working correctly, except for some minor warnings, and some files I had to redownload from `catboy.best` instead of the main source `osu.ppy.sh`.

Notable issues (fixed by choosing a mirror instead of the main website):
- [#1344515 (std)](https://osu.ppy.sh/beatmapsets/1344515) - File is not a zip file error, when downloading from `osu.ppy.sh`, but works fine if downloaded from [catboy.best](https://catboy.best/d/1344515)
- [#2453821 (mania)](https://osu.ppy.sh/beatmapsets/2453821) - Hash mismatch. This does not always happen, sometimes it fixes itself after redownload, sometimes not. It seems that one of the osu servers is out-of-date, but others are up-to-date. Redownload from [catboy.best](https://catboy.best/d/245382) also helps
- [#1958128 (taiko)](https://osu.ppy.sh/beatmapsets/1958128) - Same situation as above, hash mismatch, redownloaded it manually
- [#2323300 (taiko)](https://osu.ppy.sh/beatmapsets/2323300) - Same situation as above, hash mismatch, redownloaded it manually
- [#17926 (std)](http://catboy.best/d/17926n) - This one has no audio file, when downloading from `catboy.best`. But it works fine, when downloaded from `osu.ppy.sh`. This is why mirrors can't always be trusted (apart from having outdated maps).

Note: I reported first four issues to osu-web github - https://github.com/ppy/osu-web/issues/12836.

As we can see, only a few maps out of more than a 1000, have critical issues (which still all of them can be solved by choosing a different download source). In case of using `catboy.best`, there would be a 100+ issues.

Found warnings are saved in the [warnings.txt](./warnings.txt) file (they are not super critical).

Note: I will also likely upload the downloaded beatmaps to the google drive, so that anyone can download them, without any programming knowledge required. Maybe even VAT team can post them as an official vocaloid map archive.
