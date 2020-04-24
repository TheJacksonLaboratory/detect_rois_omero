def create_rois(image, size_thresh, closing):
    from skimage.transform import rescale, downscale_local_mean
    from skimage.color import rgb2gray
    from skimage.filters import threshold_otsu
    from skimage.util import invert
    from skimage.morphology import diamond, binary_closing
    from skimage.measure import regionprops, label
    import numpy as np

    im = rgb2gray(image)
    im = invert(im)
    
    im_thresh = im > threshold_otsu(im)
    im_thresh = binary_closing(im_thresh, diamond(closing))
    im_lab = label(im_thresh)
    for i in range(1, im_lab.max()+1):
        coords = np.where(im_lab == i)
        if len(coords[0]) < size_thresh:
            im_lab[coords] = 0
        
    regions = regionprops(im_lab)
    return regions

