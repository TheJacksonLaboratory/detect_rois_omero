from omero.rtypes import rdouble, rint, rstring

def save_rois(image, regions, scale):
    """
    Usage: In napari, open console...
    >>> from omero_napari import *
    >>> save_rois(viewer, omero_image)
    """
    if regions and image:
        conn = image._conn
        counter = 1
        for region in regions:
            bbox = region
            
            shape = create_rectangle(bbox, image, counter, scale)
            if shape is not None:
                roi = create_roi(conn, image, [shape])
            counter = counter + 1
            
    else:
        return None
    


def get_t(coordinate, image):
    if image.getSizeT() > 1:
        return coordinate[0]
    return 0

def get_z(coordinate, image):
    if image.getSizeZ() == 1:
        return 0
    if image.getSizeT() == 1:
        return coordinate[0]
    #if coordinate includes T and Z... [t, z, x, y]
    return coordinate[1]


def create_rectangle(data, image, order, scale):
    
    from omero.model import RectangleI
    z_index = get_z(0, image)
    t_index = get_t(0, image)
    y1 = data[0] * scale
    x1 = data[1] * scale
    h = (data[2] - data[0]) * scale
    w = (data[3] - data[1]) * scale
    shape = RectangleI()
    # TODO: handle 'updside down' rectangle x3 < x1
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
    from omero.model import RoiI
    updateService = conn.getUpdateService()
    roi = RoiI()
    #img = get_image(conn, img_id)
    roi.setImage(img._obj)
    for shape in shapes:
        roi.addShape(shape)
    group_id = img.getDetails().getGroup().getId()
    ctx = {'omero.group': str(group_id)}
    return updateService.saveAndReturnObject(roi, ctx)


def get_image(conn, image_id):
    
    if (image_id):
        image = conn.getObject("Image", image_id)
        return image
    else:
        return None