import os

from werkzeug.datastructures import FileStorage

from app import app

def test_ping():
    # Create a test client using the Flask application configured for testing
    response = app.test_client().get('/ping')
    assert response.status_code == 200
    assert response.data.decode('utf-8') == 'pong'

class TestFileUpload:
    def test_post_one_file(self):
        pdf_file = os.path.join("tests/test.pdf")
        my_file = FileStorage(
            stream=open(pdf_file, "rb"),
            filename="test.pdf",
            content_type="application/pdf",
        )
        response = app.test_client().post(
            "/",
            data={"document": my_file},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert response.data.decode('utf-8') == "Got your file!"
