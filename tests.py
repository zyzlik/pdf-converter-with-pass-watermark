import os
import shutil

from PyPDF2 import errors, _page, PdfReader
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
        self.d.merge_pages()
        assert os.path.exists("document.pdf")
        reader = PdfReader("document.pdf")
        assert len(reader.pages) == 8
        os.remove("document.pdf")
    
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
        os.remove("watermark.pdf")
        os.remove("tests/watermark_test_pdf.pdf")
    
    def test_merge_watermark_pdf(self):
        reader = PdfReader("tests/test_pdf.pdf")
        page = reader.pages[0]
        out = self.d.merge_watermark_pdf(page, "tests/test.pdf")
        assert type(out) == _page
    
    def test_merge_as_stamp(self):
        reader = PdfReader("tests/test_pdf.pdf")
        page = reader.pages[0]
        out = self.d.merge_as_stamp(page, "tests/test.pdf")
        assert type(out) == _page
    
    def test_merge_as_watermark(self):
        reader = PdfReader("tests/test_pdf.pdf")
        page = reader.pages[0]
        out = self.d.merge_as_watermark(page, "tests/test.pdf")
        assert type(out) == _page
    
    def test_encrypt(self):
        shutil.copyfile("tests/test_pdf.pdf", "tests/test_encrypt.pdf")
        self.d.encrypt("tests/test_encrypt.pdf")
        reader = PdfReader("tests/test_encrypt.pdf")
        with pytest.raises(errors.PdfReadError):
            reader.documentInfo
        # With wrong password
        result = reader.decrypt("wrong")
        assert result.name == "NOT_DECRYPTED"
        result = reader.decrypt(self.d.password)
        assert result.name == "OWNER_PASSWORD"
        # Now we can read document info
        reader.documentInfo
        os.remove("tests/test_encrypt.pdf")
    
    # def test_convert_file(self):
    #     self.d.convert_file_to_pdf("tests/test_file.docx")
    #     assert os.path.exists("test_file.pdf")
