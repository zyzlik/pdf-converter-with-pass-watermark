from datetime import datetime
from math import floor, ceil
import os
import subprocess
from sys import platform

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont, ImageOps
from PyPDF2 import PdfMerger, PdfReader, PdfWriter, _page


A4_SIZE = (595, 842,)
FILE_EXTENSIONS = {".docx", ".doc"}
FINAL_PDF_NAME = "document"
FONT_START_SIZE = 200
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
PADDING = 20
PDF_EXTENSIONS = {".pdf"}
WATERMARK_COLOR = (128, 128, 128, 100)
WATERMARK_PATH = "watermark.pdf"


class UnprocessibleFileException(Exception):
    pass


class BaseFile:

    def __init__(self) -> None:
        pass

    def get_extension(self, path: str):
        """
        Returns file's extension
        """
        return os.path.splitext(path)[-1]
    
    def get_filename(self, path: str):
        """
        Returns name of the file without folder name
        """
        _, filename = os.path.split(path)
        return filename
    
    def get_filename_no_ext(self, path: str):
        """
        Returns name of the file without folder and extension
        """
        _, filename = os.path.split(path)
        filename_no_ext = os.path.splitext(filename)[0]
        return filename_no_ext
    
    def add_prefix_to_filename(self, path: str, prefix: str):
        """
        Adds prefix to the file name
        """
        folder, filename = os.path.split(path)
        filename = f"{prefix}_{filename}"
        return os.path.join(folder, filename)
    
    def change_extension(self, path: str, new_ext: str):
        """
        Changes extension of the file name
        """
        folder, filename = os.path.split(path)
        filename_no_ext = os.path.splitext(filename)[0]
        filename = f"{filename_no_ext}.{new_ext}"
        return os.path.join(folder, filename)
    
    def delete_file(self, path: str):
        """
        Deletes file
        """
        os.remove(path)
    
    def generate_filename(self):
        ts = datetime.now().timestamp()
        return f"{FINAL_PDF_NAME}.{ts}.pdf"


class Document(BaseFile):
    def __init__(self, files: list, password: str, watermark: str):
        """
        Class to represent document with watermark and password
        :param files list: list of file paths
        :param password str: password word
        :param watermark str: watermark word
        """

        print("Initiating document...")
        self.files = files
        self.password = password
        self.watermark = watermark
        # List of pdf docs paths to merge at the end
        self.pages = list()
        self.allowed_formats = (".pdf", ".docx", ".png", ".jpg", ".jpeg")
        self.filename = self.generate_filename()
    
    def process(self):
        """
        Main function:
        Goes through files, calls the methods to add watermarks,
        Converts to PDF and encrypts
        """
        for f in self.files:
            print("Processing {}".format(f))
            if self.get_extension(f) in IMAGE_EXTENSIONS:
                filename = self.apply_image_watermark(f)
                pdf = self.convert_image_to_pdf(filename)
                self.delete_file(filename)
            if self.get_extension(f) in FILE_EXTENSIONS:
                pdf = self.convert_file_to_pdf(f)
                pdf = self.apply_pdf_watermark(pdf)
            if self.get_extension(f) in PDF_EXTENSIONS:
                pdf = self.apply_pdf_watermark(f)
            self.pages.append(pdf)
        self.merge_pages(self.filename)
        self.encrypt(self.filename)
        self.cleanup()
        return self.filename
    
    def merge_pages(self, path):
        merger = PdfMerger()
        for pdf in self.pages:
            merger.append(pdf)
        merger.write(path)
        merger.close()
    
    def validate_all(self):
        for f in self.files:
            self.validate(f)
    
    def validate(self, f):
        extension = self.get_extension(f).lower()
        if extension in self.allowed_formats:
            return
        raise UnprocessibleFileException(f"{extension} is not a valid format")
    
    def convert_image_to_pdf(self, path):
        """
        Convert image files to PDF, saves locally
        :param path: path to a file
        """
        print("Converting {} to pdf".format(path))
        pdf = FPDF("P", 'mm', 'A4')
        pdf.add_page()
        pdf.image(path, 0, 0, pdf.w, pdf.h)

        filename = self.get_filename_no_ext(path)
        pdf.output(f"{filename}.pdf")
        return f"{filename}.pdf"
    
    def convert_file_to_pdf(self, path):
        """
        convert a doc or docx document to PDF
        :param path: path to a file
        """
        if platform == "linux":
            cmd = 'libreoffice --convert-to pdf'.split() + [path]
        elif platform == "darwin":
            cmd = '/Applications/LibreOffice.app/Contents/MacOS/soffice --convert-to pdf'.split() + [path]
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        p.wait(timeout=10)
        _, stderr = p.communicate()
        if stderr:
            raise subprocess.SubprocessError(stderr)
        
    def apply_image_watermark(self, f):
        """
        Apply watermark to a file
        :param f str: file path
        """
        w = Watermark(self.watermark, f=f)
        filename = w.add_watermark()
        return filename
    
    def apply_pdf_watermark(self, f):
        """
        Apply watermark to a file
        :param f str: file path
        """
        reader = PdfReader(f)
        writer = PdfWriter()
        for page in reader.pages:
            width = ceil(page.mediabox.width)
            height = ceil(page.mediabox.height)
            w = Watermark(self.watermark, dimensions=(width, height))
            filename = w.add_watermark()
            new_page = self.merge_as_stamp(page, filename)
            writer.add_page(new_page)
            self.delete_file(filename)
        new_filename = self.add_prefix_to_filename(f, "watermark")
        with open(new_filename, "wb") as fb:
            writer.write(fb)
        # self.delete_file(f)
        return new_filename
    
    def merge_as_stamp(self, page: _page.PageObject, watermark: str):
        """
        For not digital generated PDF such as images or scans
        We can't put watermark under it, so we put on top
        """

        print("Stamping watermark over the page")
        watermark_reader = PdfReader(watermark)
        watermark = watermark_reader.pages[0]

        mediabox = page.mediabox
        
        page.merge_page(watermark)
        page.mediabox = mediabox
        return page

    def encrypt(self, path):
        """
        Add password
        """
        reader = PdfReader(path)
        writer = PdfWriter()

        # Add all pages to the writer
        for page in reader.pages:
            writer.add_page(page)

        # Add a password to the new PDF
        writer.encrypt(self.password)

        # Save the new PDF to a file
        with open(path, "wb") as f:
            writer.write(f)
    
    def cleanup(self):
        for f in self.pages:
            self.delete_file(f)


class Watermark(BaseFile):
    def __init__(self, watermark: str, f: str = "", dimensions: tuple = None):
        """
        Class to create a pdf file with watermark word across the page
        :param watermark str: watermark word
        """

        self.watermark = watermark
        self.path = f
        self.dimensions = dimensions
    
    def add_watermark(self):
        if self.get_extension(self.path) in IMAGE_EXTENSIONS:
            return self._create_image_with_watermark()
        else:
            return self._create_pdf_with_watermark()
    
    def _create_image_with_watermark(self):
        """
        Helper method to add watermark to an image
        """

        image = Image.open(self.path).convert("RGBA")
        image = ImageOps.exif_transpose(image)
        font = self._get_right_font_pil(image.size[0])
        txt = Image.new("RGBA", image.size, (255, 255, 255, 0))

        draw = ImageDraw.Draw(txt)

        word_length = font.getlength(self.watermark)
        center_image_width = self._get_center_width(txt.size[0], word_length)
        center_image_length = self._get_center_length(txt.size[1], font)

        # Draw on top in the center
        draw.text((center_image_width, 0 + PADDING), self.watermark,  font=font, fill=WATERMARK_COLOR)

        # Draw in the center
        draw.text((center_image_width, center_image_length), self.watermark,  font=font, fill=WATERMARK_COLOR)

        # Draw at the bottom
        draw.text((center_image_width, txt.size[1] - PADDING - self._get_text_height(font)), self.watermark,  font=font, fill=WATERMARK_COLOR)      
        
        # Merge images
        out = Image.alpha_composite(image, txt)

        # Save file
        out = out.convert("RGB")
        filename = self.change_extension(self.path, "jpeg")
        new_filename = self.add_prefix_to_filename(filename, "watermark")
        out.save(new_filename)
        return new_filename
    
    def _create_pdf_with_watermark(self):
        """
        Helper method to create a new PDF document 
        and add text to it
        """
        
        pdf = FPDF('P', 'pt', (self.dimensions))
        pdf.add_font("Roboto", "", "Roboto-Bold.ttf", uni=True)

        self._set_right_font_fpdf(self.dimensions[0], pdf)
        pdf.set_text_color(128, 128, 128)
        pdf.add_page()

        word_length = pdf.get_string_width(self.watermark)

        center_image_width = self._get_center_width(self.dimensions[0], word_length)
        center_image_height = self.dimensions[1] / 2 - ceil(pdf.font_size) / 2
        padding_from_bottom = self.dimensions[1] - PADDING * 2 - ceil(pdf.font_size) - pdf.b_margin

        pdf.cell(word_length + PADDING * 2, pdf.font_size + PADDING * 2, self.watermark, 0, 1, 'C')

        pdf.set_x(center_image_width)
        pdf.set_y(center_image_height)
        pdf.cell(word_length + PADDING * 2, pdf.font_size, self.watermark, 0, 1, 'C')

        pdf.set_y(padding_from_bottom)
        pdf.cell(word_length + PADDING * 2, pdf.font_size + PADDING * 2, self.watermark, 0, 1, 'C')

        pdf.output(WATERMARK_PATH, 'F')
        return WATERMARK_PATH
    
    def _get_right_font_pil(self, max_length):
        font_size = FONT_START_SIZE
        font = ImageFont.truetype("Roboto-Bold.ttf", size=font_size)
        length = font.getlength(self.watermark)
        while length > max_length - PADDING:
            font_size -= PADDING
            font = ImageFont.truetype("Roboto-Bold.ttf", size=font_size)
            length = font.getlength(self.watermark)
        return font
    
    def _set_right_font_fpdf(self, max_length, pdf):
        font_size = FONT_START_SIZE
        pdf.set_font("Roboto", "", font_size)
        length = pdf.get_string_width(self.watermark)
        while length > max_length - PADDING * 2:
            font_size -= PADDING
            pdf.set_font("Roboto", "", font_size)
            length = pdf.get_string_width(self.watermark)
    
    def _get_center_width(self, width, text_length):
        center_image_width = width / 2 - text_length / 2
        return floor(center_image_width)
    
    def _get_center_length(self, length, font):
        text_height = self._get_text_height(font)
        center_image_length = length / 2 - text_height / 2
        return ceil(center_image_length)
    
    def _get_text_height(self, font):
        text_box = font.getbbox(self.watermark)
        text_height = text_box[3] - text_box[1]
        return ceil(text_height)
