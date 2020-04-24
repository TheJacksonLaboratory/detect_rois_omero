def retrieve_image(session, base_url, img_id, scale):
    from PIL import Image
    from io import BytesIO
    import numpy as np
    r = session.get(base_url)
    host = base_url.split("/api")[0]
    # which lists a bunch of urls as starting points
    urls = r.json()
    images_url = urls['url:images']
    single_image_url = images_url+str(img_id)+"/"
    thisjson = session.get(single_image_url).json()
    width = int(thisjson['data']['Pixels']['SizeX'])
    print(width)
    scaled = round(width/scale)
    img_address = host+"/webgateway/render_birds_eye_view/"+str(img_id)+"/"+str(scaled)
    jpeg = session.get(img_address, stream=True)
    i = Image.open(BytesIO(jpeg.content))
    jpeg.close()
    return np.array(i)
    