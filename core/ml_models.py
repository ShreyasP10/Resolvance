import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualDenseBlock(nn.Module):
    def __init__(self, nf=64, gc=32, bias=True):
        super().__init__()
        self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1, bias=bias)
        self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1, bias=bias)
        self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1, bias=bias)
        self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1, bias=bias)
        self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1, bias=bias)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x

class RRDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.rdb1 = ResidualDenseBlock(nf, gc)
        self.rdb2 = ResidualDenseBlock(nf, gc)
        self.rdb3 = ResidualDenseBlock(nf, gc)

    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x

class NChannelRRDBNet(nn.Module):
    """
    N-Channel RRDB Network for Super Resolution.
    Supports dynamic in_nc and out_nc to handle 4-band or 8-band Sentinel imagery.
    Includes MC-Dropout layer in the tail for uncertainty estimation.
    """
    def __init__(self, in_nc=4, out_nc=4, nf=64, nb=5, scale=3, dropout_p=0.2):
        super().__init__()
        self.scale = scale
        self.in_nc = in_nc
        self.out_nc = out_nc
        
        self.conv_first = nn.Conv2d(in_nc, nf, 3, 1, 1)
        self.body = nn.Sequential(*[RRDB(nf=nf) for _ in range(nb)])
        self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        
        # Upsampling
        self.upconv = nn.Conv2d(nf, nf, 3, 1, 1)
        
        # Dropout for Monte Carlo Uncertainty Estimation
        self.dropout = nn.Dropout(p=dropout_p)
        self.conv_last = nn.Conv2d(nf, out_nc, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        # x: B x C x H x W
        feat = self.conv_first(x)
        body_feat = self.conv_body(self.body(feat))
        feat = feat + body_feat
        
        # Upsample by scale factor
        feat = F.interpolate(feat, scale_factor=self.scale, mode='nearest')
        feat = self.lrelu(self.upconv(feat))
        
        # Tail with dropout
        feat = self.dropout(feat)
        out = self.conv_last(feat)
        return out


def sam_loss(output, target):
    """
    Spectral Angle Mapper Loss.
    Penalizes spectral distortion across N-bands.
    """
    # output, target: (B, C, H, W)
    dot = (output * target).sum(dim=1)
    norm_out = torch.norm(output, dim=1)
    norm_tar = torch.norm(target, dim=1)
    # Add epsilon to avoid division by zero
    sam = torch.acos(torch.clamp(dot / (norm_out * norm_tar + 1e-8), -1.0, 1.0))
    return sam.mean()

class CombinedSRLoss(nn.Module):
    """
    Total Loss = L1 Loss + lambda1 * Perceptual Loss + lambda2 * SAM Loss
    (Perceptual loss stubbed as MSE on downscaled image if VGG not available for N-channels,
    or using 3 bands if standard VGG is used.)
    """
    def __init__(self, lambda_l1=1.0, lambda_perceptual=0.1, lambda_sam=0.05):
        super().__init__()
        self.lambda_l1 = lambda_l1
        self.lambda_perceptual = lambda_perceptual
        self.lambda_sam = lambda_sam
        self.l1 = nn.L1Loss()
        
    def forward(self, output, target):
        loss_l1 = self.l1(output, target)
        loss_sam = sam_loss(output, target)
        
        # Standard perceptual loss requires VGG (RGB).
        # For N-channels, we approximate perceptual consistency by comparing local gradients or downsampled features.
        # Here we use an L2 penalty on edges as a lightweight proxy for N-channel perceptual loss.
        # Compute edges using simple differences
        diff_h_out = output[:, :, 1:, :] - output[:, :, :-1, :]
        diff_h_tar = target[:, :, 1:, :] - target[:, :, :-1, :]
        diff_w_out = output[:, :, :, 1:] - output[:, :, :, :-1]
        diff_w_tar = target[:, :, :, 1:] - target[:, :, :, :-1]
        loss_perceptual = F.mse_loss(diff_h_out, diff_h_tar) + F.mse_loss(diff_w_out, diff_w_tar)
        
        return self.lambda_l1 * loss_l1 + self.lambda_perceptual * loss_perceptual + self.lambda_sam * loss_sam
