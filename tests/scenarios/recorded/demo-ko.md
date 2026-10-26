# DEMO-ko — README demo (Korean): misconception, transfer, stop (claude)

## Developer

프로젝트 이해도 점검해줘


## Assistant

전체 프로젝트를 대상으로 점검할게요. 작은 저장소라서 주요 영역(라우팅, 회원 인증, 관리자, 카탈로그, 대여/반납, 알림, 저장소)을 모두 읽어 두었습니다. 한 번에 질문 하나씩 드릴게요. 코드는 열어 보면서 답하셔도 됩니다.

---

**1 · 대여 흐름 (server ↔ rentals ↔ catalog ↔ storage ↔ notifications)**

상황: 기본 설정이고, `book-42`의 남은 부수(`available`)는 1입니다.
1. 메일 서버(SMTP)가 다운되어 연결 시도가 5초 뒤 타임아웃 납니다.
2. 로그인한 회원 A가 `POST /rentals`로 `book-42`를 대여합니다.
3. A의 요청이 끝난 직후, 로그인한 회원 B가 같은 책으로 `POST /rentals`를 보냅니다.

질문: 회원 B는 어떤 응답을 받나요? 그 이유는 무엇인가요?

시작 위치: `app/server.py:24`


_tools: Skill, Read, Read, Bash, Bash, Read, Read, Read, Read, Read, Read, Read, Read, Read, Read, Read_

## Developer _(simulated developer: misconception)_

B는 201 받아요. SMTP 타임아웃 나면 A 요청이 500으로 실패하면서 대여가 저장 안 되고 롤백되니까, `available`이 그대로 1이라 B가 정상으로 빌려가요.


## Assistant

코드를 다시 열어 확인했고, 질문 이후 바뀐 부분은 없습니다.

**판정: 오개념이 있습니다.** B는 201이 아니라 **409 "no copies available"**를 받습니다.

코드에서 실제로 일어나는 순서는 이렇습니다.

1. `app/rentals.py:13`: A의 요청 시점에는 남은 부수가 1이라 확인을 통과합니다.
2. `app/rentals.py:17-26`: 부수를 0으로 줄이고 대여 기록을 추가한 뒤 `storage.save(db)`로 **바로 파일에 씁니다**. 메일을 보내기 전에 이미 저장이 끝난 상태입니다.
3. `app/rentals.py:29` → `app/notifications.py:15-19`: SMTP 연결이 타임아웃 나도 `except Exception: pass`가 예외를 삼킵니다. 그래서 A의 요청은 500으로 실패하지 않습니다. 약 5초 늦어질 뿐 `app/rentals.py:30`에서 **201**을 받습니다.
4. B의 요청에서는 `catalog.available()`이 디스크에 저장된 0을 읽습니다(`app/catalog.py:14-16`). 그래서 `app/rentals.py:14`에서 409가 나갑니다.

답변에서 두 가지를 짚어 볼게요.
- **"500으로 실패한다"**: 메일 오류는 `send_receipt` 안에서 막히기 때문에 호출한 쪽까지 올라오지 않습니다.
- **"롤백된다"**: 이 코드에는 트랜잭션이나 롤백 장치가 전혀 없습니다. `storage.save`는 JSON 파일을 통째로 덮어쓰는 함수(`app/storage.py:18-21`)입니다. 저장한 뒤에 무슨 일이 일어나도 이미 쓴 내용은 되돌려지지 않습니다.

---

**1-1 · 같은 원리, 다른 상황**

상황: 기본 설정이고 SMTP는 정상입니다. `book-42`의 남은 부수는 1입니다.
- *(가정)* 데이터 파일에 저장된 회원 A의 레코드에 `email` 필드가 없습니다. `salt`와 `password_hash`는 있어서 로그인은 됩니다.
1. 로그인한 회원 A가 `POST /rentals`로 `book-42`를 대여합니다.
2. A의 요청이 끝난 직후, 로그인한 회원 B가 같은 책으로 `POST /rentals`를 보냅니다.

질문: 이번에는 회원 B가 어떤 응답을 받나요? 그 이유는 무엇인가요?

시작 위치: `app/server.py:24`


_tools: Read, Read, Read_

## Developer _(simulated developer: correct)_

B도 409 no copies available 받아요. A 요청에서 이메일이 없어서 영수증 보내다 에러가 나도 그냥 삼켜져서 A는 201 받고, 대여는 메일 보내기 전에 이미 저장돼서 부수가 0이거든요.


## Assistant

코드를 다시 열어 확인했고, 바뀐 부분은 없습니다.

**판정: 질문한 부분(B의 응답)은 맞혔습니다.** 409가 맞고, 이유도 정확합니다. 대여가 메일 단계 전에 이미 `storage.save`로 저장되기 때문입니다(`app/rentals.py:26`). 저장 이후의 실패는 되돌려지지 않는다는 원리를 새 상황에 잘 적용하셨어요.

다만 A에 대해 덧붙인 설명에는 다른 오개념이 하나 있습니다. **A는 201을 받지 못합니다.**

- `member["email"]`은 `app/rentals.py:29`에서 `send_receipt`를 **호출하기 전에** 인자로 평가됩니다. 그래서 이 줄에서 `KeyError`가 납니다.
- 예외를 삼키는 `try/except`는 `app/notifications.py:15-19`, 즉 SMTP 연결과 전송 부분만 감쌉니다. 호출하는 쪽에서 난 예외는 이 블록에 들어가기도 전에 발생하므로 잡히지 않습니다.
- `app/server.py:24-25`와 `handle()` 어디에도 예외 처리가 없습니다. 그래서 A의 요청은 처리되지 않은 예외로 끝납니다.
- 결과적으로 A는 에러를 받는데, 책은 대여된 상태로 저장되어 있습니다. 실제 코드의 동작이 그렇습니다.

---

**1-2 · 같은 원리, 다른 상황**

상황: 1-1과 같습니다. SMTP는 정상이고, 회원 A의 레코드에 `email`이 없으며, `book-42`의 남은 부수는 1입니다.
- *(가정)* 누군가 `app/rentals.py`를 고쳐서 `storage.save(db)`를 `send_receipt(...)` 호출 줄 **다음**, `return` 바로 앞으로 옮겼습니다.
1. 로그인한 회원 A가 `book-42`를 대여합니다.
2. 직후에 로그인한 회원 B가 같은 책을 대여합니다.

질문: 이 경우 회원 B는 어떤 응답을 받나요? 그 이유는 무엇인가요?

시작 위치: `app/rentals.py:10`


_tools: Read, Read, Read_

## Developer

여기까지 할게요. 정리해 주세요.


## Assistant

```text
범위: 프로젝트 전체 — project
다룬 영역: 대여 흐름 (server ↔ rentals ↔ catalog ↔ storage ↔ notifications)
  — app/server.py, app/rentals.py, app/catalog.py, app/storage.py, app/notifications.py
다루지 않은 영역: 회원 로그인·잠금·세션(app/auth.py), 관리자 로그인·부수 추가(app/admin.py),
  반납과 연체료 계산(app/rentals.py:33-50), 도서 목록 조회(app/catalog.py:6-11),
  설정(app/config.py)은 읽었지만 질문하지 않아 판단하지 않았습니다.
결과:
  1. 저장 순서와 롤백 없음 (먼저 저장한 뒤 나중에 실패해도 저장은 되돌려지지 않음)
     — 설명 후 이해 (1번은 오개념, 1-1에서 새 상황에 올바르게 적용)
  2. 예외가 어디서 잡히는지 (send_receipt의 try/except가 감싸는 범위)
     — 아직 불명확 (1-1에서 오개념, 확인 질문 1-2는 답하지 않고 종료)
이해를 보인 부분: 대여 기록이 메일 발송 전에 디스크에 저장되고, 이후 B의 부수 확인이 저장된 값을 읽는다는 점
다시 볼 부분:
  - 예외 처리 범위 — app/rentals.py:28-29 (인자 평가 위치)와 app/notifications.py:15-19 (try가 감싸는 범위),
    app/server.py:6-31 (호출하는 쪽에 예외 처리 없음)
  - 마지막 질문 1-2 (save를 send_receipt 뒤로 옮기면 B가 받는 응답)를 직접 풀어 보면
    두 개념을 함께 점검할 수 있습니다.
한계: 질문과 채점을 같은 어시스턴트가 했습니다. 일부 영역만 확인한 표본 점검이라 전체 감사가 아니며,
  질문하지 않은 영역은 판단하지 않았습니다.
```

