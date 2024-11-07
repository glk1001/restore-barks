import os
from collections import OrderedDict
from pathlib import Path
from typing import Tuple, Dict

import cv2 as cv
import numpy as np

from remove_alias_artifacts import get_median_filter

DEBUG_WRITE_COLOR_COUNTS = True

NUM_POSTERIZE_LEVELS = 5
NUM_POSTERIZE_EXCEPTION_LEVELS = 2
FIRST_LEVEL = int(255 / (NUM_POSTERIZE_LEVELS - 1))


def posterize_image(image: cv.typing.MatLike):
    for i in range(NUM_POSTERIZE_LEVELS):
        image[
            (image >= i * 255 / NUM_POSTERIZE_LEVELS)
            & (image < (i + 1) * 255 / NUM_POSTERIZE_LEVELS)
        ] = (i * 255 / (NUM_POSTERIZE_LEVELS - 1))


def remove_colors(image: cv.typing.MatLike):
    remove_colors = np.any(
        [
            image[:, :, 0] > FIRST_LEVEL,
            image[:, :, 1] > FIRST_LEVEL,
            image[:, :, 2] > FIRST_LEVEL,
        ],
        axis=0,
    )
    image[remove_colors] = (255, 255, 255)


def get_color_counts(image: cv.typing.MatLike) -> Dict[Tuple[int, int, int], int]:
    image_h, image_w = image.shape[0], image.shape[1]

    all_colors = dict()

    for i in range(0, image_h):  ## traverse image row
        for j in range(0, image_w):  ## traverse image col
            pixel = image[i][j]
            red = int(pixel[2])
            green = int(pixel[1])
            blue = int(pixel[0])

            color = (red, green, blue)

            if color in all_colors:
                all_colors[color] += 1
            else:
                all_colors[color] = 1

    return all_colors


def write_color_counts(filename: str, image: cv.typing.MatLike):
    color_counts = get_color_counts(image)
    color_counts_descending = OrderedDict(
        sorted(color_counts.items(), key=lambda kv: kv[1], reverse=True)
    )
    with open(filename, "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")


def process_image(out_basename: str, image: cv.typing.MatLike):
    out_image = get_median_filter(image)
    median_filter_image_file = os.path.join(
        out_dir, out_basename + "-median-filtered.jpg"
    )
    cv.imwrite(median_filter_image_file, out_image)

    posterize_image(out_image)
    posterized_image_file = os.path.join(out_dir, out_basename + "-posterized.jpg")
    cv.imwrite(posterized_image_file, out_image)

    if DEBUG_WRITE_COLOR_COUNTS:
        posterized_counts_file = os.path.join(
            out_dir, out_basename + "-posterized-color-counts.txt"
        )
        write_color_counts(posterized_counts_file, out_image)

    remove_colors(out_image)

    if DEBUG_WRITE_COLOR_COUNTS:
        remaining_color_counts_file = os.path.join(
            out_dir, out_basename + "-remaining-color-counts.txt"
        )
        write_color_counts(remaining_color_counts_file, out_image)

    out_image_file = os.path.join(out_dir, out_basename + "-color-removed.jpg")
    cv.imwrite(out_image_file, out_image)


# posterized_colors = get_posterized_colors()
# for color in posterized_colors:
#         print(f"{color}")


out_dir = "/home/greg/Prj/workdir/restore-tests"
os.makedirs(out_dir, exist_ok=True)

test_image_files = [
    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg"),
    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg"),
    Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg"),
]
# test_image_file = Path("/home/greg/Prj/github/restore-barks/experiments/test-image-3-noise-reduction.jpg")
# test_image_file = Path("/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg")

for image_file in test_image_files:
    print(f'Processing "{image_file}"...')

    src_image = cv.imread(str(image_file))

    height, width, num_channels = src_image.shape
    print(f"width: {width}, height: {height}, channels: {num_channels}")

    process_image(image_file.stem, src_image)
