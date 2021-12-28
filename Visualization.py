# -*- codeing = utf-8 -*-
# @Time : 2021-12-12 15:49
# @Author : cAMP-Cascade-DNN
# @File : Visualization.py
# @Software : Pycharm
# @Contact: qq:1071747983
#          mail:wuxiaolong8001@163.com

# -*- 功能说明 -*-

#

# -*- 功能说明 -*-
import numpy as np
from scipy.ndimage.morphology import binary_dilation


# 该函数将每个2d图像进行变换。
def MergeImageWithROI(data, roi, overlap=False, max_value=1, min_value=0):
    if data.ndim >= 3:
        print("Should input 2d image")
        return data
    if not isinstance(roi, list):
        roi = [roi]

    if overlap:
        new_data = np.stack([data, data, data], axis=2)
        hsi = np.array([1, 0, 0])
        rgb = hsi * (max_value - min_value) + min_value
        index_x, index_y = np.where(roi[0] >= 1)  # 选择分隔图像像素点
        new_data[index_x, index_y, 0] = rgb[0]
        new_data[index_x, index_y, 1] = rgb[1]
        new_data[index_x, index_y, 2] = rgb[2]

    else:
        kernel = np.ones((3, 3))
        new_data = np.stack([data, data, data], axis=2)
        hsi = np.array([1, 0, 0])
        rgb = hsi * (max_value - min_value) + min_value
        boundary = binary_dilation(
            input=roi[0], structure=kernel, iterations=1)
        boundary = boundary - roi[0]
        index_x, index_y = np.where(boundary == 1)
        new_data[index_x, index_y, 0] = rgb[0]
        new_data[index_x, index_y, 1] = rgb[1]
        new_data[index_x, index_y, 2] = rgb[2]
    return new_data


def Merge3DImageWithROI(data, roi, overlap=False):
    # roi.shape 512 512 689

    # new_data.shape 689 512 512 3
    new_data = np.zeros((data.shape[2], data.shape[0], data.shape[1], 3))
    max_value = np.max(data)
    min_value = np.min(data)
    for slice_index in range(data.shape[2]):  # 遍历原图所有切片
        slice = data[..., slice_index]  # 即一张512*512的二维原数据切片
        roi_list = []  # 一张512*512的二维分隔数据切片
        roi_list.append(roi[..., slice_index])
        new_data[slice_index, ...] = MergeImageWithROI(
            slice, roi_list, overlap=overlap, max_value=max_value, min_value=min_value)

    return new_data


def Imshow(origin, roi=None, mode=False, overlap=False):
    '''

    :param origin: nii原图
    :param ori:    nii分割图
    :param mode:  显示处理模式 True为融合图 FALSE为单张图 默认为单张图
    :param overlap: 图片融合模式 True为覆盖 False为边界线 默认为边界线
    :return: numpy数组 按z-y-x格式返回图像数据

    单张图片为3维数据 融合图片为4维
    '''
    min_v = -200
    max_v = 200

    origin[origin > max_v] = max_v
    origin[origin < min_v] = min_v
    origin[origin == -2000] = 0

    origin = origin.transpose(1, 2, 0)

    # 如果存在roi分隔图 对图像进行融合与边缘显示
    if mode and isinstance(roi, list) or isinstance(roi, type(origin)):
        roi = roi.transpose(1, 2, 0)
        origin = Merge3DImageWithROI(origin, roi, overlap=overlap)

    # print(np.ndim(origin))  # nii图为4 单图为3
    # print(origin.shape)  # nii融合图情况下为 689 512 512 3
    if np.ndim(origin) == 3:
        # print(origin.shape)
        origin = np.swapaxes(origin, 0, 1)
        # print(origin.shape)
        origin = np.transpose(origin)
        # print(origin.shape)

    return origin


def Imshow3D(origin):
    '''

    :param origin: nii原图
    :return: numpy 4维数组  返回 x-y-z-rgb
    '''
    # 设定hu值范围为肝脏窗口
    min_v = -200
    max_v = 200

    origin[origin > max_v] = max_v
    origin[origin < min_v] = min_v
    origin[origin == -2000] = 0

    origin = origin.transpose(1, 2, 0)

    # create color image channels
    data = np.empty(origin.shape + (4,), dtype=np.ubyte)
    data[..., 0] = origin * (255. / (origin.max() / 1))
    data[..., 1] = data[..., 0]
    data[..., 2] = data[..., 0]
    data[..., 3] = data[..., 0]
    data[..., 3] = (data[..., 3].astype(float) / 255.) ** 2 * 255

    # xyz坐标轴
    data[:, 0, 0] = [255, 0, 0, 255]
    data[0, :, 0] = [0, 255, 0, 255]
    data[0, 0, :] = [0, 0, 255, 255]

    return data
