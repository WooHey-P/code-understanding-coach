"""Books and available copies."""

from app import storage


def list_books():
    db = storage.load()
    return [
        {"id": book_id, "title": book["title"], "available": book["available"]}
        for book_id, book in sorted(db["books"].items())
    ]


def available(book_id):
    book = storage.load()["books"].get(book_id)
    return 0 if book is None else book["available"]


def add_copies(book_id, count):
    db = storage.load()
    book = db["books"].get(book_id)
    if book is None:
        return {"status": 404, "error": "no such book"}
    book["available"] += count
    storage.save(db)
    return {"status": 200, "available": book["available"]}
