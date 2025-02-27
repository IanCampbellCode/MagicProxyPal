from PIL import Image
from pypdf import PdfWriter
import os


class PdfHandler:
    def __init__(self):
        self.horizontal = 50
        self.vertical = 22
        self.card_paste_number = 0

    def generate_pdf(self, cards):
        page_number = 1
        pdfs = []
        dpi = 195
        height = 2242
        width = 1657
        output_image = Image.new('RGB', (int(width), int(height)), "white")
        for card in cards:
            if card.image_uri is not None:
                card_img = Image.open("images/" + str(card).replace("/", "-") + ".jpg")
                count = 0
                while count < card.quantity:
                    self.card_paste_number += 1
                    self.get_next_position()
                    output_image.paste(card_img, (self.horizontal, self.vertical))
                    count += 1
                    if self.card_paste_number % 9 == 0:
                        file_name = "printable_cards_page_" + str(page_number) + ".pdf"
                        output_image.save(file_name, "PDF", dpi=(dpi, dpi))
                        pdfs.append(file_name)
                        page_number += 1
                        output_image = Image.new('RGB', (int(width), int(height)), "white")
        if self.card_paste_number % 9 != 0:
            file_name = "printable_cards_page_" + str(page_number) + ".pdf"
            output_image.save(file_name, "PDF", dpi=(dpi, dpi))
            pdfs.append(file_name)
        merger = PdfWriter()
        for pdf in pdfs:
            merger.append(pdf)
        merger.write("printable_deck.pdf")
        merger.close()
        for pdf in pdfs:
            os.remove(pdf)

    def get_next_position(self):
        if self.card_paste_number % 9 == 1:
            self.vertical = 22
            self.horizontal = 50
        elif self.card_paste_number % 3 == 1:
            self.horizontal = 50
            self.vertical += 740
        else:
            self.horizontal += 500
