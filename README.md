# SkyGuitar Scrapper

This project allows you to scrap sheet music from SkyGuitar videos.
It's just a small demo for learning purposes.
Please *do* support the channel by purchasing the sheet music.

The initial version was in Rust but I gave up on that.

```
usage: main.py [-h] [--link LINK] [--omit OMIT [OMIT ...]] [--i-start I_START] [--i-end I_END] [--tab-up]

options:
  -h, --help            show this help message and exit
  --link LINK, -l LINK  link to the YouTube video you want to scrap tabs from
  --omit OMIT [OMIT ...]
                        indicies of lines to omit
  --i-start I_START     which line to start from
  --i-end I_END         which line to end with
  --tab-up              usually the tabs are in the bottom half but sometimes in the upper half (yellow vids)
```