"""Bilinear sampling support, not a claim about a network's receptive field."""
import numpy as np


def sampling_support(valid):
    valid=np.asarray(valid)
    if valid.shape!=(900,900) or valid.dtype!=bool:
        raise ValueError('native 900x900 boolean support required')
    source=(np.arange(448)+.5)*900/448-.5
    lo=np.floor(source).astype(int)
    hi=lo+1
    # The fixed ratio has no integer source positions: all four weights > 0.
    return (valid[np.ix_(lo,lo)] & valid[np.ix_(lo,hi)] &
            valid[np.ix_(hi,lo)] & valid[np.ix_(hi,hi)])


def inspect_support(valid, shifts):
    resized=sampling_support(valid)
    invalid=[int((~resized[32:416,32:416]).sum())]
    for s in shifts:
        dy,dx=s['dy'],s['dx']
        if not isinstance(dy,int) or not isinstance(dx,int) or max(abs(dy),abs(dx))>32:
            raise ValueError('invalid frozen displacement')
        invalid.append(int((~resized[32+dy:416+dy,32+dx:416+dx]).sum()))
    if any(invalid):
        raise ValueError('original full 384 core lacks sampling support; no cropping or member replacement')
    return {'native_invalid':int((~valid).sum()),'resized_invalid':int((~resized).sum()),
            'core_invalid':invalid,'limitation':'No-data outside these samples can affect predictions through the network receptive field.'}


def read_input(path,tile,shifts):
    import rasterio
    import torch
    import torch.nn.functional as F
    x0,y0=map(int,tile.split('_'))
    with rasterio.open(path) as ds:
        if (ds.width,ds.height,ds.count)!=(900,900,4) or ds.crs.to_epsg()!=32616:
            raise ValueError('wrong native raster grid')
        if not np.allclose(tuple(ds.transform)[:6],(.5,0,x0,0,-.5,y0+450),rtol=0,atol=1e-8):
            raise ValueError('native ground identity mismatch')
        raw=ds.read((1,2,3)).astype(np.float32)
        if not np.isfinite(raw).all():
            raise ValueError('nonfinite input cannot be silently filled')
        valid=np.all(ds.read_masks((1,2,3))>0,axis=0)
        if ds.nodata is not None:
            valid &= ~np.any(raw==ds.nodata,axis=0)
    info=inspect_support(valid,shifts)
    info['invalid_nonzero_rgb_values']=int(np.count_nonzero(raw[:,~valid]))
    # Native stored values are kept, including missing-data zeroes. No inpainting,
    # masking of probabilities, or changed tensor normalization is introduced.
    image=F.interpolate(torch.from_numpy(raw)[None],size=(448,448),mode='bilinear',align_corners=False)[0]
    return image.numpy().astype(np.float16).astype(np.float32),info
