# detect_rois_omero
Set of helper functions for automatically generating bounding boxes for OMERO slidescans


## Functions

### Session creation

- **create_json_session(web_host, username, password)**: creates a session/CSRF token for usage with the JSON OMERO API. 
- **create_blitz_session(host, username, password)**: creates and connects a BlitzGateway object with a session for usage with the Blitz OMERO API.

### Image retrieval

- **retrieve_image(session, base_url, image_id, scaling_factor)**: retrieves a jpeg for a 2D image from OMERO (given an image ID), scaled down by a scaling factor. *session* and *base_url* are outputs from **create_json_session**. Output is a 2D+RGB numpy array.
- **get_image(conn, image_id)**: retrieves an *Image* object from OMERO (given an image ID), using the Blitz API, from the BlitzGateway object specified by *conn*.

### ROI generation

- **create_rois(image, minimum_size, method, closing)**: creates ordered (left/right/top/bottom) ROIs that *should* approximate each slice in a slide scan. Uses thresholding based on a specified method (from 'triangle', 'otsu', 'yen', 'li'), filters by a minimum specified size in pixels, morphologically closes regions using a specified closing radius and then creates, merges appropriately and orders ROIs.

### ROI uploading

- **save_rois(image, regions, scaling_factor)**: saves ROIs back to OMERO - needs to use the Blitz API due to ROI saving not being supported via JSON API, and therefore needs an *Image* object retrieved from OMERO via Blitz API. Scaling factor needs to be specified here to scale ROIs back to full-size image server-side. 

## Example usage

```python
    from create_session import create_json_session, create_blitz_session
    from retrieve_image import retrieve_image
    from save_rois import save_rois, get_image
    from create_rois import create_rois

    login_rsp, session, base_url = create_json_session(WEB_HOSTNAME, USERNAME, PASSWORD)
    img = retrieve_image(session, base_url, img_id, scale_factor)
    regions = create_rois(img, min_size, method, closing)
    conn = create_blitz_session(HOSTNAME, USERNAME, PASSWORD)
    image = get_image(conn, img_id)
    save_rois(image, regions, scale_factor)
    conn.close()
```
