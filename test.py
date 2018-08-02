import os
import numpy as np
import os.path as osp
from argparse import ArgumentParser
from pprint import pprint
import sys

import skimage.io as io
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(osp.join(BASE_DIR, 'lib'))

import prosr
from prosr import Phase
from prosr.data import DataLoader, Dataset
from prosr.logger import info
from prosr.metrics import eval_psnr_and_ssim
from prosr.utils import get_filenames, tensor2im

def print_evaluation(filename, psnr, ssim, iid=None, n_images=None):
    if iid and n_images:
        print('[{:03d}/{:03d}] {:10s} | psnr: {:.2f} | ssim: {:.2f}'.format(iid,n_images, osp.splitext(filename)[0], psnr, ssim))
    else:
        print('[{:7s}]            | psnr: {:.2f} | ssim: {:.2f}'.format(filename, psnr, ssim))


def parse_args():
    parser = ArgumentParser(description='ProSR')
    parser.add_argument('-c', '--checkpoint', type=str, required=True, help='Checkpoint')
    parser.add_argument('-i', '--input', help='Input images, either list or path to folder. If not given, use bicubically downsampled target image as input',
        type=str, nargs='*',required=False,default=[])
    parser.add_argument('-t','--target', help='Target images, either list or path to folder', type=str,nargs='*',required=False,default=[])
    parser.add_argument('-u','--upscale-factor',help='upscale ratio e.g. 2, 4 or 8', type=int,required=True)
    parser.add_argument('-f', '--fmt', help='Image file format', type=str, default='*')
    parser.add_argument('-o', '--output-dir', help='Output folder.', type=str, default='./')

    args = parser.parse_args()

    args.input = get_filenames(args.input, args.fmt)
    args.target = get_filenames(args.target, args.fmt)

    # if not len(args.input):
    #     error("Did not find images in: {}".format(args.input))

    return args


if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_args()

    checkpoint = torch.load(args.checkpoint)
    cls_model = getattr(prosr.models, checkpoint['class_name'])

    model = cls_model(**checkpoint['params']['G'])
    model.load_state_dict(checkpoint['state_dict'])

    info('Phase: {}'.format(Phase.TEST))
    info('Checkpoint: {}'.format(osp.basename(args.checkpoint)))
    pprint(checkpoint['params'])

    model.eval()

    if torch.cuda.is_available():
        model = model.cuda()

    # TODO Change
    checkpoint['params']['data']['crop_size'] = None
    dataset = Dataset(Phase.TEST, args.input, args.target, args.upscale_factor, **checkpoint['params']['data'])

    data_loader = DataLoader(dataset, batch_size=1)

    mean = checkpoint['params']['data']['mean']
    stddev = checkpoint['params']['data']['stddev']

    if not osp.isdir(args.output_dir):
        os.makedirs(args.output_dir)

    with torch.no_grad():
        if len(args.target):
            psnr_mean = 0
            ssim_mean = 0

        for iid,data in enumerate(data_loader):
            output = model(data['input'].cuda(), args.upscale_factor).cpu() + data['bicubic']
            sr_img = tensor2im(output, mean, stddev)
            if 'target' in data:
                hr_img = tensor2im(data['target'], mean, stddev)
                psnr_val, ssim_val = eval_psnr_and_ssim(sr_img, hr_img, args.upscale_factor)
                print_evaluation(
                    osp.basename(data['input_fn'][0]), psnr_val, ssim_val,iid+1,len(dataset))
                psnr_mean += psnr_val
                ssim_mean += ssim_val
            else:
                print_evaluation(
                    osp.basename(data['input_fn'][0]),np.nan,np.nan,iid,len(dataset))
            io.imsave(
                osp.join(args.output_dir, osp.basename(data['input_fn'][0])),
                sr_img)

        if len(args.target):
            psnr_mean /= len(dataset)
            ssim_mean /= len(dataset)
            print_evaluation("average", psnr_mean, ssim_mean)
