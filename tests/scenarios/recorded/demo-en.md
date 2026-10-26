# DEMO-en — README demo (English): misconception, transfer, stop (claude)

## Developer

Check my understanding of this project.


## Assistant

This is a small project (8 modules in `app/`), so I'll check it as a whole, one question at a time. You can keep the code open while you answer.

---

**Renting: rentals, storage and notifications.** A member is logged in with a valid session and sends `POST /rentals` for a book that has exactly 1 available copy. The mail server at `SMTP_HOST` is down, so any connection attempt to it fails.

**Does the rental go through, meaning the member gets the book and the copy count drops? Why or why not?**

Start from: `app/server.py:24`


_tools: Skill, Read, Read, Bash, Read, Read, Read, Read, Read, Read, Read, Read, Read, Read_

## Developer _(simulated developer: misconception)_

No, it fails. The receipt goes out before the rental is saved, so when the SMTP connection blows up the request errors out with a 500 and the save never happens. The copy count stays at 1.


## Assistant

**Grade: misconception.** Both the outcome and the reason are wrong.

The rental goes through. The member gets `201` with a `due_at`, and the copy count drops from 1 to 0. Here's the actual order:

1. `app/rentals.py:13` checks availability, then `app/rentals.py:16-26` loads the db, decrements `available`, appends the rental, and calls `storage.save(db)`. **The save happens first.**
2. Only after that, `app/rentals.py:29` calls `notifications.send_receipt(...)`.
3. Inside `send_receipt`, the SMTP connection is wrapped in `try / except Exception: pass` (`app/notifications.py:15-19`). The connection failure is caught and dropped, so nothing reaches `rent`.
4. `rent` continues to `app/rentals.py:30` and returns `201`.

So there are two separate reasons there's no 500. The save comes before the send, and the send can't raise anyway. The only thing the member notices is that the request may take a bit longer while the SMTP attempt fails (it has a 5-second timeout). They also get no receipt, and nothing is logged about that.

---

**Transfer question (hypothetical change).** Imagine someone moves the `notifications.send_receipt(...)` call so it runs **before** `storage.save(db)` on line 26. That's the order you described. Nothing else changes. The SMTP server is still down, and the same member rents the same last copy.

**Does the rental go through now? Why or why not?**

Start from: `app/rentals.py:10`


_tools: Read, Read_

## Developer _(simulated developer: correct)_

Yeah, it still goes through. send_receipt catches the SMTP error and swallows it, so nothing reaches rent and it carries on to the save and returns 201. The only differences are that the save now waits behind the SMTP timeout (up to about 5s), and a receipt could go out before the rental is actually written.


## Assistant

**Grade: understood after explanation.** You applied the idea to an ordering I hadn't walked through. The swallowing in `app/notifications.py:18-19` is what keeps `rent` safe no matter where the call sits, and the only cost is the timeout from `app/notifications.py:16`. You also caught a side effect I didn't ask about: with that ordering, a receipt could go out for a rental that never gets written.

Since this was after an explanation, I'll record it as "understood after explanation," not "understood from the start."

---

**Member login: auth and config.** The server was just started. A member types the wrong password at `POST /login` **5 times in a row**. On the **6th** try they type the **correct** password.

**What does the 6th request return, and why?**

Start from: `app/server.py:11`


_tools: Read, Read, Read, Read_

## Developer

Let's stop here. Summarize, please.


## Assistant

I didn't modify any code during this check; I only read files.

```text
Scope: whole project — book rental service (project/)
Covered: Renting flow — app/server.py, app/rentals.py, app/notifications.py, app/storage.py, app/catalog.py
Not covered: Member login/lockout and sessions (app/auth.py, app/config.py; question asked but not answered),
             returns and late fees (app/rentals.py:33-50), staff login and catalog management (app/admin.py),
             JSON persistence behavior (app/storage.py), tests (tests/test_rentals.py, not read)
Results:
  1. Receipt failure during a rental (save-then-send order; SMTP errors swallowed)
     — understood after explanation
     (first answer predicted a 500 and no save; the transfer question with the send moved
      before the save was answered correctly, including the up-to-5s delay and the risk of a
      receipt going out before the rental is written)
  2. Login lockout after repeated failures — undetermined (check ended before an answer)
Showed understanding of: send_receipt swallowing all exceptions so callers keep going;
  how moving a side effect before or after the save changes timing and consistency
Worth revisiting: order of save vs. receipt in rent — app/rentals.py:16-30;
  error swallowing — app/notifications.py:15-19;
  lockout check and threshold (the comment and the config value disagree) — app/auth.py:22-24, app/config.py:7
Limits: questions and grading came from the same assistant; this was a sample, not a
complete audit; areas not asked about are not judged.
```

