from math import floor, ceil
import os

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfReader, PdfWriter, _page


FILE_EXTENSIONS = {".docx"}
FINAL_PDF_PATH = "document.pdf"
FONT_START_SIZE = 200
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
PADDING = 20
PDF_DIMENSIONS = (2480, 3508)
PDF_EXTENSIONS = {".pdf"}
WATERMARK_COLOR = (128, 128, 128, 100)
WATERMARK_PATH = "watermark.pdf"


class UnprocessibleFileException(Exception):
    pass


class BaseFile:

    def __init__(self) -> None:
        pass

    def get_extension(self, path):
        return os.path.splitext(path)[-1]
    
    def get_filename(self, path):
        _, filename = os.path.split(path)
        return filename
    
    def get_filename_no_ext(self, path):
        _, filename = os.path.split(path)
        filename_no_ext = os.path.splitext(filename)[0]
        return filename_no_ext
    
    def add_prefix_to_filename(self, path, prefix):
        folder, filename = os.path.split(path)
        filename = f"{prefix}_{filename}"
        return os.path.join(folder, filename)
    
    def change_extension(self, path, new_ext):
        folder, filename = os.path.split(path)
        filename_no_ext = os.path.splitext(filename)[0]
        filename = f"{filename_no_ext}.{new_ext}"
        return os.path.join(folder, filename)


class Document(BaseFile):
    def __init__(self, files: list, password: str, watermark: str):
        """
        Class to represent document with watermark and password
        :param files list: list of file paths
        :param password str: password word
        :param watermark str: watermark word
        """

        self.files = files
        self.password = password
        self.watermark = watermark
        # List of pdf docs paths to merge at the end
        self.pages = list()
        self.allowed_formats = (".pdf", ".docx", ".png", ".jpg", ".jpeg")
    
    def process(self):
        for f in self.files:
            if self.get_extension(f) in IMAGE_EXTENSIONS:
                filename = self.apply_image_watermark(f)
                pdf = self.convert_image_to_pdf(filename)
            if self.get_extension(f) in FILE_EXTENSIONS:
                pdf = self.convert_file_to_pdf(f)
                pdf = self.apply_pdf_watermark(pdf)
            if self.get_extension(f) in PDF_EXTENSIONS:
                self.apply_pdf_watermark(f)
                pdf = f
            self.pages.append(pdf)
        filename = self.save()
    
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
        Conver image files to PDF, saves locally
        """
        image = Image.open(path)
        pdf = image.convert("RGB")
        filename = self.get_filename_no_ext(path)
        pdf.save(f"{filename}.pdf")
        return f"{filename}.pdf"
    
    # def convert_file_to_pdf(self, path):
    #     filename = self.get_filename(path)
    #     convert(path, f"{filename}.pdf")
        
    def apply_image_watermark(self, f):
        """
        Apply watermark to a file
        :param f str: file path
        """

        w = Watermark(self.watermark, f=f)
        filename = w.create_image_with_watermark()
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
            filename = w.create_pdf_with_watermark()
            new_page = self.merge_watermark_pdf(page, filename)
            writer.add_page(new_page)
        with open(f, "wb") as fb:
            writer.write(fb)
        return f
    
    def merge_watermark_pdf(self, page, watermark):
        if not page.extract_text():
            return self.merge_as_stamp(page, watermark)
        else:
            return self.merge_as_watermark(page, watermark)
    
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
    
    def merge_as_watermark(self, page: _page.PageObject, watermark: str):
        """
        For digital-generated PDF we can put watermark under the page content
        """

        print("Adding watermark underneath the page")
        watermark_reader = PdfReader(watermark)
        watermark = watermark_reader.pages[0]
        
        mediabox = page.mediabox

        watermark.merge_page(page)
        watermark.mediabox = mediabox
        return watermark

    def encrypt(self):
        """
        Add password
        """
        reader = PdfReader(FINAL_PDF_PATH)
        writer = PdfWriter()

        # Add all pages to the writer
        for page in reader.pages:
            writer.add_page(page)

        # Add a password to the new PDF
        writer.encrypt(self.password)

        # Save the new PDF to a file
        with open(FINAL_PDF_PATH, "wb") as f:
            writer.write(f)


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
            self.create_image_with_watermark()
        else:
            self.create_pdf_with_watermark()
    
    def create_image_with_watermark(self):
        """
        Helper method to add watermark to an image
        """

        image = Image.open(self.path).convert("RGBA")
        font = self.get_right_font(min(image.size))
        txt = Image.new("RGBA", image.size, (255, 255, 255, 0))

        draw = ImageDraw.Draw(txt)

        word_length = font.getLength(self.watermark)
        center_image_width = self.get_center_width(txt.size[0], word_length)
        center_image_length = self.get_center_length(txt.size[1], font)

        # Draw on top in the center
        draw.text((center_image_width, 0 + PADDING), self.watermark,  font=font, fill=WATERMARK_COLOR)

        # Draw in the center
        draw.text((center_image_width, center_image_length), self.watermark,  font=font, fill=WATERMARK_COLOR)

        # Draw at the bottom
        draw.text((center_image_width, txt.size[1] - PADDING - self.get_text_height(font)), self.watermark,  font=font, fill=WATERMARK_COLOR)      
        
        # Merge images
        out = Image.alpha_composite(image, txt)

        # Save file
        if self.get_extension(self.path) != ".png":
            self.path = self.change_extension(self.path, "png")
        new_filename = self.add_prefix_to_filename(self.path, "watermark")
        out.save(new_filename)
        return new_filename
    
    def create_pdf_with_watermark(self):
        """
        Helper method to create a new PDF document 
        and add text to it
        """
        
        pdf = FPDF('P', 'pt', (self.dimensions))
        pdf.add_font("Roboto", "", "Roboto-Bold.ttf", uni=True)

        self.set_right_font_fpdf(self.dimensions[0], pdf)
        pdf.set_text_color(128, 128, 128)
        pdf.add_page()

        word_length = pdf.get_string_width(self.watermark)

        center_image_width = self.get_center_width(self.dimensions[0], word_length)
        center_image_height = self.dimensions[1] / 2 - ceil(pdf.font_size) / 2
        padding_from_bottom = self.dimensions[1] - PADDING * 2 - ceil(pdf.font_size) - pdf.b_margin

        pdf.cell(word_length + PADDING * 2, pdf.font_size + PADDING * 2, self.watermark, 0, 1, 'C')

        pdf.set_x(center_image_width)
        pdf.set_y(center_image_height)
        pdf.cell(word_length + PADDING * 2, pdf.font_size, self.watermark, 0, 1, 'C')

        pdf.set_y(padding_from_bottom)
        print("Height: " + str(self.dimensions[1]))
        print("printing at the bottom at " + str(padding_from_bottom))
        pdf.cell(word_length + PADDING * 2, pdf.font_size + PADDING * 2, self.watermark, 0, 1, 'C')

        pdf.output('watermark.pdf', 'F')
        return WATERMARK_PATH
    
    def get_right_font_pil(self, max_length):
        font_size = FONT_START_SIZE
        font = ImageFont.truetype("Roboto-Bold.ttf", size=font_size)
        length = font.getlength(self.watermark)
        while length > max_length - PADDING:
            font_size -= PADDING
            font = ImageFont.truetype("Roboto-Bold.ttf", size=font_size)
            length = font.getlength(self.watermark)
        return font
    
    def set_right_font_fpdf(self, max_length, pdf):
        font_size = FONT_START_SIZE
        pdf.set_font("Roboto", "", font_size)
        length = pdf.get_string_width(self.watermark)
        while length > max_length - PADDING * 2:
            font_size -= PADDING
            pdf.set_font("Roboto", "", font_size)
            length = pdf.get_string_width(self.watermark)
    
    def get_center_width(self, width, text_length):
        center_image_width = width / 2 - text_length / 2
        return floor(center_image_width)
    
    def get_center_length(self, length, font):
        text_height = self.get_text_height(font)
        center_image_length = length / 2 - text_height / 2
        return ceil(center_image_length)
    
    def get_text_height(self, font):
        text_box = font.getbbox(self.watermark)
        text_height = text_box[3] - text_box[1]
        return ceil(text_height)
