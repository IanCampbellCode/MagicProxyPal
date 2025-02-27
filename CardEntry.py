class CardEntry:
    def __init__(self, quantity, name, set_abrv, collector_number, image_uri):
        self.quantity = quantity
        self.name = name
        self.set_abrv = set_abrv
        self.collector_number = collector_number
        self.image_uri = image_uri

    def __str__(self):
        return self.name + " (" + self.set_abrv + ") " + self.collector_number