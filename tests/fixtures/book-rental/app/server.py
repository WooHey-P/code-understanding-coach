"""Request routing. A request is a dict: {"method", "path", "headers", "body"}."""

from app import admin, auth, catalog, rentals


def handle(request):
    route = (request["method"], request["path"])
    body = request.get("body") or {}
    token = request.get("headers", {}).get("Authorization", "")

    if route == ("POST", "/login"):
        return auth.login(body.get("username", ""), body.get("password", ""))
    if route == ("POST", "/admin/login"):
        return admin.admin_login(body.get("password", ""))
    if route == ("GET", "/books"):
        return {"status": 200, "books": catalog.list_books()}
    if route == ("POST", "/admin/books/copies"):
        return admin.add_copies(token, body.get("book_id", ""), int(body.get("count", 0)))

    username = auth.current_member(token)
    if username is None:
        return {"status": 401, "error": "login required"}

    if route == ("POST", "/rentals"):
        return rentals.rent(username, body.get("book_id", ""))
    if route == ("POST", "/returns"):
        return rentals.return_book(username, body.get("book_id", ""))
    if route == ("POST", "/logout"):
        auth.logout(token)
        return {"status": 204}
    return {"status": 404, "error": "not found"}
