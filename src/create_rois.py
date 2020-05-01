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
    regions = order_regions(regions)
    #return []
    return regions

def distance(p1, p2):
    import numpy as np
    d = np.sqrt(((p2[0] - p1[0]) ** 2) + ((p2[1] - p1[1]) ** 2))
    return d

def weighted_distance(p1, p2, weight):
    import numpy as np
    d = np.sqrt(((p2[0] - p1[0]) ** 2) + ((weight * (p2[1] - p1[1])) ** 2))
    return d

def generate_centroids(regions):
    centroids = []
    if regions != []:
        for region in regions:
            centroids.append(((region[1]+ region[3])/2, (region[0]+ region[2])/2))
    return centroids

def order_regions(regions):
    import networkx as nx
    import matplotlib.pyplot as plt
    import numpy as np
    if regions != []:
        # regions: y1 x2 y2 x2
        # centroids: xmean, ymean
        #while regions != []:
        centroids = generate_centroids(regions)
        sums = [c[0]+c[1] for c in centroids]
        topleft = sums.index(min(sums))
        c_topleft = centroids[topleft]
        r_topleft = regions[topleft]
        regions.remove(r_topleft)
        centroids.remove(c_topleft)
        dists = [weighted_distance(x,c_topleft,20) for x in centroids]
        
        
        centroids = [x for _,x in sorted(zip(dists,centroids))]
        regions = [x for _,x in sorted(zip(dists,regions))]
        dists = [x for x in sorted(dists)]
        differences = [dists[i+1]-dists[i] for i in range(len(dists)-1)]
        line_dividers = differences > 1.5*np.std(differences)
        line_dividers = np.insert(line_dividers,0,False)

        lines = []
        lines.append([r_topleft])
        for i in range(len(regions)):
            if line_dividers[i]:
                lines.append([])
            lines[-1].append(regions[i])
            
        results = []
        for line in lines:
            line_centr = generate_centroids(line)
            xvals = [x[0] for x in line_centr]  
            results.append([x for _,x in sorted(zip(xvals,line))])  
        return [item for sublist in results for item in sublist]
    else:
        return []

def prune_regions(regions):
    restart = True
    while restart:
        restart = False
        for region in regions:   
            if check_aspect_ratio(region, 4):
                regions.remove(region)
                restart = True
                break
            
    regions = cluster_regions(regions)
    
    
    # add code to order ROIs using Dave's networkx thing as a base

    return(regions)


def cluster_regions(regions):
    import networkx as nx
    willmerge = []
    mergee = []
    results = []
    for region in regions:
        intersection = check_intersections(region,regions)
        if intersection != -1:
            willmerge.append(True)
            mergee.append(intersection)
            
            
        else:
            willmerge.append(False)
            mergee.append(intersection)
            results.append(region)
    

    # code for merging clusters go here
    G = nx.Graph()
    edges = []
    count = 0
    for roi in range(len(mergee)):
        if willmerge[count] == True:
            edges.append((count,mergee[count]))
        count = count + 1
    G.add_edges_from(edges)
    for a in nx.connected_components(G):
        roi = merge_cluster(list(a), regions)
        results.append(roi)
    
    return results


def merge_cluster(indices, regions):
    region = regions[indices[0]]
    for i in range(1,len(indices)):
        region = merge_regions(region, regions[indices[i]])
    return region

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
    if max(int_areas) == 0:
        return - 1
    else:
        return int_areas.index(max(int_areas)) 


def merge_regions(region,other):
    x1 = min(region[0],other[0])
    y1 = min(region[1], other[1])
    x2 = max(region[2], other[2])
    y2 = max(region[3], other[3])
    
    return (x1,y1,x2,y2) 

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