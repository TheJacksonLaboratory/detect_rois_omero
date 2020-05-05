def create_rois(image, size_thresh, method_thresh, closing):
    '''
    Main entry-point function for generating ROIs automatically. 
    Does thresholding, clever merging of intersecting ROIs and ordering left-right-top-bottom.

            Parameters:
                    image (np.array): 3-dimensional (2d + RGB) numpy array with pixel data for retrieved jpeg from OMERO
                    size_thresh (num): Minimum size (in pixels) for an ROI to be considered an ROI
                    method_thresh (str): Thresholding method. Current options are 'otsu', 'triangle', 'yen' and 'li'.
                    closing (int): radius for the diamond-shaped structuring element used for closing operation.

            Returns:
                    regions (list): list of pruned, ordered tuples of the form (y1,x1,y2,x2) representing the ROIs to be saved back to OMERO.
    '''
    from skimage.color import rgb2gray
    from skimage.filters import threshold_otsu, threshold_triangle, threshold_yen, threshold_li
    from skimage.util import invert
    from skimage.morphology import diamond, binary_closing
    from skimage.measure import regionprops, label
    import numpy as np


    # we're assuming the image is RGB and dark features on light background
    im = rgb2gray(image)
    im = invert(im)
    
    # ugly thresholding choice here - I'm assuming the inputs to be well-behaved
    if method_thresh == 'otsu':
        im_thresh = im > threshold_otsu(im)
    elif method_thresh == 'triangle':
        im_thresh = im > threshold_triangle(im)
    elif method_thresh == 'yen':
        im_thresh = im > threshold_yen(im)
    elif method_thresh == 'li':
        im_thresh = im > threshold_li(im)

    # do a bit of closing to already merge regions that are almost touching
    # how much? up to you, it's an input parameter
    im_thresh = binary_closing(im_thresh, diamond(closing))
    im_lab = label(im_thresh)

    # get rid of ROIs smaller than required size threshold
    for i in range(1, im_lab.max()+1):
        coords = np.where(im_lab == i)
        if len(coords[0]) < size_thresh:
            im_lab[coords] = 0
      
    regionproperties = regionprops(im_lab)
    regions = []

    # at least for now we only care about the bounding boxes for ROIs
    for r in regionproperties:
        regions.append(r.bbox)
    regions = prune_regions(regions)
    regions = order_regions(regions)
    #return []
    return regions

def distance(p1, p2):
    '''
    Basic L2 distance. I will not bother writing a detailed docstring for this.
    '''

    import numpy as np
    d = np.sqrt(((p2[0] - p1[0]) ** 2) + ((p2[1] - p1[1]) ** 2))
    return d

def weighted_distance(p1, p2, weight):
    '''
    Weighted L2 distance where Y difference is multiplied by a weight. 
    We want discrepancies in Y to be magnified to be able to detect lines.
    '''
    import numpy as np
    d = np.sqrt(((p2[0] - p1[0]) ** 2) + ((weight * (p2[1] - p1[1])) ** 2))
    return d

def generate_centroids(regions):
    '''
    Generate centroids of the region bounding boxes. 

    Parameters:
                    regions (list): tuples of the form (y1,x1,y2,x2) representing the ROI bounding boxes
                    
            Returns:
                    centroids (list): list of tuples of the form (X, Y) with centroids (because I hate the original tuple coordinate ordering)
                                    
    '''
   
    centroids = []
    if regions != []:
        for region in regions:
            centroids.append(((region[1]+ region[3])/2, (region[0]+ region[2])/2))
    return centroids

def order_regions(regions):
    '''
    This function is an absolute nightmare that will require a lot of in-line commenting to make any sense of. But basically it gets
    a list of region bounding boxes and returns the same list, but ordered left-right and top-bottom (i.e. writing order). 

    Parameters:
                    regions (list): tuples of the form (y1,x1,y2,x2) representing the ROI bounding boxes
                    
            Returns:
                    a mess (list): also tuples of the form (y1,x1,y2,x2) representing the ROI bounding boxes, but ordered
                                    
    '''


    import numpy as np
    if regions != []:
        
        #while regions != []:
        centroids = generate_centroids(regions)

        # detecting top-left ROI: lowest sum of coordinates
        sums = [c[0]+c[1] for c in centroids]
        topleft = sums.index(min(sums))
        # I won't need to order that one (it's the first), so I get rid of it
        c_topleft = centroids[topleft]
        r_topleft = regions[topleft]
        regions.remove(r_topleft)
        centroids.remove(c_topleft)

        # calculate weighted distances to the top left ROI, where Y distances are weighted at
        # 20 (!!!) times the X distances - this sucks and I still can't figure out a better way to 
        # make sure I'm getting lines correctly!
        dists = [weighted_distance(x,c_topleft,20) for x in centroids]
        
        # basically I sort everything based on the weighted distances
        # If I did things right, the first elements are on the top line, then there's a big
        # jump in weighted distances, then second line, big jump, third line, and so on
        centroids = [x for _,x in sorted(zip(dists,centroids))]
        regions = [x for _,x in sorted(zip(dists,regions))]
        dists = [x for x in sorted(dists)]

        # detecting "big jumps" as anything bigger than 1.5 times the st dev of differences
        differences = [dists[i+1]-dists[i] for i in range(len(dists)-1)]
        line_dividers = differences > 1.5*np.std(differences)
        line_dividers = np.insert(line_dividers,0,False)


        # create list of lists where each element is a list containing a line of ROIs
        lines = []
        lines.append([r_topleft])
        for i in range(len(regions)):
            if line_dividers[i]:
                lines.append([])
            lines[-1].append(regions[i])
            
        results = []

        # sort each line left-to-right by comparing x values
        for line in lines:
            line_centr = generate_centroids(line)
            xvals = [x[0] for x in line_centr]  
            results.append([x for _,x in sorted(zip(xvals,line))])  

        # return statement is just unraveling the list of lists as a single list
        return [item for sublist in results for item in sublist]
    else:
        return []

def prune_regions(regions):
    '''
    Get rid of any regions with aspect ratios bigger than 4. Why 4? Good question.
    '''
    restart = True
    while restart:
        restart = False
        for region in regions:   
            if check_aspect_ratio(region, 4):
                regions.remove(region)
                restart = True
                break
            
    regions = cluster_regions(regions)
    
  
    return(regions)


def cluster_regions(regions):

    '''
    This function does some clever graph stuff to merge ROIs hierarchically based on intersection areas. By defining merge 
    priorities a priori instead of iteratively, we get really good quality ROIs that can even overlap without becoming a single
    huge bounding box.

    Parameters:
                    regions (list): tuples of the form (y1,x1,y2,x2) representing the ROI bounding boxes
                    
            Returns:
                    results (list): also tuples of the form (y1,x1,y2,x2) (but fewer of them) representing the ROI bounding boxes, but merged
                                    
    '''
    import networkx as nx
    willmerge = []
    mergee = []
    results = []

    # we do a pass through all regions and generate two new lists: a boolean saying whether that region needs merging
    # (i.e. it intersects with another one) and an integer one with the index of the region that should be merged with
    # that one
    for region in regions:
        intersection = check_intersections(region,regions)
        if intersection != -1:
            willmerge.append(True)
            mergee.append(intersection)
            
    # if a region doesn't have intersections, go ahead and add it to the results list        
        else:
            willmerge.append(False)
            mergee.append(intersection)
            results.append(region)
    
    # create a graph and add an edge for each combination of regions that need to be merged.
    G = nx.Graph()
    edges = []
    count = 0
    for roi in range(len(mergee)):
        if willmerge[count] == True:
            edges.append((count,mergee[count]))
        count = count + 1
    G.add_edges_from(edges)


    # the resulting graph will have one connected component per final ROI, and the final ROI is the bounding box
    # around all ROIs in this connected component
    for a in nx.connected_components(G):
        roi = merge_cluster(list(a), regions)
        results.append(roi)
    
    return results


def merge_cluster(indices, regions):
    '''
    Generate a bounding box around all ROIs with given indices on the list of regions (also given)
    '''
    region = regions[indices[0]]
    for i in range(1,len(indices)):
        region = merge_regions(region, regions[indices[i]])
    return region

def check_aspect_ratio(region, threshold):
    '''
    Simple binary check to see whether a bounding box exceeds a threshold aspect ratio. True means ROI is very elongated.
    '''
    bbox = region
    ratio = (bbox[2]-bbox[0])/(bbox[3]-bbox[1])
    if ratio > threshold or ratio < (1/threshold):
        return True

def check_intersections(region, regions):
    '''
    Calculates intersection areas between a region and all other regions and returns the index of the maximum intersection area.

    Parameters:
                    regions (list): tuples of the form (y1,x1,y2,x2) representing the ROI bounding boxes
                    region (tuple): tuple of the form (y1,x1,y2,x2) representing the ROI to be checked against all others
                    
            Returns:
                    index (int): index of the maximum intersection area ROI on the regions list
                                    
    '''
    int_areas = []
    bbox = region
    for r in regions:
        r_bbox = r
        
        # the current region being checked is always on the regions list, so we ignore it
        if (r_bbox == bbox):
            int_areas.append(0)

            continue
        if bbox[0] >= r_bbox[2] or r_bbox[0] >= bbox[2]:
            int_areas.append(0) 
            continue
        if bbox[1] >= r_bbox[3] or r_bbox[1] >= bbox[3]:
            int_areas.append(0) 
            continue

        # magical code that gives us coordinates for the intersection bounding box
        y1 = max(min(bbox[0],r_bbox[2]), min(r_bbox[0],bbox[2]))
        x1 = max(min(bbox[1],r_bbox[3]), min(r_bbox[1],bbox[3]))
        y2 = min(max(bbox[0],r_bbox[2]), max(r_bbox[0],bbox[2]))
        x2 = min(max(bbox[1],r_bbox[3]), max(r_bbox[1],bbox[3]))

        # we add the area of intersection to the int_areas list
        if (x2 > x1) and (y2 > y1):
            int_areas.append((x2-x1)*(y2-y1))
        else:
            int_areas.append(0)

    # return -1 if there is no intersection (returning 0 is a bad idea because 0 is a valid index)
    if max(int_areas) == 0:
        return -1
    else:
    # otherwise, return index of maximum intersection area
        return int_areas.index(max(int_areas)) 


def merge_regions(region,other):
    '''
    Simple magic code that generates a bounding box that is the union of two bounding boxes.
    '''
    y1 = min(region[0],other[0])
    x1 = min(region[1], other[1])
    y2 = max(region[2], other[2])
    x2 = max(region[3], other[3])
    
    return (y1,x1,y2,x2) 



# just some sample code if you want to run the whole workflow standalone

if __name__ == "__main__":
    import os
    from create_session import create_json_session, create_blitz_session
    from retrieve_image import retrieve_image, get_image
    from save_rois import save_rois
    
   

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