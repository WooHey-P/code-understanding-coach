# DEMO-ko — README demo (Korean): misconception, transfer, stop (claude)

## Developer

프로젝트 이해도 점검해줘


## Assistant

전체 프로젝트 기준으로 점검할게요. 프로젝트가 작아서(`app/` 아래 모듈 8개) 주요 흐름을 대부분 다룰 수 있지만, 그래도 표본 질문이라 이해도를 전부 보증하지는 않아요. 코드를 열어 놓고 답하셔도 됩니다. 질문은 한 번에 하나씩 드릴게요.

---

**질문 1 — 대여 흐름 (라우팅 → 인증 → 대여 → 저장 → 알림)**

상황: 메일 서버(`SMTP_HOST`)가 내려가서 연결이 즉시 거부되고 있어요. 로그인한 회원이 유효한 토큰으로 `POST /rentals`를 보내고, 대여할 책은 남은 수량이 1권이에요.

이 회원은 어떤 응답을 받을까요? 그리고 그 이유는 뭘까요?

시작 지점: `app/server.py:6` (`handle`)


_tools: Skill, Read, Read, Bash, Read, Read, Read, Read, Read, Read, Read, Read, Read, Read, Read_

## Developer _(simulated developer: misconception)_

아마 500 에러 받을 거예요. `rent`에서 영수증 메일을 먼저 보내고 나서 저장하는데, SMTP 연결이 거부되면 거기서 예외가 그대로 올라가요. 그래서 대여는 저장이 안 되고 재고도 1권 그대로 남아요.


## Assistant

**판정: 오해가 있어요.** 순서를 거꾸로 보셨고, 예외 처리도 놓치셨어요.

실제로 실행되는 경로는 이래요.

1. `app/rentals.py:13`: 재고를 확인해요(1권이라 통과).
2. `app/rentals.py:17`: 재고를 1 줄이고, `:25`에서 대여 기록을 추가한 다음, **`:26`의 `storage.save(db)`에서 파일에 먼저 저장해요.**
3. 메일은 그 다음인 `app/rentals.py:29`에서 보내요.
4. `app/notifications.py:15-19`에서는 SMTP 연결과 전송이 `try`로 감싸져 있고, `except Exception: pass`가 **모든 예외를 삼켜요.** 그래서 연결이 거부돼도 `rent`까지 예외가 올라오지 않아요.
5. 결국 `app/rentals.py:30`에서 **201과 `due_at`**을 돌려줘요. 대여는 저장되고 재고는 0이 돼요. 회원만 영수증을 못 받아요.

참고로, 연결이 즉시 거부되는 게 아니라 응답 없이 멈추는 경우에는 `timeout=5`(`app/notifications.py:16`) 때문에 응답이 최대 5초쯤 늦어질 수 있어요. 결과는 똑같이 201이에요.

---

**질문 1-1 (전이 질문) — 같은 대여 흐름, 다른 실패 지점**

*가정 상황(현재 데이터에 이런 경우가 있다는 뜻은 아니에요):* 어떤 회원의 `members` 항목에 `email` 키가 빠져 있어요. 이 회원이 남은 수량이 1권인 책을 `POST /rentals`로 대여해요. SMTP 서버는 정상이에요.

이 요청이 끝난 뒤 `data/library.json`에 이 대여 기록이 남아 있을까요? 그 이유는 뭘까요?

시작 지점: `app/rentals.py:10` (`rent`)


_tools: Read, Read_

## Developer _(simulated developer: correct)_

네, 남아 있어요. 대여 기록은 영수증 보내기 전에 이미 파일에 저장되거든요. 이메일이 없어서 메일 쪽에서 예외가 나도 저장은 이미 끝난 상태라 기록이랑 재고 0은 그대로 남아요.


## Assistant

**판정: 이해하셨어요. (설명을 들은 뒤)** 저장은 `app/rentals.py:26`, 이메일 조회는 `:28-29`에서 일어나서, 기록과 재고 0은 그대로 남아요.

한 가지만 정확히 짚을게요. 예외는 "메일 쪽" 안에서 나는 게 아니에요. `send_receipt`를 호출하기 **전에**, 인자를 만드는 `member["email"]`(`app/rentals.py:29`)에서 `KeyError`가 나요. 이 줄은 `notifications.py`의 `try` 밖이라서 예외가 그대로 올라가요. 그래서 회원은 201을 받지 못하는데, 데이터는 이미 바뀐 상태로 남아요.

---

**질문 2 — 회원 로그인과 잠금 (`app/auth.py`)**

상황: 서버가 재시작 없이 계속 떠 있어요. 누군가 `alice` 계정에 틀린 비밀번호로 `POST /login`을 연속 5번 보냈어요. 그 직후 alice 본인이 **올바른** 비밀번호로 로그인을 시도해요.

alice는 어떤 응답을 받을까요? 그 이유는 뭘까요?

시작 지점: `app/server.py:11`


_tools: Read, Read_

## Developer

여기까지 할게요. 정리해 주세요.


## Assistant

```text
범위: 전체 프로젝트 — project (도서 대여 서비스)
다룬 영역: 대여 흐름 — app/server.py, app/rentals.py(rent), app/notifications.py, app/storage.py
다루지 않은 영역: 반납과 연체료(app/rentals.py return_book, late_fee_cents), 회원 세션 만료와 로그아웃(app/auth.py),
          관리자 로그인과 재고 추가(app/admin.py, app/catalog.py add_copies), 설정(app/config.py)
          ※ 로그인 잠금은 질문만 드리고 답을 듣지 못해서 판단하지 않았어요.
결과:
  1. 대여 시 저장과 메일 발송의 순서, 메일 실패 처리 — 오해 있었음
  1-1. 저장 이후에 난 실패가 데이터에 남기는 영향(전이 질문) — 설명을 들은 뒤 이해함
  2. 로그인 실패 누적과 계정 잠금 — 판단 불가 (답변 전에 종료)
확인된 이해: 대여 기록은 영수증 발송 전에 파일에 저장된다는 순서
다시 볼 만한 부분:
  - 메일 예외가 어디서 삼켜지는지와 그 범위 — app/notifications.py:15-19
  - try 밖에서 난 예외는 저장이 끝난 뒤에도 호출자에게 올라감 — app/rentals.py:26-30
  - (답하지 못한 질문 2) 잠금 확인과 비밀번호 검증의 순서, 실패 카운터 초기화 — app/auth.py:22-31
    주석에는 "3회"라고 적혀 있는데, 실제 기준은 config.MAX_FAILED_LOGINS입니다(app/config.py:7).
한계: 질문과 채점을 같은 어시스턴트가 했어요. 표본 점검이라 전체를 감사한 결과가 아니고,
      묻지 않은 영역은 판단하지 않았어요.
```

수고하셨어요. 다음에는 질문 2나 반납·연체료 흐름부터 이어서 해도 좋아요.

