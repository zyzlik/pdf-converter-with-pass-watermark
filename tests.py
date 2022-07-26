import os

import pytest
from werkzeug.datastructures import FileStorage

from app import app
from lib.pdf import BaseFile, Document, Watermark, UnprocessibleFileException, FINAL_PDF_PATH

def test_ping():
    # Create a test client using the Flask application configured for testing
    response = app.test_client().get('/ping')
    assert response.status_code == 200
    assert response.data.decode('utf-8') == 'pong'


class TestBaseFile:

    def setup_method(self):
        self.b = BaseFile()

    def test_get_extension(self):
        ext = self.b.get_extension("tests/test_file.docx")
        assert ext == ".docx"
    
    def test_get_filename(self):
        filename = self.b.get_filename("tests/test_file.docx")
        assert filename == "test_file.docx"
    
    def test_add_prefix_to_filename(self):
        filename = self.b.add_prefix_to_filename("tests/test_file.docx", "prefix")
        assert filename == "tests/prefix_test_file.docx"
    
    def test_change_extension(self):
        filename = self.b.change_extension("tests/test_file.docx", "png")
        assert filename == "tests/test_file.png"

class TestFileUpload:
    def test_post_one_file(self):
        pdf_file = os.path.join("tests/test_pdf.pdf")
        my_file = FileStorage(
            stream=open(pdf_file, "rb"),
            filename="test_pdf.pdf",
            content_type="application/pdf",
        )
        response = app.test_client().post(
            "/",
            data={"document": my_file},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert response.data.decode('utf-8') == '{"link":"https://example.com"}\n'

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
    
    def test_apply_image_watermark(self):
        self.d.watermark = "kseniia churiumova"
        filename = self.d.apply_image_watermark("tests/test_image.jpeg")
        assert filename == "tests/watermark_test_image.png"
        assert os.path.exists("tests/watermark_test_image.png")
        os.remove("tests/watermark_test_image.png")
    
    # def test_convert_file(self):
    #     self.d.convert_file_to_pdf("tests/test_file.docx")
    #     assert os.path.exists("test_file.pdf")
