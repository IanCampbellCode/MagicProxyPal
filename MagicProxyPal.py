import glob
import os
import tkinter
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

        parent_menu = Menu(self.root)
        self.root.config(menu=parent_menu)
        file_menu = Menu(parent_menu, tearoff=0)
        parent_menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Help", command=self.show_help)
        file_menu.add_command(label="Exit", command=self.root.quit)

        self.right_frame = Frame(self.root, height=100, relief=RAISED, width=50)
        self.right_frame.grid(column=1, row=0, rowspan=2, padx=5, pady=5)
        self.generate_pdf_button = Button(self.right_frame, text="Generate PDF", command=self.pdf_generate_button_click)
        self.generate_pdf_button.pack()
        delete_images_button = Button(self.right_frame, text="Delete Saved Images",
                                      command=self.delete_images_button_pressed)
        delete_images_button.pack()
        self.update_database_button = Button(self.right_frame, text="Update Database", command=self.update_catalog)
        self.update_database_button.pack()

        self.leftFrame = Frame(self.root, relief=RAISED)
        self.leftFrame.grid(column=0, row=0)
        self.label = Label(self.leftFrame, text="Deck List")
        self.label.pack()
        self.deck_entry = Text(self.leftFrame, height=20, width=80)
        self.deck_entry.pack()

        self.output_frame = Frame(self.root, relief=RAISED)
        self.output_frame.grid(row=1, column=0, padx=5, pady=5)
        self.output_label = Label(self.output_frame, text="Output")
        self.output_label.pack()
        self.output_text = Text(self.output_frame, height=10, bg="black", fg="white")
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
        self.append_log("Deleted contents of images folder.\n")

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

    def update_catalog(self):
        # Request to get latest of bulk downloads
        if self.database.db_connection is not None:
            self.database.db_connection.close()
        if os.path.exists("res/data/catalog.json"):
            os.remove("res/data/catalog.json")
        if os.path.exists("res/data/CardDatabase.db"):
            os.remove("res/data/CardDatabase.db")
        self.append_log("Deleted old catalog and database\n")
        response = requests.get(' https://api.scryfall.com/bulk-data')
        if response.status_code != 200:
            self.append_log("Failed to get bulk data from scryfall. Better get the catalog yourself.\n")
            return
        response_data = response.json()["data"]
        catalog_uri = None
        x = 0
        self.append_log("Retrieved Location of newest catalog.\nDownloading catalog now.\n")
        while x < len(response_data) and catalog_uri is None:
            if response_data[x].get("type") == "default_cards":
                catalog_uri = response_data[x].get("download_uri")
        with requests.get(catalog_uri, stream=True) as response:
            response.raise_for_status()
            with open("res/data/catalog.json", "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        self.append_log("New catalog downloaded.\nPopulation database.\n")
        self.database.startup_db()
        self.append_log("Database populated successfully.\n")



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

    def show_help(self):
        help_window = tkinter.Toplevel()
        help_window.title("Magic Proxy Pal Help")
        help_usage_label_1 = Label(help_window, text="Copy a deck list from tappedout then paste it into the deck list"
                                                     "to generate a pdf")
