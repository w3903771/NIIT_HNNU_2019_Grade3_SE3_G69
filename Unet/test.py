import os
import sys

import SimpleITK as sitk
import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from utils.common import posthandle

import config
from Dataloder.dataloder_test import Test_Datasets
from models import ResUNet


def predict_one_img(model, img_dataset):
    dataloader = DataLoader(
        dataset=img_dataset,
        batch_size=1,
        num_workers=0,
        shuffle=False)
    model.eval()

    with torch.no_grad():
        for data in tqdm(dataloader, total=len(dataloader)):
            data = data.to(device)
            output = model(data)
            img_dataset.update_result(output.detach().cpu())

    pred = img_dataset.recompone_result()
    pred = torch.argmax(pred, dim=1)
    pred = np.asarray(pred.numpy(), dtype='uint8')
    pred = sitk.GetImageFromArray(np.squeeze(pred, axis=0))

    return pred


if __name__ == '__main__':
    '''
        通过命令行 参数test_data_path指定到具体的nii测试文件路径 注意路径采用绝对路径
        如 python test.py --test_data_path 1.nii --cpu
        生成结果保存在同级文件夹result下 以result-id.nii.gz命名
    '''

    if getattr(sys, 'frozen', False):
        code_path = os.path.dirname(sys.executable)
    elif __file__:
        code_path = os.path.dirname(os.path.abspath(__file__))

    args = config.args
    model_path = os.path.join(code_path, 'experiments', args.save)

    device = torch.device('cpu')
    model = ResUNet(
        in_channel=1,
        out_channel=args.n_labels,
        training=False).to(device)
    ckpt = torch.load('{}/best_model.pth'.format(model_path))
    # ckpt = torch.load('{}/best_model.pth'.format(model_path), map_location='cpu') 报错用这个
    model.load_state_dict(ckpt['net'])

    # 测试文件与目录路径
    file_path = args.test_data_path
    folder_path = os.path.dirname(file_path)
    # 在测试文件同级建立result文件夹存放结果
    result_save_path = '{}/result'.format(folder_path)
    if not os.path.exists(result_save_path):
        os.mkdir(result_save_path)

    datasets = Test_Datasets(args.test_data_path, args=args)
    for img_dataset, file_idx in datasets:
        pred_img = predict_one_img(model, img_dataset)
        pred_array = sitk.GetArrayFromImage(pred_img)
        pred_array = posthandle(pred_array)
        pred_img = sitk.GetImageFromArray(pred_array)
        sitk.WriteImage(
            pred_img,
            os.path.join(
                result_save_path,
                'result-' +
                file_idx +
                '.gz'))
