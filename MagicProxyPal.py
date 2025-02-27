import glob
import os
from tkinter import *
import requests
from CardDatabase import CardDatabase
from CardEntry import CardEntry
from PdfHandler import PdfHandler


class MagicProxyPal:
    def __init__(self):
        self.fallback_card_names = []
        self.root = Tk()
        self.root.title("Magic Proxy Pal")

        self.frame = Frame(self.root, bd=3, height=100, relief=RAISED, width=100)

        self.frame.grid(column=0, row=0)

        self.right_frame = Frame(self.root, bd=3, height=100, relief=RAISED, width=50)
        self.right_frame.grid(column=1, row=0, rowspan=2)
        self.generate_pdf_button = Button(self.right_frame, text="Generate PDF", command=self.pdf_generate_button_click)
        self.generate_pdf_button.pack()
        delete_images_button = Button(self.right_frame, text="Delete Saved Images",
                                      command=self.delete_images_button_pressed)
        delete_images_button.pack()

        self.label = Label(self.frame, text="Deck List")
        self.label.pack()
        self.deck_entry = Text(self.frame, height=20, width=80)
        self.deck_entry.pack()


        self.output_frame = Frame(self.root, bd=3, height=100, relief=RAISED, width=200)
        self.output_frame.grid(row=1, column=0)
        self.output_label = Label(self.output_frame, text="Output")
        self.output_label.pack()
        self.output_text = Text(self.output_frame, height=10, width=100, bg="black", fg="white")
        self.output_text.pack()
        self.cards = []
        self.missed_card_names = []
        if not os.path.exists("images"):
            os.makedirs("images")
        self.database = CardDatabase()
        self.database.startup_db()
        self.pdfHandler = PdfHandler()


    def delete_images_button_pressed(self):
        for file in glob.glob("images/*.jpg"):
            os.remove(file)
        self.append_log("Deleted contents of images folder.")

    def pdf_generate_button_click(self):
        self.missed_card_names = []
        self.fallback_card_names = []
        deck_raw_text = self.deck_entry.get(1.0, END)
        self.output_text.delete(1.0, END)
        self.parse_deck_list(deck_raw_text)
        for card in self.cards:
            self.retrieve_card_uri_from_db(card)
        for card in self.cards:
            self.get_image(card)

        self.pdfHandler.generate_pdf(self.cards)

        self.append_log("\n\nPDF Creation complete\n\n")

        if len(self.missed_card_names) > 0:
            self.append_log("The following cards were missed:\n")
            for name in self.missed_card_names:
                self.append_log(name + "\n")
        else:
            self.append_log("No cards were missed.\n")
        if len(self.fallback_card_names) > 0:
            self.append_log("The following cards are using fallback art:\n")
            for name in self.fallback_card_names:
                self.append_log(name + "\n")
        else:
            self.append_log("No cards are using fallback art.\n")

    def parse_deck_list(self, raw_deck_list):
        self.cards = []
        for line in raw_deck_list.splitlines():
            if len(line) > 0 and line[0].isnumeric and "x" in line:
                x_index = line.index("x")
                name_end_index = line.index("(")
                set_end_index = line.index(")")
                card_quantity = line[0:x_index]
                card_name = line[x_index + 1:name_end_index].strip()
                card_set_abrv = line[name_end_index + 1:set_end_index].strip()
                card_collector_number = line[set_end_index + 1:].strip()
                if not self.is_basic_land(card_name):
                    new_card_entry = CardEntry(int(card_quantity), card_name, card_set_abrv, card_collector_number,
                                               None)
                    self.cards.append(new_card_entry)
                    self.append_log(str(new_card_entry) + "\n")

    def retrieve_card_uri_from_db(self, card: CardEntry):
        result = self.database.set_card_uri(card)
        if result == "Fallback":
            self.append_log("Using fallback art for " + str(card) + "\n")
            self.add_card_fallback_list(str(card))
        elif card.image_uri is None:
            self.append_log("No image found for: " + str(card) + "\n")
            self.missed_card_names.append(str(card))

    def get_image(self, card: CardEntry):
        file_name = "images/" + str(card).replace("/", "-") + ".jpg"
        if os.path.exists(file_name):
            self.append_log("Image already exists for " + str(card) + "\n")
            return
        if card.image_uri is None:
            return
        response = requests.get(card.image_uri, stream=True)
        self.append_log(f"Downloading image for {str(card)}\n")
        if response.status_code == 200:
            with open(file_name, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            self.append_log(f"Image downloaded successfully for {str(card)}\n")
        else:
            self.append_log(f"Error: {response.status_code} when downloading image for {str(card)}\n")
            self.add_card_to_missed_list(str(card))

    def run(self):
        self.root.mainloop()

    def is_basic_land(self, card_name):
        return card_name in ["Island", "Swamp", "Forest", "Plains", "Mountain"]

    def append_log(self, message):
        self.output_text.insert(END, message)
        self.output_text.see(END)

    def clear_log(self):
        self.output_text.delete(1.0, END)

    def add_card_to_missed_list(self, card_name):
        if card_name not in self.missed_card_names:
            self.missed_card_names.append(card_name)

    def add_card_fallback_list(self, card_name):
        if card_name not in self.missed_card_names:
            self.fallback_card_names.append(card_name)
