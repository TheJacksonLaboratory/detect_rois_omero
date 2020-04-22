from detect_rois_omero.src.create_session import create_session


def test_json_login():
    import os
    HOSTNAME = os.environ['OMERO_HOSTNAME']
    USERNAME = os.environ['OMERO_ADMIN_USER']
    PASSWORD = os.environ['OMERO_ADMIN_PASSWORD']

    login_rsp, session, base_url = create_session(HOSTNAME, USERNAME, PASSWORD)
    assert login_rsp['success']