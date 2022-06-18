#!/usr/bin/env python3

import itertools
from pytube import YouTube
from argparse import ArgumentParser
from pathlib import Path
import shutil
import cv2
import numpy as np
from PIL import Image
import re


def sanitize_vid_title(name):
    name = name.replace("TAB", "")
    name = name.replace("- Fingerstyle Lesson", "")
    name = name.strip()
    name = re.sub(r"[\d\+\#]+", "", name)
    name = re.sub(" +", " ", name)
    return name


if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument(
        "--link", "-l", default="https://www.youtube.com/watch?v=sBUsiVBxzEQ",
        help="link to the YouTube video you want to scrap tabs from"
    )
    args.add_argument(
        "--count", "-c", type=int, default=None,
        help="how many sheet lines to take (top crop)"
    )
    args.add_argument(
        "--tab-up", action="store_true",
        help="usually the tabs are in the bottom half but sometimes in the upper half (yellow vids)"
    )
    args = args.parse_args()

    Path('videos/').mkdir(exist_ok=True)

    # getting video part
    handle = YouTube(args.link)
    vid_title = sanitize_vid_title(handle.title)
    new_path = f"videos/{vid_title}.mp4"

    if Path(new_path).is_file():
        print(f"Found existing file `{new_path}`, skipping download")
    else:
        streams = handle.streams.filter(progressive=True, file_extension='mp4')
        streams = streams.order_by('resolution').desc().first()
        print("Downloading", vid_title)
        downloaded_path = streams.download(output_path="videos/")
        shutil.move(downloaded_path, new_path)
        print("Finished")

    # getting frames
    vidcap = cv2.VideoCapture(new_path)
    start_frame = None

    for frame in itertools.count(start=1000, step=20):
        vidcap.set(1, frame)
        success, img = vidcap.read()
        if not success:
            print("Unable to find first tab appearance")
            exit()

        if args.tab_up:
            img_tab = img[:int(img.shape[0] * 0.4)]
        else:
            img_tab = img[-int(img.shape[0] * 0.4):]

        black_pixels = np.all(img_tab <= 10, axis=2).sum()
        print(f"frame {frame}, black pixels {black_pixels}")
        if black_pixels <= 50000:
            start_frame = frame
            print(f"found start frame at {start_frame}")
            break

    if start_frame is None:
        print("Couldn't find start frame")
        exit()

    sheet_frames = []
    hand_frame = None

    # find when hands disappear
    prev_img = None
    for frame in range(start_frame, start_frame + 500, 20):
        vidcap.set(1, frame)
        success, img = vidcap.read()
        if not success:
            print("Unable to find disappearing hand")
            exit()

        # crop and normalize
        if args.tab_up:
            img = img[:int(img.shape[0] * 0.4), -int(img.shape[1] * 0.4):]
        else:
            img = img[-int(img.shape[0] * 0.4):, -int(img.shape[1] * 0.4):]

        # transform BGR to RGB
        img = img[:, :, ::-1]

        if prev_img is not None:
            diff = np.linalg.norm((prev_img - img).flatten() / 255, ord=1)
            print(f"avg difference {diff}")
            if diff >= 100000:
                # the first hit is when the "hands" start disappearing
                # so we need to skip forward
                hand_frame = frame + 40
                break

        prev_img = img

    if hand_frame is None:
        print("Couldn't find the frame when hands disappear")
        exit()
    sheet_frames.append(hand_frame)

    # main loop
    for frame in itertools.count(start=hand_frame, step=20):
        # cooldown adding frames
        if frame <= sheet_frames[-1] + 200:
            continue

        vidcap.set(1, frame)
        success, img = vidcap.read()
        if not success:
            break

        # crop and normalize
        if args.tab_up:
            img = img[:int(img.shape[0] * 0.4)]
        else:
            img = img[-int(img.shape[0] * 0.4):]
        # transform BGR to RGB
        img = img[:, :, ::-1]

        img_left = img[:, :int(img.shape[1] * 0.2)].copy()
        mask_0 = img_left[:, :, 2] >= img_left[:, :, 0]
        mask_1 = img_left[:, :, 2] >= img_left[:, :, 1]
        mask_2 = np.all(img_left > 10, axis=2)
        mask = np.all(np.stack([mask_0, mask_1, mask_2], axis=2), axis=2)
        blue_pixels = mask.sum()
        print(f"frame {frame}, blue pixels {blue_pixels}")

        if blue_pixels >= 10000:
            sheet_frames.append(frame)

            # manual override of number of lines
            if len(sheet_frames) == args.count:
                break

    print("Done parsing")
    print("Saving")
    img_data = []
    for frame_i, frame in enumerate(sheet_frames):
        vidcap.set(1, frame)
        success, img = vidcap.read()
        if not success:
            break

        # crop and normalize
        if args.tab_up:
            img = img[:int(img.shape[0] * 0.45)]
        else:
            img = img[-int(img.shape[0] * 0.45):]
        # transform BGR to RGB
        img = img[:, :, ::-1]

        img_data.append(img)

    img_all = np.concatenate(img_data, axis=0)
    pil_handle = Image.fromarray(img_all, 'RGB')
    pil_handle.save(f"videos/{vid_title}.png")
