class Catalog:
    def __init__(self, rows):
        self.rows = rows

    def get(self, item_id):
        return next((row for row in self.rows if row["id"] == item_id), None)
