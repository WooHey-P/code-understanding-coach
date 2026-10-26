# Book Rental

A small book-rental service for a neighborhood library. Members log in, rent books for
two weeks, and pay a late fee when they return them late. Staff use a separate admin
login to manage the catalog.

Plain Python 3 standard library. Data lives in `data/library.json`.

## Layout

- `app/server.py` — request routing
- `app/auth.py` — member login and sessions
- `app/admin.py` — staff login and catalog management
- `app/catalog.py` — books and available copies
- `app/rentals.py` — renting and returning
- `app/notifications.py` — e-mail receipts
- `app/storage.py` — JSON persistence
- `app/config.py` — settings
