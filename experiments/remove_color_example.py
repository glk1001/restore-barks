from typing import Set, Tuple, Dict, List
from collections import OrderedDict

import cv2 as cv
import numpy as np

from remove_alias_artifacts import get_median_filter

COLOR_REMOVE_EXCEPTIONS = {
 (0, 0, 0),
        (0, 0, 63),
        (0, 63, 0),
        (0, 63, 63),
        (63, 0, 0),
        (63, 63, 0),
(63, 0, 63),
}


def posterize_image(image: cv.typing.MatLike):
    n = 5

    for i in range(n):
        image[(image >= i * 255 / n) & (image < (i + 1) * 255 / n)] = i * 255 / (n - 1)


def get_posterized_colors() -> Set[Tuple[int,int,int]]:
    n = 5

    all_colors = set()
    for r in range(n):
        red = int(r * 255 / (n - 1))
        for g in range(n):
            green = int(g * 255 / (n - 1))
            for b in range(n):
                blue = int(b * 255 / (n - 1))
                all_colors.add((red, green, blue))

    return all_colors


def get_colors_to_remove() -> Set[Tuple[int,int,int]]:
    posterized_colors = get_posterized_colors()
    return posterized_colors - COLOR_REMOVE_EXCEPTIONS


def get_color_counts(image: cv.typing.MatLike) -> Dict[Tuple[int,int,int], int]:
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


def remove_colors(
    colors: Set[Tuple[int, int, int]],
    grey_img: cv.typing.MatLike,
    image: cv.typing.MatLike,
):
    image_h, image_w = image.shape[0], image.shape[1]

    threshold_red = 90
    threshold_green = 90
    threshold_blue = 90

    accepted_colors = dict()
    posterized_removed_colors = dict()
    unposterized_removed_colors = dict()

    for i in range(0, image_h):  ## traverse image row
        for j in range(0, image_w):  ## traverse image col
            pixel = image[i][j]
            red = int(pixel[2])
            green = int(pixel[1])
            blue = int(pixel[0])
            grey = int(grey_img[i][j])

            color = (red, green, blue)

            if color in colors:
                image[i][j] = (255, 255, 255)
                print(f"({i},{j}): {red},{green},{blue},{grey} - remove posterized")
                if color in posterized_removed_colors:
                    posterized_removed_colors[color] += 1
                else:
                    posterized_removed_colors[color] = 1
            elif (
                abs(red - grey) < threshold_red
                and abs(green - grey) < threshold_green
                and abs(blue - grey) < threshold_blue
            ):
                image[i][j] = pixel
                if color in accepted_colors:
                    accepted_colors[color] += 1
                else:
                    accepted_colors[color] = 1
                print(f"({i},{j}): {red},{green},{blue},{grey} - keep")
            else:
                image[i][j] = (255, 255, 255)
                print(f"({i},{j}): {red},{green},{blue},{grey} - remove unposterized")
                if color in unposterized_removed_colors:
                    unposterized_removed_colors[color] += 1
                else:
                    unposterized_removed_colors[color] = 1

    color_counts_descending = OrderedDict(sorted(accepted_colors.items(),
                                                 key=lambda kv: kv[1], reverse=True))
    with open("accepted-color-counts.txt", "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")

    color_counts_descending = OrderedDict(sorted(posterized_removed_colors.items(),
                                                 key=lambda kv: kv[1], reverse=True))
    with open("posterized-removed-color-counts.txt", "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")

    color_counts_descending = OrderedDict(sorted(unposterized_removed_colors.items(),
                                                 key=lambda kv: kv[1], reverse=True))
    with open("unposterized-removed-color-counts.txt", "w") as f:
        for color in color_counts_descending:
            f.write(f"{color}: {color_counts_descending[color]}\n")


# test_image = "/home/greg/Prj/github/restore-barks/experiments/test-image-1.jpg"
# out_file = "/tmp/test-image-1-out.jpg"
# test_image = "/home/greg/Prj/github/restore-barks/experiments/test-image-2.jpg"
# out_file = "/tmp/test-image-2-out.jpg"
test_image = "/home/greg/Prj/github/restore-barks/experiments/test-image-3.jpg"
out_file = "/tmp/test-image-3-out.jpg"
# test_image = "/home/greg/Books/Carl Barks/Silent Night (Gemstone)/Gemstone-cp-3/01-upscayled_upscayl_2x_ultramix_balanced.jpg"
# out_file ="/tmp/junk-out-image-big.jpg"

src_image = cv.imread(test_image)
# src_image = cv.copyMakeBorder(src_image, 10, 10, 10, 10, cv.BORDER_CONSTANT, None, value = (255,255,255))
height, width, num_channels = src_image.shape
print(f"width: {width}, height: {height}, channels: {num_channels}")

blurred_image = get_median_filter(src_image)
gray_image = cv.cvtColor(blurred_image, cv.COLOR_BGR2GRAY)

# posterized_colors = get_posterized_colors()
# for color in posterized_colors:
#         print(f"{color}")

colors_to_remove = get_colors_to_remove()

out_image = blurred_image
posterize_image(out_image)
cv.imwrite("/tmp/posterized-image.jpg", out_image)

color_counts = get_color_counts(out_image)
color_counts_descending = OrderedDict(sorted(color_counts.items(),
                                             key=lambda kv: kv[1], reverse=True))
with open("posterized-color-counts.txt", "w") as f:
    for color in color_counts_descending:
        f.write(f"{color}: {color_counts_descending[color]}\n")

remove_colors(colors_to_remove, gray_image, out_image)

color_counts = get_color_counts(out_image)
color_counts_descending = OrderedDict(sorted(color_counts.items(),
                                             key=lambda kv: kv[1], reverse=True))
with open("remaining-color-counts.txt", "w") as f:
    for color in color_counts_descending:
        f.write(f"{color}: {color_counts_descending[color]}\n")

cv.imwrite(out_file, out_image)
