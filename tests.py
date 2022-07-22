import os

import pytest
from werkzeug.datastructures import FileStorage

from app import app
from lib.pdf import Document, Watermark, UnprocessibleFileException

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

class TestDocument:

    def setup_method(self):
        self.d = Document(["one.pdf", "two.png", "three.jpg"], "qwerty", "kseniia")

    def test_validate_allowed(self):
        self.d.validate_all()
    
    def test_validate_unallowed(self):
        with pytest.raises(UnprocessibleFileException):
            self.d.validate("one.doc")
    
    def test_validate_caps(self):
        self.d.validate("three.JPEG")
    
    def test_convert_image(self):
        self.d.convert_image_to_pdf("tests/test_image.jpeg")
        assert os.path.exists("test_image.pdf")
        os.remove("test_image.pdf")
    
    # def test_convert_file(self):
    #     self.d.convert_file_to_pdf("tests/test_file.docx")
    #     assert os.path.exists("test_file.pdf")
