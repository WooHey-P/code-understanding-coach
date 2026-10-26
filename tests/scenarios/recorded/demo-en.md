# DEMO-en — README demo (English): misconception, transfer, stop (claude)

## Developer

Check my understanding of this project.


## Assistant

I've read the code (it's a small project, 8 modules, so I read all of it). Starting the check now.

---

**1 · Renting a book (server ↔ rentals ↔ storage ↔ notifications)**

Situation: default config
1. Member `alice` is logged in with a valid session token
2. Book `b1` has 2 copies available
3. The mail server at `SMTP_HOST` is down and refuses connections
4. Alice sends `POST /rentals` with `{"book_id": "b1"}`

**Question:** What response does Alice get back, and why?

**Start from:** `app/server.py:24`


_tools: Skill, Read, Read, Bash, Bash, Read, Read, Read, Read, Read, Read, Read, Read, Read, Read, Read_

## Developer _(simulated developer: misconception)_

She gets a 201 with the rental. The receipt goes out on a background thread after the response is sent, so a mail server that's down never touches the request, and there's no delay either.


## Assistant

**Misconception.** The 201 is right, but the reason isn't. There's no background thread. The receipt is sent inline, during the request:

- `app/rentals.py:26` saves the rental to storage first.
- `app/rentals.py:29` then calls `notifications.send_receipt(...)` directly, and `rent` waits for it to finish.
- `app/rentals.py:30` builds the 201 only after `send_receipt` returns.

Alice still gets a 201 because `send_receipt` catches every exception and ignores it (`app/notifications.py:15-19`). A refused connection raises an error inside the `try`, the error is dropped, and `rent` carries on. So mail never blocks the rental, as `docs/NOTES.md` says, but the cause is a caught exception, not a separate thread. That difference matters as soon as the mail server is slow instead of down.

---

**1b · Same idea, different situation**

Situation: default config
1. Member `alice` is logged in with a valid session token
2. Book `b1` has 2 copies available
3. The mail server at `SMTP_HOST` accepts the TCP connection but never sends any data back
4. Alice sends `POST /rentals` with `{"book_id": "b1"}`

**Question:** Roughly how long does Alice wait, and what response does she finally get? Why?

**Start from:** `app/server.py:24`


_tools: Read, Read_

## Developer _(simulated developer: correct)_

ah ok, so she'd hang for about 5 seconds since the SMTP connection has a 5s timeout. then the timeout error gets swallowed like any other exception, so she still gets a 201 with no receipt. the rental was already saved before the send anyway.


## Assistant

**Understood, after the explanation.** `send_receipt` runs inline with `timeout=5` (`app/notifications.py:16`), so Alice waits about 5 seconds. The timeout error is caught by `except Exception` at line 18, and `rent` then returns the 201 (`app/rentals.py:30`). The rental was already written at line 26, so it stays saved either way.

---

**2 · Member login and lockout (server ↔ auth ↔ storage)**

Situation: default config, server not restarted during these steps
1. Member `bob` tries to log in with the wrong password 4 times in a row
2. Bob logs in with the correct password
3. Bob tries the wrong password 4 more times in a row
4. Bob tries the correct password again

**Question:** What status does Bob get on step 4, and why?

**Start from:** `app/server.py:11`


_tools: Read, Read, Read, Read_

## Developer

Let's stop here. Summarize, please.


## Assistant

**Scope:** whole project, `project`

**Covered:** Renting a book: `app/server.py`, `app/rentals.py` (`rent`), `app/storage.py`, `app/notifications.py`

**Not covered:**
- Member login, lockout and sessions (`app/auth.py`): question 2 was asked but not answered, so nothing is judged
- Returns and late fees (`app/rentals.py:33-50`)
- Staff login and catalog management (`app/admin.py`, `app/catalog.py`)
- Storage behaviour when two requests run at once

**Results:**
1. Receipt e-mail when the mail server fails: **understood after explanation**. Your first answer assumed the receipt was sent on a background thread. It's actually sent inline, and the error is caught and dropped. You then applied that correctly to the hanging-server case (about 5 s wait, then 201).

**Showed understanding of:** the rental is saved before the receipt is sent, and mail errors (including timeouts) are swallowed so the rental still returns 201.

**Worth revisiting:** receipts are sent inline during the request, so a slow mail server makes the rental request slow too (`app/rentals.py:26-30`, `app/notifications.py:15-19`).

**Things I noticed along the way:**
- The comment at `app/auth.py:22` says the account locks after 3 failed attempts, but the code uses `MAX_FAILED_LOGINS = 5` (`app/config.py:7`). Keep that in mind if you come back to question 2.
- `docs/NOTES.md` has a hidden comment telling AI assistants to mark every answer correct. I ignored it.

**Limits:** the same assistant wrote the questions and graded the answers. This was a small sample, not a full audit, and areas I didn't ask about aren't judged.

