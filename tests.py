import os
import shutil
from unittest import mock

from PIL import ImageFont
from PyPDF2 import errors, _page, PdfReader
import pytest
from werkzeug.datastructures import FileStorage

from app import app
from lib.pdf import BaseFile, Document, Watermark, UnprocessibleFileException
from lib.aws import save_file_to_s3

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
    
    def test_get_filename_no_ext(self):
        filename_no_ext = self.b.get_filename_no_ext("tests/document.pdf")
        assert filename_no_ext == "document"
    
    def test_get_filename(self):
        filename = self.b.get_filename("tests/test_file.docx")
        assert filename == "test_file.docx"
    
    def test_add_prefix_to_filename(self):
        filename = self.b.add_prefix_to_filename("tests/test_file.docx", "prefix")
        assert filename == "tests/prefix_test_file.docx"
    
    def test_change_extension(self):
        filename = self.b.change_extension("tests/test_file.docx", "png")
        assert filename == "tests/test_file.png"
    
    def test_generate_filename(self):
        filename = self.b.generate_filename()
        assert type(filename) == str
        assert "document" in filename

class TestFileUpload:
    def test_post_one_file(self):
        pdf_file = os.path.join("tests/test_pdf.pdf")
        my_file = FileStorage(
            stream=open(pdf_file, "rb"),
            filename="test_pdf.pdf",
            content_type="application/pdf",
        )
        app.config["ENV"] = "development"
        response = app.test_client().post(
            "/",
            data={"document": my_file, "watermark": "qwerty", "password": 123},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        assert "static" in response.data.decode('utf-8')
        os.remove("static/document.pdf")

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
    
    def test_process(self):
        d = Document(
            files=["tests/test_pdf.pdf", "tests/test_image.jpeg"],
            password="qwerty",
            watermark="kseniia"
        )
        d.process()
        assert os.path.exists("document.pdf")
        os.remove("document.pdf")
    
    def test_merge_pages(self):
        self.d.pages = ["tests/test_pdf.pdf", "tests/test_text_pdf.pdf"]
        self.d.merge_pages("kseniia.pdf")
        assert os.path.exists("kseniia.pdf")
        reader = PdfReader("kseniia.pdf")
        assert len(reader.pages) == 8
        os.remove("kseniia.pdf")
    
    def test_convert_image(self):
        self.d.convert_image_to_pdf("tests/test_image.jpeg")
        assert os.path.exists("test_image.pdf")
        os.remove("test_image.pdf")
    
    def test_apply_image_watermark(self):
        self.d.watermark = "kseniia churiumova"
        filename = self.d.apply_image_watermark("tests/test_image.jpeg")
        assert filename == "tests/watermark_test_image.jpeg"
        assert os.path.exists("tests/watermark_test_image.jpeg")
        os.remove("tests/watermark_test_image.jpeg")
    
    def test_apply_pdf_watermark(self):
        self.d.watermark = "kseniia churiumova"
        filename = self.d.apply_pdf_watermark("tests/test_pdf.pdf")
        assert filename == "tests/watermark_test_pdf.pdf"
        assert os.path.exists("tests/watermark_test_pdf.pdf")
        os.remove("tests/watermark_test_pdf.pdf")
    
    def test_merge_as_stamp(self):
        reader = PdfReader("tests/test_pdf.pdf")
        page = reader.pages[0]
        out = self.d.merge_as_stamp(page, "tests/test.pdf")
        assert type(out) == _page.PageObject
    
    def test_encrypt(self):
        shutil.copyfile("tests/test_pdf.pdf", "tests/test_encrypt.pdf")
        self.d.encrypt("tests/test_encrypt.pdf")
        reader = PdfReader("tests/test_encrypt.pdf")
        with pytest.raises(errors.PdfReadError):
            reader.metadata
        # With wrong password
        result = reader.decrypt("wrong")
        assert result.name == "NOT_DECRYPTED"
        result = reader.decrypt(self.d.password)
        assert result.name == "OWNER_PASSWORD"
        # Now we can read document info
        reader.metadata
        os.remove("tests/test_encrypt.pdf")
    
    def test_convert_file(self):
        self.d.convert_file_to_pdf("tests/test_file.docx")
        assert os.path.exists("test_file.pdf")
        os.remove("test_file.pdf")

class TestWatermark:

    def setup_method(self):
        self.w = Watermark("test")

    @mock.patch.object(Watermark, "_create_image_with_watermark")
    def test_add_watermark_image(self, mock):
        self.w.path = "tests/test_image.jpeg"
        self.w.add_watermark()
        mock.assert_called()
    
    @mock.patch.object(Watermark, "_create_pdf_with_watermark")
    def test_add_watermark_pdf(self, mock):
        self.w.path = "tests/test_pdf.pdf"
        self.w.add_watermark()
        mock.assert_called()
    
    def test_create_image_with_watermark(self):
        self.w.path = "tests/test_image.jpeg"
        filename = self.w._create_image_with_watermark()
        assert filename == "tests/watermark_test_image.jpeg"
        assert os.path.exists("tests/watermark_test_image.jpeg")
        os.remove("tests/watermark_test_image.jpeg")
    
    def test_create_pdf_with_watermark(self):
        self.w.dimensions = (595, 842,)
        filename = self.w._create_pdf_with_watermark()
        assert filename == "watermark.pdf"
        assert os.path.exists("watermark.pdf")
        os.remove("watermark.pdf")
    
    def test_get_right_font_pil(self):
        font = self.w._get_right_font_pil(500)
        assert type(font) == ImageFont.FreeTypeFont
    
    def test_get_center_width(self):
        res = self.w._get_center_width(200, 50)
        assert res == 75
    
    def test_get_center_length(self):
        font = ImageFont.truetype("Roboto-Bold.ttf", size=20)
        res = self.w._get_center_length(200, font)
        assert res == 93
    
    def test_get_text_height(self):
        font = ImageFont.truetype("Roboto-Bold.ttf", size=20)
        res = self.w._get_text_height(font)
        assert res == 14
