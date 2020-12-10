from omero.rtypes import rdouble, rint, rstring

def save_rois(image, regions, scale, replace):
    '''
    Main entry point - given a (BlitzGateway-based) omero image, regions and a scaling factor (that should be the same used for ROI creation),
    saves the regions as ROIs in OMERO

    Parameters:
                    image (OMERO image): return of a BlitzGateway.getObject() call, where ROIs will be saved to
                    regions (list): list of tuples of the form (y1,x1,y2,x2) representing the ROIs to be saved
                    scale (int? I guess it could be float...): scaling factor that will be applied to the regions (should be the same as the
                    one used when creating the ROIs)
                    replace(bool): whether to delete ALL existing ROIs from the image before saving the newly created ones or not. Use when rerunning 
                    the code on the same image.
    
                                    
    '''


    if replace:
        remove_all_rois(image)
    if regions and image:
        conn = image._conn
        counter = 1
        for region in regions:
            bbox = region
            
            shape = create_rectangle(bbox, counter, scale)
            if shape is not None:
                roi = create_roi(conn, image, [shape])
            counter = counter + 1
            
    else:
        return None


def remove_all_rois(image):
    conn = image._conn
    roi_service = conn.getRoiService()
    result = roi_service.findByImage(image.getId(), None)
    for roi in result.rois:
        conn.deleteObjects("Roi", [roi.getId().getValue()])
    return


def create_rectangle(data, order, scale):
    '''
    Generate shape from bounding box data and scaling factor.
                                    
    '''
    from omero.model import RectangleI
    # assuming 2d image
    z_index = 0
    t_index = 0

    # scale up to full-size image
    y1 = data[0] * scale
    x1 = data[1] * scale
    h = (data[2] - data[0]) * scale
    w = (data[3] - data[1]) * scale
    shape = RectangleI()
    
    shape.x = rdouble(x1)
    shape.y = rdouble(y1)
    shape.width = rdouble(w)
    shape.height = rdouble(h)
    
    shape.textValue = rstring("ROI "+str(order))
     

    if shape is not None:
        shape.theZ = rint(z_index)
        shape.theT = rint(t_index)
    return shape

def create_roi(conn, img, shapes):

    '''
    Generic function to save ROI(s) to OMERO using updateService    
                                    
    '''
    from omero.model import RoiI
    updateService = conn.getUpdateService()
    roi = RoiI()
    
    roi.setImage(img._obj)
    # I could be calling this function just once by creating a list of shapes beforehand, but whatever
    for shape in shapes:
        roi.addShape(shape)
    # setting group is always necessary here - using same group as the image's 
    group_id = img.getDetails().getGroup().getId()
    ctx = {'omero.group': str(group_id)}
    return updateService.saveAndReturnObject(roi, ctx)


