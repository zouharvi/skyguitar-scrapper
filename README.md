# SkyGuitar Scrapper

This project allows you to scrap sheet music from SkyGuitar videos.
It's just a small demo for learning purposes.
Please *do* support the channel by purchasing the sheet music.

The initial version was in Rust but I gave up on that.

```
usage: main.py [-h] [--link LINK] [--count COUNT] [--tab-up]

options:
  -h, --help            show this help message and exit
  --link LINK, -l LINK  link to the YouTube video you want to scrap tabs from
  --count COUNT, -c COUNT
                        how many sheet lines to take (top crop)
  --tab-up              usually the tabs are in the bottom half but sometimes in the upper half (yellow vids)
```