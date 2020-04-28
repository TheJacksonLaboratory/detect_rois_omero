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
    #im_lab_color = label2rgb(im_lab, bg_label = 0, bg_color=(0,0,0))
    # imshow(im_lab_color)
    # plt.show()    
    regionproperties = regionprops(im_lab)
    regions = []
    for r in regionproperties:
        regions.append(r.bbox)
    regions = prune_regions(regions)
    return regions


def prune_regions(regions):
    restart = True
    while restart:
        restart = False
        for region in regions:   
            if check_aspect_ratio(region, 4):
                regions.remove(region)
                restart = True
                break
            
    restart = True
    willmerge = []
    mergee = []
    for region in regions:
        intersection = check_intersections(region,regions)
        if intersection:
            willmerge.append(True)
            mergee.append(intersection)
            #regions = merge_regions(region,regions,intersection)
            #restart = True
            
        else:
            willmerge.append(False)
            mergee.append(intersection)
    counter = 0
    for region in regions:
        if willmerge[counter]:
            regions = merge_regions(region,regions,mergee[counter])
        counter = counter + 1
        
    return list(set(regions))

def check_aspect_ratio(region, threshold):
    bbox = region
    ratio = (bbox[2]-bbox[0])/(bbox[3]-bbox[1])
    if ratio > threshold or ratio < (1/threshold):
        return True

def check_intersections(region, regions):
    int_areas = []
    bbox = region
    for r in regions:
        r_bbox = r
        if (r_bbox == bbox):
            int_areas.append(0)
            continue
        if bbox[0] >= r_bbox[2] or r_bbox[0] >= bbox[2]:
            int_areas.append(0) 
            continue
        if bbox[1] >= r_bbox[3] or r_bbox[1] >= bbox[3]:
            int_areas.append(0) 
            continue
        x1 = max(min(bbox[0],r_bbox[2]), min(r_bbox[0],bbox[2]))
        y1 = max(min(bbox[1],r_bbox[3]), min(r_bbox[1],bbox[3]))
        x2 = min(max(bbox[0],r_bbox[2]), max(r_bbox[0],bbox[2]))
        y2 = min(max(bbox[1],r_bbox[3]), max(r_bbox[1],bbox[3]))
        if (x2 > x1) and (y2 > y1):
            int_areas.append((x2-x1)*(y2-y1))
        else:
            int_areas.append(0)
    
    return int_areas.index(max(int_areas))


def merge_regions(region,regions,intersection):
    other = regions[intersection]
    x1 = min(region[0],other[0])
    y1 = min(region[1], other[1])
    x2 = max(region[2], other[2])
    y2 = max(region[3], other[3])
    regions[intersection] = (x1,y1,x2,y2)
    regions[regions.index(region)] = (x1,y1,x2,y2)
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