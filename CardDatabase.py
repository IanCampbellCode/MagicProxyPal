import json
import os
import sqlite3

from CardEntry import CardEntry


class CardDatabase:
    def __init__(self):
        self.db_connection = None
        self.cursor = None
        self.catalog_json_exists = None
        self.db_exists = None
        self.db_name = "CardDatabase.db"
        self.catalog_name = "catalog.json"

    def startup_db(self):
        self.db_exists = self.check_if_db_exists()
        self.catalog_json_exists = self.check_if_catalog_json_exists()
        if not self.db_exists and not self.catalog_json_exists:
            self.instruct_user_to_download_catalog_json()
            return
        if self.catalog_json_exists and not self.db_exists:
            self.convert_catalog_json_to_db()
            self.db_exists = True
            self.connect_to_db()
            self.load_db()
        elif self.db_exists:
            self.connect_to_db()

    def find_card(self, card_name, field):
        pass

    def load_db(self):
        with open(self.catalog_name, 'r', encoding='utf-8') as json_file:
            card_json = json.load(json_file)
        commit_batch = 0
        for card in card_json:
            if not card.get('image_uris') is None:
                self.cursor.execute(
                    "INSERT INTO Catalog (card_name, set_abrv, collector_number, uri) VALUES (?, ?, ?, ?)",
                    (card['name'], card['set'].upper(), card['collector_number'],
                     card['image_uris']['normal']))
                if commit_batch > 20000:
                    self.db_connection.commit()
                    commit_batch = 0
                commit_batch += 1
        self.db_connection.commit()

    def convert_catalog_json_to_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        table = "CREATE TABLE IF NOT EXISTS Catalog (id INTEGER PRIMARY KEY AUTOINCREMENT, card_name TEXT NOT NULL, set_abrv TEXT NOT NULL, collector_number TEXT NOT NULL,uri TEXT NOT NULL)"
        cursor.execute(table)
        conn.commit()
        conn.close()

    def check_if_db_exists(self):
        return os.path.exists(self.db_name)

    def check_if_catalog_json_exists(self):
        return os.path.exists(self.catalog_name)

    #Informs user on how to get the catalog file
    def instruct_user_to_download_catalog_json(self):
        pass

    def connect_to_db(self):
        self.db_connection = sqlite3.connect(self.db_name)
        self.cursor = self.db_connection.cursor()

    def set_card_uri(self, card: CardEntry) -> str:
        results = self.cursor.execute(
            "SELECT * FROM Catalog WHERE card_name= ? AND set_abrv = ? AND collector_number = ? ",
            (card.name, card.set_abrv, card.collector_number)).fetchall()
        if len(results) == 0:
            # Find card with the same name instead
            results = self.cursor.execute("SELECT * FROM Catalog WHERE card_name = ? ", (card.name,)).fetchall()
            if len(results) == 0:
                card.image_uri = None
                return "Missing"
            else:
                card.image_uri = results[0][4]
                return "Fallback"
        card.image_uri = results[0][4]
        return "Found"
