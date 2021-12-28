# -*- codeing = utf-8 -*-
# @Time : 2021-12-21 16:34
# @Author : cAMP-Cascade-DNN
# @File : pre-process.py
# @Software : Pycharm
# @Contact: qq:1071747983
#          mail:wuxiaolong8001@163.com

# -*- 功能说明 -*-

# 进行数据预处理 进行图片的剪切 肝脏切片提取等

# -*- 功能说明 -*-
import os
import random
from os.path import join

import SimpleITK as sitk
import numpy as np
from scipy import ndimage

import config


class preprocess:
    def __init__(self, origin_path, fixed_path, args):
        self.origin_path = origin_path
        self.fixed_path = fixed_path
        self.expand_slice = args.expand_slice  # 轴向外侧扩张的slice数量
        self.size = args.min_slices  # 取样的最小slice数量
        self.xy_down_scale = args.xy_down_scale  # 降采样倍数 默认为0.5倍
        self.slice_down_scale = args.slice_down_scale
        self.valid_rate = args.valid_rate  # 验证集比例

    def fix(self):
        if not os.path.exists(self.fixed_path):  # 创建保存目录
            os.makedirs(join(self.fixed_path, 'data'))
            os.makedirs(join(self.fixed_path, 'label'))
        # 遍历训练数据的volume文件 创建文件list
        volume_list = os.listdir(join(self.origin_path, 'data'))
        # 文件数
        num = len(volume_list)
        print(f'Total num is {num}')
        # 循环目录
        for id, name in zip(range(num), volume_list):  # 生成序号与文件名
            print(f'......{name}  |  {id + 1}/{num}')  # 输出本轮文件名与进度
            volume_path = os.path.join(self.origin_path, 'data', name)  # volume文件名路径
            segment_path = os.path.join(self.origin_path, 'label', name.replace('volume', 'segmentation'))
            new_volume, new_segment = self.process(volume_path, segment_path)
            # 保存裁剪后的图片
            sitk.WriteImage(new_volume, os.path.join(self.fixed_path, 'data', name))
            sitk.WriteImage(new_segment, os.path.join(self.fixed_path, 'label',
                                                      name.replace('volume', 'segmentation').replace('.nii',
                                                                                                     '.nii.gz')))
            # 生成文件名列表
            self.write_train_val_name_list()

    def process(self, volume_path, segment_path):
        volume = sitk.ReadImage(volume_path, sitk.sitkInt16)
        volume_array = sitk.GetArrayFromImage(volume)  # 转换为numpy数组
        seg = sitk.ReadImage(segment_path, sitk.sitkInt8)
        seg_array = sitk.GetArrayFromImage(seg)  # 转换为numpy数组

        print(f'Original volume shape: {volume_array.shape} segment shape: {seg_array.shape}')
        seg_array[seg_array > 0] = 1  # 将分割标签中的肿瘤(白色)变为肝脏

        # 根据肝脏特点进行hu值窗口选择
        volume_array[volume_array > 200] = 200
        volume_array[volume_array < -200] = -200
        # volume_array[volume_array == -2000] = 0 #存疑

        # 降采样，ndimage矩阵缩放（对x和y轴进行降采样，slice轴的spacing归一化到slice_down_scale 1）
        volume_array = ndimage.zoom(volume_array, (
            volume.GetSpacing()[-1] / self.slice_down_scale, self.xy_down_scale, self.xy_down_scale), order=3)
        seg_array = ndimage.zoom(seg_array, (
            volume.GetSpacing()[-1] / self.slice_down_scale, self.xy_down_scale, self.xy_down_scale), order=0)

        # 根据分隔文件后俩个维度不为0 找到肝脏区域开始和结束的slice，并各向外扩张
        z = np.any(seg_array, axis=(1, 2))
        start, end = np.where(z)[0][[0, -1]]  # 开始与结束slice

        # 两个方向上各扩张个slice
        if start - self.expand_slice < 0:  # 已经很小了
            start = 0
        else:
            start -= self.expand_slice

        if end + self.expand_slice >= seg_array.shape[0]:
            end = seg_array.shape[0] - 1
        else:
            end += self.expand_slice

        print("Cut out range:", str(start) + '--' + str(end))

        # 如果这时候剩下的slice数量不足最低的size，直接放弃，这样的数据很少
        if end - start + 1 < self.size:
            print('Data range is too low :', name)
            return None, None

        # 截取保留区域
        volume_array = volume_array[start:end + 1, :, :]
        seg_array = seg_array[start:end + 1, :, :]
        print("Preprocessed shape:", volume_array.shape, seg_array.shape)

        # 保存为对应的格式
        new_volume = sitk.GetImageFromArray(volume_array)
        new_volume.SetDirection(volume.GetDirection())
        new_volume.SetOrigin(volume.GetOrigin())
        new_volume.SetSpacing((volume.GetSpacing()[0] * int(1 / self.xy_down_scale),
                               volume.GetSpacing()[1] * int(1 / self.xy_down_scale), self.slice_down_scale))

        new_seg = sitk.GetImageFromArray(seg_array)
        new_seg.SetDirection(volume.GetDirection())
        new_seg.SetOrigin(volume.GetOrigin())
        new_seg.SetSpacing((volume.GetSpacing()[0] * int(1 / self.xy_down_scale),
                            volume.GetSpacing()[1] * int(1 / self.xy_down_scale), self.slice_down_scale))
        return new_volume, new_seg

    def write_train_val_name_list(self):
        data_name_list = os.listdir(join(self.fixed_path, "data"))
        data_num = len(data_name_list)
        print('the fixed dataset total numbers of samples is :', data_num)
        random.shuffle(data_name_list)

        assert self.valid_rate < 1.0
        train_name_list = data_name_list[0:int(data_num * (1 - self.valid_rate))]
        val_name_list = data_name_list[int(data_num * (1 - self.valid_rate)):int(
            data_num * ((1 - self.valid_rate) + self.valid_rate))]

        self.write_name_list(train_name_list, "train_path_list.txt")
        self.write_name_list(val_name_list, "val_path_list.txt")

    def write_name_list(self, name_list, file_name):
        f = open(join(self.fixed_path, file_name), 'w')
        for name in name_list:
            # data_path = os.path.join('fixed', 'data', name)
            # seg_path = os.path.join('fixed', 'label', name.replace('volume', 'segmentation'))
            data_path = os.path.join(self.fixed_path, 'data', name)
            seg_path = os.path.join(self.fixed_path, 'label', name.replace('volume', 'segmentation'))
            f.write(data_path + ' ' + seg_path + "\n")
        f.close()


if __name__ == '__main__':
    # 加载超参数
    args = config.args

    origin_path = r'E:\Programming\Python\dataset\train'  # 训练数据根目录路径
    fixed_path = r'E:\Programming\Python\dataset\fixed'  # 处理数据根目录路径

    tool = preprocess(origin_path, fixed_path, args)
    tool.fix()  # 对原始数据进行裁剪并保存
