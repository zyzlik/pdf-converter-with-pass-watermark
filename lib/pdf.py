import os

from PIL import Image, ImageDraw, ImageFont


IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
FILE_EXTENSIONS = {"docx"}
PDF_EXTENSIONS = {"pdf"}


class UnprocessibleFileException(Exception):
    pass


class Document:
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
        self.allowed_formats = ("pdf", "docx", "png", "jpg", "jpeg")
    
    def process(self):
        for f in self.files:
            if self.get_extension(f) in IMAGE_EXTENSIONS:
                pdf = self.convert_image_to_pdf(f)
            if self.get_extension(f) in FILE_EXTENSIONS:
                pdf = self.convert_file_to_pdf(f)
            if self.get_extension(f) in PDF_EXTENSIONS:
                pdf = f
            pdf = self.apply_watermark(pdf)
            self.pages.append(pdf)
        self.save()
    
    def validate_all(self):
        for f in self.files:
            self.validate(f)
    
    def validate(self, f):
        extension = self.get_extension(f)
        if extension in self.allowed_formats:
            return
        raise UnprocessibleFileException(f"{extension} is not a valid format")
    
    def convert_image_to_pdf(self, path):
        """
        Conver image files to PDF, saves locally
        """
        image = Image.open(path)
        pdf = image.convert("RGB")
        filename = self.get_filename(path)
        pdf.save(f"{filename}.pdf")
    
    # def convert_file_to_pdf(self, path):
    #     filename = self.get_filename(path)
    #     convert(path, f"{filename}.pdf")
        
    def apply_watermark(self):
        """
        Merge watermark PDF with files
        """
        pass

    def encrypt(self):
        """
        Add password
        """
        pass
    
    def save(self):
        """
        Saves all the pages into single PDF file
        """
        first_page = self.pages.pop(0)
        first_page.save("document.pdf", save_all=True, append_images=self.pages)
    
    def get_extension(self, path):
        return path.split(".")[-1].lower()
    
    def get_filename(self, path):
        filename = os.path.basename(path)
        return filename.split(".")[0]


class Watermark:
    def __init__(self, watermark: str):
        """
        Class to create a pdf file with watermark word across the page
        :param watermark str: watermark word
        """
        self.watermark = watermark
        self.create_pdf_with_watermark() 
    
    def create_pdf_with_watermark(self):
        """
        Helper method to create a new image 
        and ass text across it then
        convert to PDF
        """

        image = Image.new('RGBA', (3508, 2480), (255, 255, 255, 255))
        wm = self.create_image()
        image.paste(wm, (200, 200))
        pdf = image.convert("RGB")
        pdf.save("watermark.pdf")

    def create_image(self):
        font = ImageFont.truetype("Roboto-Bold.ttf", size=300)
        image_with_text = Image.new('L', (2500, 1500), 255)
        draw = ImageDraw.Draw(image_with_text)
        draw.text((0, 0), self.watermark,  font=font, fill=0)
        out = image_with_text.rotate(-45,  expand=1, fillcolor=255)
        return out