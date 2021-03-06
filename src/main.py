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
    name = re.sub(r"[\d\+\#]+", "", name)
    name = re.sub(" +", " ", name)
    name = name.strip()
    return name


if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument(
        "--link", "-l", default="https://www.youtube.com/watch?v=sBUsiVBxzEQ",
        help="link to the YouTube video you want to scrap tabs from"
    )
    args.add_argument(
        "--omit", type=int, nargs="+", default=[],
        help="indicies of lines to omit"
    )
    args.add_argument(
        "--frame-start", type=int, default=1000,
        help="which video to start from"
    )
    args.add_argument(
        "--i-start", type=int, default=0,
        help="which line to start from"
    )
    args.add_argument(
        "--i-end", type=int, default=None,
        help="which line to end with"
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

    for frame in itertools.count(start=args.frame_start, step=20):
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
        print(f"Frame {frame:<4}: black pixels {black_pixels}")
        if black_pixels <= 50000:
            start_frame = frame
            print(f"Found start frame at {start_frame}")
            break

    if start_frame is None:
        print("Couldn't find start frame")
        exit()

    sheet_frames = []
    hand_frame = None

    # find when hands disappear
    prev_img = None
    for frame in range(start_frame, start_frame + 1000, 20):
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
            print(f"Frame {frame:<4}: avg difference {diff:.2f}")
            if diff >= 100000:
                # the first hit is when the "hands" start disappearing
                # so we need to skip forward
                hand_frame = frame + 40
                break

        prev_img = img

    if hand_frame is None:
        print("Couldn't find the frame when hands disappear")
        exit()

    if 0 not in args.omit and args.i_start <= 1:
        sheet_frames.append(hand_frame)

    # main loop
    for frame in itertools.count(start=hand_frame, step=20):
        # cooldown adding frames
        if len(sheet_frames) != 0 and frame <= sheet_frames[-1] + 120:
            continue

        vidcap.set(1, frame)
        success, img = vidcap.read()
        if not success:
            break

        # crop and normalize
        if args.tab_up:
            img = img[:int(img.shape[0] * 0.35)]
        else:
            img = img[-int(img.shape[0] * 0.35):]
        # transform BGR to RGB
        img = img[:, :, ::-1]

        img_left = img[:, :int(img.shape[1] * 0.2)].copy()
        mask_0 = img_left[:, :, 2] > img_left[:, :, 0]
        mask_1 = img_left[:, :, 2] > img_left[:, :, 1]
        mask_2 = np.all(img_left > 10, axis=2)
        mask = np.all(np.stack([mask_0, mask_1, mask_2], axis=2), axis=2)
        blue_pixels = mask.sum()
        print(f"Frame {frame:<4}: blue pixels {blue_pixels}")

        if blue_pixels >= 8000:
            # pil_handle = Image.fromarray(img, mode="RGB")
            # pil_handle.show()
            sheet_frames.append(frame)

    print("Done parsing")
    print(f"Saving {len(sheet_frames)} lines")

    img_data = []
    for frame_i, frame in enumerate(sheet_frames):
        if frame_i + 1 in args.omit or frame_i + 1 < args.i_start - 1 or (args.i_end is not None and frame_i + 1 > args.i_end):
            continue

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
