import os

import SimpleITK as sitk
import numpy as np
import torch
from torch.utils.data import Dataset as dataset
from torchvision.transforms import Compose


class Center_Crop:
    def __init__(self, base, max_size):
        self.base = base  # base默认取16，因为4次下采样后为1
        self.max_size = max_size
        if self.max_size % self.base:
            self.max_size = self.max_size - self.max_size % self.base  # max_size为限制最大采样slices数，防止显存溢出，同时也应为16的倍数

    def __call__(self, img, label):
        if img.size(1) < self.base:
            return None
        slice_num = img.size(1) - img.size(1) % self.base
        slice_num = min(self.max_size, slice_num)

        left = img.size(1) // 2 - slice_num // 2
        right = img.size(1) // 2 + slice_num // 2

        crop_img = img[:, left:right]
        crop_label = label[:, left:right]
        return crop_img, crop_label


class Val_Dataset(dataset):
    def __init__(self, args):
        self.args = args
        self.filename_list = self.load_file_name_list(os.path.join(args.dataset_path, 'val_path_list.txt'))
        self.transforms = Compose([
            Center_Crop(base=16, max_size=args.val_crop_max_size)  # 居中剪裁
        ])

    def __getitem__(self, index):

        ct = sitk.ReadImage(self.filename_list[index][0], sitk.sitkInt16)
        seg = sitk.ReadImage(self.filename_list[index][1], sitk.sitkUInt8)

        ct_array = sitk.GetArrayFromImage(ct)
        seg_array = sitk.GetArrayFromImage(seg)

        ct_array = ct_array / self.args.norm_factor
        ct_array = ct_array.astype(np.float32)

        ct_array = torch.FloatTensor(ct_array).unsqueeze(0)
        seg_array = torch.FloatTensor(seg_array).unsqueeze(0)

        if self.transforms:
            ct_array = self.transforms(ct_array)
            seg_array = self.transforms(seg_array)

        return ct_array, seg_array.squeeze(0)

    def __len__(self):
        return len(self.filename_list)

    def load_file_name_list(self, file_path):
        file_name_list = []
        with open(file_path, 'r') as file_to_read:
            while True:
                lines = file_to_read.readline().strip()  # 整行读取数据
                if not lines:
                    break
                file_name_list.append(lines.split())
        return file_name_list
