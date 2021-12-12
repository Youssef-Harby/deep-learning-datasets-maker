# coding: utf8
# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import glob
import os.path
# import argparse
import warnings
import numpy as np



# TODO:  assign command line argument to variable

def get_files(path, format, postfix):
    pattern = '*%s.%s' % (postfix, format)

    search_files = os.path.join(path, pattern)
    search_files2 = os.path.join(path, "*", pattern)  # 包含子目录
    search_files3 = os.path.join(path, "*", "*", pattern)  # 包含三级目录

    filenames = glob.glob(search_files)
    filenames2 = glob.glob(search_files2)
    filenames3 = glob.glob(search_files3)

    filenames = filenames + filenames2 + filenames3

    return sorted(filenames)


def generate_list(args):
    separator = args["separator"]
    dataset_root = args["dataset_root"]
    if sum(args["split"]) != 1.0:
        raise ValueError("划分比例之和必须为1")

    file_list = os.path.join(dataset_root, 'labels.txt')
    with open(file_list, "w") as f:
        for label_class in args["label_class"]:
            # print(label_class)  # test
            f.write(label_class + '\n')

    image_dir = os.path.join(dataset_root, args["images_dir_name"])
    label_dir = os.path.join(dataset_root, args["labels_dir_name"])
    image_files = get_files(image_dir, args["format"][0], args["postfix"][0])
    label_files = get_files(label_dir, args["format"][1], args["postfix"][1])
    if not image_files:
        warnings.warn("No files in {}".format(image_dir))
    num_images = len(image_files)

    if not label_files:
        warnings.warn("No files in {}".format(label_dir))
    num_label = len(label_files)

    if num_images != num_label and num_label > 0:
        raise Exception("Number of images = {}    number of labels = {} \n"
                        "Either number of images is equal to number of labels, "
                        "or number of labels is equal to 0.\n"
                        "Please check your dataset!".format(
                            num_images, num_label))

    image_files = np.array(image_files)
    label_files = np.array(label_files)
    state = np.random.get_state()
    np.random.shuffle(image_files)
    np.random.set_state(state)
    np.random.shuffle(label_files)

    start = 0
    num_split = len(args["split"])
    dataset_name = ['train', 'val', 'test']
    for i in range(num_split):
        dataset_split = dataset_name[i]
        print("Creating {}.txt...".format(dataset_split))
        if args["split"][i] > 1.0 or args["split"][i] < 0:
            raise ValueError(
                "{} dataset percentage should be 0~1.".format(dataset_split))

        file_list = os.path.join(dataset_root, dataset_split + '.txt')
        with open(file_list, "w") as f:
            num = round(args["split"][i] * num_images)
            end = start + num
            if i == num_split - 1:
                end = num_images
            for item in range(start, end):
                left = image_files[item].replace(dataset_root, '')
                if left[0] == os.path.sep:
                    left = left.lstrip(os.path.sep)

                try:
                    right = label_files[item].replace(dataset_root, '')
                    if right[0] == os.path.sep:
                        right = right.lstrip(os.path.sep)
                    line = left + separator + right + '\n'
                except:
                    line = left + '\n'

                f.write(line)
                # print(line)  # test
            start = end


# if __name__ == '__main__':
#     args = parse_args()
#     generate_list(args)
