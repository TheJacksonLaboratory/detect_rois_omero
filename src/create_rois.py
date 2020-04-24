def create_rois(image, size_thresh, method_thresh, closing):
    from skimage.transform import rescale, downscale_local_mean
    from skimage.color import rgb2gray,label2rgb
    from skimage.filters import threshold_otsu, threshold_triangle
    from skimage.util import invert
    from skimage.morphology import diamond, binary_closing
    from skimage.measure import regionprops, label
    import numpy as np
    from skimage.io import imshow
    import matplotlib.pyplot as plt

    im = rgb2gray(image)
    im = invert(im)
    
    if method_thresh == 'otsu':
        im_thresh = im > threshold_otsu(im)
    elif method_thresh == 'triangle':
        im_thresh = im > threshold_triangle(im)
    elif method_thresh == 'yen':
        im_thresh = im > threshold_yen(im)
    elif method_thresh == 'li':
        im_thresh = im > threshold_li(im)
    im_thresh = binary_closing(im_thresh, diamond(closing))
    im_lab = label(im_thresh)
    for i in range(1, im_lab.max()+1):
        coords = np.where(im_lab == i)
        if len(coords[0]) < size_thresh:
            im_lab[coords] = 0
    im_lab_color = label2rgb(im_lab, bg_label = 0, bg_color=(0,0,0))
    # imshow(im_lab_color)
    # plt.show()    
    regions = regionprops(im_lab)
    return regions



if __name__ == "__main__":
    import os
    from create_session import create_json_session, create_blitz_session
    from retrieve_image import retrieve_image
    from save_rois import save_rois, get_image
    


    WEB_HOSTNAME = os.environ['OMERO_WEB_HOSTNAME']
    HOSTNAME = os.environ['OMERO_HOSTNAME']
    USERNAME = os.environ['OMERO_ADMIN_USER']
    PASSWORD = os.environ['OMERO_ADMIN_PASSWORD']
    img_id = 1
    scale_factor = 64
    login_rsp, session, base_url = create_json_session(WEB_HOSTNAME, USERNAME, PASSWORD)
    img = retrieve_image(session, base_url, img_id, scale_factor)
    regions = create_rois(img, 200, 'triangle', 5)
    conn = create_blitz_session(HOSTNAME, USERNAME, PASSWORD)
    image = get_image(conn, img_id)
    save_rois(image, regions, scale_factor)
    conn.close()