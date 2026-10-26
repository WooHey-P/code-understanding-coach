"""Renting and returning books."""

import time

from app import catalog, config, notifications, storage

DAY = 24 * 60 * 60


def rent(username, book_id, now=None):
    now = time.time() if now is None else now

    if catalog.available(book_id) < 1:
        return {"status": 409, "error": "no copies available"}

    db = storage.load()
    db["books"][book_id]["available"] -= 1
    rental = {
        "username": username,
        "book_id": book_id,
        "rented_at": now,
        "due_at": now + config.RENTAL_DAYS * DAY,
        "returned_at": None,
    }
    db["rentals"].append(rental)
    storage.save(db)

    member = db["members"][username]
    notifications.send_receipt(member["email"], "Rental receipt", f"Due back in {config.RENTAL_DAYS} days.")
    return {"status": 201, "due_at": rental["due_at"]}


def late_fee_cents(due_at, returned_at):
    if returned_at <= due_at:
        return 0
    days_late = int((returned_at - due_at) // DAY) + 1
    return min(days_late * config.LATE_FEE_PER_DAY_CENTS, config.LATE_FEE_CAP_CENTS)


def return_book(username, book_id, now=None):
    now = time.time() if now is None else now
    db = storage.load()
    for rental in db["rentals"]:
        if rental["username"] == username and rental["book_id"] == book_id and rental["returned_at"] is None:
            rental["returned_at"] = now
            db["books"][book_id]["available"] += 1
            fee = late_fee_cents(rental["due_at"], now)
            storage.save(db)
            return {"status": 200, "late_fee_cents": fee}
    return {"status": 404, "error": "no open rental"}
