import kornia
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from torchvision.utils import save_image
import utils.im_manipulation as ImageManipulator


class My_Laplacian(nn.Module):

    def __init__(self,
                 mode: str = 'sobel',
                 order: int = 1,
                 normalized: bool = True) -> None:
        super(My_Laplacian, self).__init__()
        self.normalized: bool = normalized
        self.order: int = order
        self.mode: str = mode


        kernel_x: torch.Tensor = torch.tensor([
        [-1., -1., -1.],
        [-1., 8., -1.],
        [-1., -1., -1.],
    ])
        kernel_y: torch.Tensor = kernel_x.transpose(0, 1)
        self.kernel = torch.stack([kernel_x, kernel_y])

        return

    def __repr__(self) -> str:
        return self.__class__.__name__ + '('\
            'order=' + str(self.order) + ', ' + \
            'normalized=' + str(self.normalized) + ', ' + \
            'mode=' + self.mode + ')'

    def forward(self, input: torch.Tensor) -> torch.Tensor:  # type: ignore
        if not torch.is_tensor(input):
            raise TypeError("Input type is not a torch.Tensor. Got {}"
                            .format(type(input)))
        if not len(input.shape) == 4:
            raise ValueError("Invalid input shape, we expect BxCxHxW. Got: {}"
                             .format(input.shape))
        # prepare kernel
        b, c, h, w = input.shape
        tmp_kernel: torch.Tensor = self.kernel.to(input.device).to(input.dtype).detach()
        kernel: torch.Tensor = tmp_kernel.unsqueeze(1).unsqueeze(1)

        # convolve input tensor with sobel kernel
        kernel_flip: torch.Tensor = kernel.flip(-3)
        # Pad with "replicate for spatial dims, but with zeros for channel
        spatial_pad = [self.kernel.size(1) // 2,
                       self.kernel.size(1) // 2,
                       self.kernel.size(2) // 2,
                       self.kernel.size(2) // 2]
        out_channels: int = 3 if self.order == 2 else 2
        padded_inp: torch.Tensor = F.pad(input.reshape(b * c, 1, h, w), spatial_pad, 'replicate')[:, :, None]
        return F.conv3d(padded_inp, kernel_flip, padding=0).view(b, c, out_channels, h, w)

'''

def Laplacian(x):
    weight = torch.tensor([
        [[[-1., 0., 0.], [0., -1., 0.], [0., 0., -1.]], [[-1., 0., 0.], [0., -1., 0.], [0., 0., -1.]],
         [[-1., 0., 0.], [0., -1., 0.], [0., 0., -1.]]],
        [[[-1., 0., 0.], [0., -1., 0.], [0., 0., -1.]], [[8., 0., 0.], [0., 8., 0.], [0., 0., 8.]],
         [[-1., 0., 0.], [0., -1., 0.], [0., 0., -1.]]],
        [[[-1., 0., 0.], [0., -1., 0.], [0., 0., -1.]], [[-1., 0., 0.], [0., -1., 0.], [0., 0., -1.]],
         [[-1., 0., 0.], [0., -1., 0.], [0., 0., -1.]]]
    ])

    #tensorification = transforms.Compose([transforms.ToTensor()])
    #weight = tensorification(weight)

    frame = torch.nn.Conv2d(x, weight, [1, 1, 1, 1], padding='SAME')
    # frame = tf.cast(((frame - tf.reduce_min(frame)) / (tf.reduce_max(frame) - tf.reduce_min(frame))) * 255, tf.uint8)
    return frame
'''

def get_laplacian(target_img):
    #x_gray = kornia.rgb_to_grayscale(target_img.float() / 255.)
    x_gray = kornia.rgb_to_grayscale(target_img.float())
    grads: torch.Tensor = kornia.spatial_gradient(x_gray, order=1, normalized=False)  # BxCx2xHxW
    grads_x = grads[:, :, 0]
    return grads_x

def get_laplacian_alt(target_img1):
    target_img = target_img1.unsqueeze(0)
    x_gray = kornia.rgb_to_grayscale(target_img.float())
    grads: torch.Tensor = kornia.spatial_gradient(x_gray, order=1, normalized=False)  # BxCx2xHxW
    grads_x = grads[:, :, 0]
    return grads_x[0]

#USING MY_LAPLACIAN INSTEAD OF KORNIA
def get_laplacian_alt_old(target_img1):
    target_img = target_img1.unsqueeze(0)
    x_gray = kornia.rgb_to_grayscale(target_img.float())
    grads = My_Laplacian("", 1, False)(x_gray)
    grads_x = grads[:, :, 0]
    return grads_x[0]


if __name__ == '__main__':
    mean = np.asarray([0.4488, 0.4371, 0.404])
    std = np.asarray([0.0039215, 0.0039215, 0.0039215])

    denormalize = transforms.Normalize((-1 * mean / std), (1.0 / std))

    normalize_fn = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4488, 0.4371, 0.404),
                             (0.0039215, 0.0039215, 0.0039215))
    ])

    target_img = ImageManipulator.image_loader(
        "/s/chopin/e/proj/sustain/sapmitra/super_resolution/SRImages/trai/9xjm5_20190407.tif")

    w, h = target_img.size
    # IF IMAGE PIXELS IS NOT DIVISIBLE BY SCALE, CROP THE BALANCE
    target_img = target_img.crop((0, 0, w - w % 8, h - h % 8))

    target_img, off_y, off_x = ImageManipulator.center_crop(256, target_img)
    target_img = normalize_fn(target_img)
    target_img = target_img.unsqueeze_(0)

    x_gray = kornia.rgb_to_grayscale(target_img.float())
    grads = My_Laplacian("", 1, False)(x_gray)
    print(grads.size())
    grads_x = grads[:, :, 0]
    save_image(denormalize(target_img[0]), '/s/chopin/e/proj/sustain/sapmitra/super_resolution/SRImages/ac1.tif',
               normalize=False)
    save_image(grads_x, '/s/chopin/e/proj/sustain/sapmitra/super_resolution/SRImages/ac2.tif',
               normalize=False)








if __name__ == '__main1__':
    #https://discuss.pytorch.org/t/understanding-transform-normalize/21730

    mean = np.asarray([0.4488, 0.4371, 0.404])
    std = np.asarray([0.0039215, 0.0039215, 0.0039215])

    denormalize = transforms.Normalize((-1 * mean / std), (1.0 / std))


    normalize_fn = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4488, 0.4371, 0.404),
                            (0.0039215, 0.0039215, 0.0039215))
    ])

    target_img = ImageManipulator.image_loader("/s/chopin/e/proj/sustain/sapmitra/super_resolution/SRImages/trai/9xjm5_20190407.tif")

    w, h = target_img.size
    # IF IMAGE PIXELS IS NOT DIVISIBLE BY SCALE, CROP THE BALANCE
    target_img = target_img.crop((0, 0, w - w % 8, h - h % 8))

    target_img, off_y, off_x = ImageManipulator.center_crop(256, target_img)
    target_img = normalize_fn(target_img)
    target_img = target_img.unsqueeze_(0)

    #x_gray = kornia.rgb_to_grayscale(target_img.float() / 255.)
    x_gray = kornia.rgb_to_grayscale(target_img.float())
    grads: torch.Tensor = kornia.spatial_gradient(x_gray, order=1, normalized=False)  # BxCx2xHxW
    grads_x = grads[:, :, 0]
    grads_y = grads[:, :, 1]
    #
    img_edges_3c = torch.cat((grads_x, grads_x,grads_x), 1)
    #img_edges_3c = normalize_fn1(img_edges_3c)

    grads_x_de = denormalize(img_edges_3c[0])

    #x_fa = get_laplacian(target_img)
    tmp = target_img - grads_x

    print(torch.max(grads_x))
    print(torch.max(target_img))
    save_image(denormalize(target_img[0]), '/s/chopin/e/proj/sustain/sapmitra/super_resolution/SRImages/ffx.tif', normalize=False)
    save_image(denormalize((tmp)[0]), '/s/chopin/e/proj/sustain/sapmitra/super_resolution/SRImages/ffy.tif', normalize=False)
    save_image(denormalize((tmp + grads_x)[0]), '/s/chopin/e/proj/sustain/sapmitra/super_resolution/SRImages/ffxx.tif',
               normalize=False)
    save_image(grads_x_de, '/s/chopin/e/proj/sustain/sapmitra/super_resolution/SRImages/ffz.tif',
               normalize=False)
