from math import floor, ceil
import os

from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfReader, PdfWriter


FILE_EXTENSIONS = {".docx"}
FINAL_PDF_PATH = "document.pdf"
FONT_START_SIZE = 300
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
                filename = self.apply_pdf_watermark(pdf)
            if self.get_extension(f) in PDF_EXTENSIONS:
                self.apply_pdf_watermark(f)
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

        w = Watermark(self.watermark, f)
        filename = w.create_image_with_watermark()
        return filename
    
    def apply_pdf_watermark(self, f):
        """
        Apply watermark to a file
        :param f str: file path
        """

        w = Watermark(self.watermark, f)
        filename = w.create_pdf_with_watermark()
        return filename

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
    def __init__(self, watermark: str, f: str):
        """
        Class to create a pdf file with watermark word across the page
        :param watermark str: watermark word
        """

        self.watermark = watermark
        self.path = f
    
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

        center_image_width = self.get_center_width(txt.size[0], font)
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
    
    def create_pdf_with_watermark(self, dimensions=None):
        """
        Helper method to create a new image 
        and add text across it then
        convert to PDF
        """

        if not dimensions:
            dimensions = PDF_DIMENSIONS
        
        image = Image.new('RGBA', dimensions, (255, 255, 255, 255))
        font = self.get_right_font(min(dimensions))
        draw = ImageDraw.Draw(image)

        conter_image_width = self.get_center_width(dimensions[0], font)
        center_image_length = self.get_center_length(dimensions[1], font)
        
        # Draw on top in the center
        draw.text((conter_image_width, 0 + PADDING), self.watermark,  font=font, fill=WATERMARK_COLOR)

        # Draw in the center
        draw.text((conter_image_width, center_image_length), self.watermark,  font=font, fill=WATERMARK_COLOR)

        # Draw at the bottom
        draw.text((conter_image_width, dimensions[1] - PADDING - self.get_text_height(font)), self.watermark,  font=font, fill=WATERMARK_COLOR)      

        self.image = image.convert("RGB")
        self.image.save(WATERMARK_PATH)
    
    def get_right_font(self, max_length):
        font_size = FONT_START_SIZE
        font = ImageFont.truetype("Roboto-Bold.ttf", size=font_size)
        length = font.getlength(self.watermark)
        while length > max_length - PADDING:
            font_size -= PADDING
            font = ImageFont.truetype("Roboto-Bold.ttf", size=font_size)
            length = font.getlength(self.watermark)
        return font
    
    def get_center_width(self, width, font):
        text_length = font.getlength(self.watermark)
        conter_image_width = width / 2 - text_length / 2
        return floor(conter_image_width)
    
    def get_center_length(self, length, font):
        text_height = self.get_text_height(font)
        center_image_length = length / 2 - text_height / 2
        return ceil(center_image_length)
    
    def get_text_height(self, font):
        text_box = font.getbbox(self.watermark)
        text_height = text_box[3] - text_box[1]
        return ceil(text_height)
