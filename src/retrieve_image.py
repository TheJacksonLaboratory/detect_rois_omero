def retrieve_image(session, base_url, img_id, scale):
    from PIL import Image
    from io import BytesIO
    import numpy as np
    # just some magical code to get the correct address from the json api session and image id
    r = session.get(base_url)
    host = base_url.split("/api")[0]
    # which lists a bunch of urls as starting points
    urls = r.json()
    images_url = urls['url:images']
    single_image_url = images_url+str(img_id)+"/"
    thisjson = session.get(single_image_url).json()

    # calculate width to be requested based on metadata and the specified scale factor
    width = int(thisjson['data']['Pixels']['SizeX'])
    scaled = round(width/scale)
    img_address = host+"/webgateway/render_birds_eye_view/"+str(img_id)+"/"+str(scaled)
    jpeg = session.get(img_address, stream=True)

    # using PIL and BytesIO to open the request content as an image
    i = Image.open(BytesIO(jpeg.content))
    jpeg.close()
    return np.array(i)
    