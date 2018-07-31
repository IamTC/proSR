from __future__ import print_function

import collections
import glob
import os

import numpy as np
from PIL import Image

IMG_EXTENSIONS = [
    '.jpg',
    '.JPG',
    '.jpeg',
    '.JPEG',
    '.png',
    '.PNG',
    '.ppm',
    '.PPM',
    '.bmp',
    '.BMP',
]


def get_filenames(source, image_format=None):
    # Seamlessy load single file, list of files and files from directories.
    source_fns = []
    if isinstance(source, str):
        if os.path.isdir(source):
            source_fns = sorted(
                glob.glob("{}/*.{}".format(source, image_format)))
        elif os.path.isfile(source):
            source_fns = [source]
        assert(all([is_image_file(f) for f in source_fns])), "Given files contain files with unsupported format"
    elif len(source) and isinstance(source[0], str):
        for s in source:
            source_fns.extend(get_filenames(s, image_format=image_format))
    return source_fns


def is_image_file(filename):
    return any(filename.endswith(extension) for extension in IMG_EXTENSIONS)


# Converts a Tensor into a Numpy array
# |imtype|: the desired type of the converted numpy array
def tensor2im(image_tensor, mean=(0.5, 0.5, 0.5), stddev=2.):
    image_numpy = image_tensor[0].cpu().float().numpy()
    image_numpy = (
        np.transpose(image_numpy, (1, 2, 0)) * stddev + np.array(mean)) * 255.0
    image_numpy = image_numpy.clip(0, 255)
    return np.around(image_numpy).astype(np.uint8)

def mod_crop(im, scale):
    h, w = im.shape[:2]
    # return im[(h % scale):, (w % scale):, ...]
    return im[:h - (h % scale), :w - (w % scale), ...]

def print_network(net):
    num_params = 0
    for param in net.parameters():
        num_params += param.numel()
    print(net)
    print('Total number of parameters: %d' % num_params)


def save_image(image_numpy, image_path, mode=None):
    image_pil = Image.fromarray(image_numpy, mode).convert('RGB')
    image_pil.save(image_path)


def info(object, spacing=10, collapse=1):
    """Print methods and doc strings.
    Takes module, class, list, dictionary, or string."""
    methodList = [
        e for e in dir(object)
        if isinstance(getattr(object, e), collections.Callable)
    ]
    processFunc = collapse and (lambda s: " ".join(s.split())) or (lambda s: s)
    print("\n".join([
        "%s %s" % (method.ljust(spacing),
                   processFunc(str(getattr(object, method).__doc__)))
        for method in methodList
    ]))


def spatial_resize(x, size=None, scale_factor=None):
    import torch.nn.functional as F
    # scale_factor has to be integer
    assert (size is not None) or (
        scale_factor is not None), 'must specify scale or scale_factor'
    assert (size is None) or (scale_factor is
                              None), 'cannot specify both size and scale_factor'
    if size is None:
        h, w = x.size()[-2:]
        size = int(h * scale_factor), int(w * scale_factor)
    if h < size[0] and w < size[0]:
        return F.upsample(x, size=size, mode='bilinear',align_corners=True)
    else:
        if size[0] % h != 0 or size[1] % w != 0:
            return F.adaptive_avg_pool2d(x, output_size=size)
        else:
            if scale_factor is None:
                assert (size[0] // h) == (size[1] // w), \
                    'scale factor is the same for both dimensions'
                scale_factor = size[0] / h
            return F.avg_pool2d(x, int(1 / scale_factor))


def mkdirs(paths):
    if isinstance(paths, list) and not isinstance(paths, str):
        for path in paths:
            mkdir(path)
    else:
        mkdir(paths)


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def print_current_errors(epoch, i, errors, t, log_name=None):
    message = '(epoch: %d, iters: %d, time: %.3f) ' % (epoch, i, t)
    for k, v in errors.items():
        message += '%s: %.3f ' % (k, v)

    print(message)
    if log_name is not None:
        with open(log_name, "a") as log_file:
            log_file.write('%s\n' % message)


def crop_boundaries(im, cs):
    if cs > 1:
        return im[cs:-cs, cs:-cs, ...]
    else:
        return im
