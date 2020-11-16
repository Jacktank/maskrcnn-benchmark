from torch import nn
from torch.nn import functional as F

from maskrcnn_benchmark.modeling import registry
from maskrcnn_benchmark.modeling.poolers import Pooler

from maskrcnn_benchmark.layers import Conv2d


@registry.ROI_GEO_ATTR_FEATURE_EXTRACTORS.register("GEOATTRRCNNFeatureExtractor")
class GEOATTRRCNNFeatureExtractor(nn.Module):
    def __init__(self, cfg, in_channels):
        super(GEOATTRRCNNFeatureExtractor, self).__init__()

        resolution = cfg.MODEL.ROI_GEO_ATTR_HEAD.POOLER_RESOLUTION
        scales = cfg.MODEL.ROI_GEO_ATTR_HEAD.POOLER_SCALES
        sampling_ratio = cfg.MODEL.ROI_GEO_ATTR_HEAD.POOLER_SAMPLING_RATIO
        pooler = Pooler(
            output_size=(resolution, resolution),
            scales=scales,
            sampling_ratio=sampling_ratio,
        )
        self.pooler = pooler

        input_features = in_channels
        layers = cfg.MODEL.ROI_GEO_ATTR_HEAD.CONV_LAYERS
        next_feature = input_features
        self.blocks = []
        for layer_idx, layer_features in enumerate(layers, 1):
            layer_name = "conv_fcn{}".format(layer_idx)
            module = Conv2d(next_feature, layer_features, 3, stride=1, padding=1)
            nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
            nn.init.constant_(module.bias, 0)
            self.add_module(layer_name, module)
            next_feature = layer_features
            self.blocks.append(layer_name)

        self.pooling_last = nn.AvgPool2d(resolution, stride=1)
        self.out_channels = layer_features

    def forward(self, x, proposals):
        x = self.pooler(x, proposals)
        for layer_name in self.blocks:
            x = F.relu(getattr(self, layer_name)(x))
        x = self.pooling_last(x).squeeze()
        return x

def make_roi_geo_attr_feature_extractor(cfg, in_channels):
    func = registry.ROI_GEO_ATTR_FEATURE_EXTRACTORS[
        cfg.MODEL.ROI_GEO_ATTR_HEAD.FEATURE_EXTRACTOR
    ]
    return func(cfg, in_channels)
