import SimpleITK as sitk
import numpy as np
import torch
from scipy import ndimage
from torch.utils.data import Dataset
from utils.common import *


class Img_DataSet(Dataset):
    def __init__(self, data_path, args):
        self.n_labels = args.n_labels
        self.cut_size = args.test_cut_size  # slide size 48
        self.cut_stride = args.test_cut_stride  # stripe size 96

        # 读取一个data文件并归一化 、resize
        self.ct = sitk.ReadImage(data_path, sitk.sitkInt16)
        self.data_np = sitk.GetArrayFromImage(self.ct)
        self.ori_shape = self.data_np.shape
        self.data_np = ndimage.zoom(self.data_np, (args.slice_down_scale, args.xy_down_scale, args.xy_down_scale),
                                    order=3)  # 双三次重采样
        self.data_np[self.data_np > 200] = 200
        self.data_np[self.data_np < -200] = -200
        self.data_np = self.data_np / args.norm_factor
        self.resized_shape = self.data_np.shape
        # 扩展一定数量的slices，以保证卷积下采样合理运算
        self.data_np = self.padding_img(self.data_np, self.cut_size, self.cut_stride)
        self.padding_shape = self.data_np.shape
        # 对数据按步长进行分patch操作，以防止显存溢出
        self.data_np = self.extract_ordered_overlap(self.data_np, self.cut_size, self.cut_stride)

        # 预测结果保存
        self.result = None

    def __getitem__(self, index):
        data = torch.from_numpy(self.data_np[index])
        data = torch.FloatTensor(data).unsqueeze(0)
        return data

    def __len__(self):
        return len(self.data_np)

    def update_result(self, tensor):
        if self.result is not None:
            self.result = torch.cat((self.result, tensor), dim=0)
        else:
            self.result = tensor

    def recompone_result(self):

        patch_s = self.result.shape[2]

        N_patches_img = (self.padding_shape[0] - patch_s) // self.cut_stride + 1
        assert (self.result.shape[0] == N_patches_img)

        full_prob = torch.zeros((self.n_labels, self.padding_shape[0], self.ori_shape[1],
                                 self.ori_shape[2]))  # itialize to zero mega array with sum of Probabilities
        full_sum = torch.zeros((self.n_labels, self.padding_shape[0], self.ori_shape[1], self.ori_shape[2]))

        for s in range(N_patches_img):
            full_prob[:, s * self.cut_stride:s * self.cut_stride + patch_s] += self.result[s]
            full_sum[:, s * self.cut_stride:s * self.cut_stride + patch_s] += 1

        assert (torch.min(full_sum) >= 1.0)  # at least one
        final_avg = full_prob / full_sum
        # print(final_avg.size())
        assert (torch.max(final_avg) <= 1.0)  # max value for a pixel is 1.0
        assert (torch.min(final_avg) >= 0.0)  # min value for a pixel is 0.0
        img = final_avg[:, :self.ori_shape[0], :self.ori_shape[1], :self.ori_shape[2]]
        return img.unsqueeze(0)

    def padding_img(self, img, size, stride):
        assert (len(img.shape) == 3)  # 3D array
        img_s, img_h, img_w = img.shape
        leftover_s = (img_s - size) % stride

        if (leftover_s != 0):
            s = img_s + (stride - leftover_s)
        else:
            s = img_s

        tmp_full_imgs = np.zeros((s, img_h, img_w), dtype=np.float32)
        tmp_full_imgs[:img_s] = img
        print("Padded images shape: " + str(tmp_full_imgs.shape))
        return tmp_full_imgs

    # Divide all the full_imgs in pacthes
    def extract_ordered_overlap(self, img, size, stride):
        img_s, img_h, img_w = img.shape
        assert (img_s - size) % stride == 0
        N_patches_img = (img_s - size) // stride + 1

        print("Patches number of the image:{}".format(N_patches_img))
        patches = np.empty((N_patches_img, size, img_h, img_w), dtype=np.float32)

        for s in range(N_patches_img):  # loop over the full images
            patch = img[s * stride: s * stride + size]
            patches[s] = patch

        return patches  # array with all the full_imgs divided in patches


# 给具体的测试文件nii地址
def Test_Datasets(datapath, args):
    print("\nStart Evaluate: ", datapath)
    # img_dataset, file_idx
    yield Img_DataSet(datapath, args=args), datapath.split('-')[-1]
