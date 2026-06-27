# QR UniPass — Attendance Demo · Build Guide for Claude Code

> 이 파일은 Claude Code가 읽고 그대로 구현하도록 작성된 빌드 명세서입니다.
> 새 저장소(repo) 루트에 `CLAUDE.md`로 저장한 뒤, Claude Code에게
> "Read CLAUDE.md and build the app described there." 라고 지시하세요.
> **앱의 모든 화면 문구(UI text)는 영어로 출력**합니다 (영어 피칭과 일치). 이 문서 설명은 한국어입니다.

---

## 0. 한 줄 목표 (What we are building)

8분 투자 피칭 중 **심사위원이 각자 휴대폰으로 QR을 찍으면, 실시간으로 출석 명단에 이름이 쌓이고, 발표자 화면(대시보드)의 출석 수가 즉시 올라가는** 라이브 데모 웹앱.

**이게 되면 데모는 성공이다:**
스크린에 QR 표시 → 관객이 폰으로 스캔 → 설치 없이 브라우저에서 check-in → 발표자 대시보드 카운트가 올라감.

---

## 1. 맥락 (Context — 왜 만드는가)

- **상황**: GYBM Korea–Vietnam 비즈니스 피칭. 아이디어는 "QR UniPass" — QR 하나로 캠퍼스(출석·식당·도서관·기숙사)를 통합 운영하는 스마트 대학 플랫폼.
- **평가**: Practicality & Feasibility가 배점 25%로 최고. "말로만"이 아니라 **실제 작동하는 MVP**를 보여주는 것이 핵심.
- **이 데모의 역할**: 발표 슬라이드 5번("Scan now")과 12번("The data you just created")에서 실행. 슬라이드의 QR이 이 앱의 공개 URL을 가리킨다.

---

## 2. 범위 (Scope)

### ✅ 이번에 만들 것 (MVP — 출석 모듈 하나만)
1. **Check-in page** (QR이 가리키는 기본 화면) — 학생/심사위원이 이름을 선택·입력하고 출석 제출.
2. **Admin dashboard** (발표자가 프로젝터에 띄움) — 출석 명단·카운트·시간 추이를 실시간 표시.
3. 두 화면이 **같은 데이터 저장소**를 공유 → 한쪽 제출이 다른 쪽에 바로 반영.
4. **공개 배포** (Streamlit Community Cloud) → 휴대폰 인터넷으로 접속 가능한 URL.

### 🟡 여유 되면 (Stretch — 구조 동일, 시간 남을 때만)
- Cafeteria 모듈: 가상 잔액(virtual balance) 차감 시뮬레이션 (실제 결제 연동 금지).
- 같은 패턴으로 library/dormitory는 만들지 않는다 — 발표에서 "동일 원리로 확장"이라고 말로 처리.

### ❌ 만들지 말 것 (Out of scope — 데모 신뢰성을 해친다)
- 로그인/회원가입/비밀번호 (마찰만 늘림 — 절대 금지).
- 실제 결제(VNPay/MoMo 등) 연동.
- 모바일 네이티브 앱 (웹만).
- 과한 인증·보안·관리자 권한 체계.
- 멋진 애니메이션·복잡한 상태관리. **단순함 > 화려함.**

---

## 3. 무대 위 데모 흐름 (The on-stage flow — 이대로 동작해야 함)

1. 발표자가 노트북에서 **Admin dashboard**를 열어 프로젝터에 띄운다 (출석 0명 상태).
2. 슬라이드 5의 QR을 화면에 표시 → "Please scan now."
3. 관객이 폰 카메라로 QR 스캔 → 브라우저에서 **Check-in page** 자동 오픈.
4. 이름을 드롭다운에서 선택(또는 입력) → **Check in** 버튼 → "✅ You're checked in!" 표시.
5. 제출과 거의 동시에(2~3초 내) Admin dashboard의 **카운트·명단·차트가 갱신**된다.
6. 발표 후반(슬라이드 12)에 대시보드를 다시 보여주며 "this is the data you just created."

> 핵심 제약: **발표장 와이파이/데이터로 접속**하므로, 네트워크만 되면 무조건 작동해야 한다. 동시 제출(약 10~30명)에도 깨지지 않을 것.

---

## 4. 기술 스택 & 제약 (Tech stack & constraints)

- **Language**: Python 3.11
- **Framework**: **Streamlit** (멀티페이지). 사용자(Chan)가 Streamlit Cloud 배포 경험 있음.
- **Data store**: **Google Sheets** via `gspread` (권장) — 아래 5절 참고. 설정 없이 가려면 **SQLite/CSV 로컬 파일** 대안.
- **Charts**: Streamlit 내장(`st.bar_chart`/`st.line_chart`) 또는 `altair`. 무거운 차트 라이브러리 금지.
- **Auto-refresh**: `streamlit-autorefresh` 패키지 또는 `st.rerun()` 기반 폴링.
- **QR**: `qrcode[pil]` — 배포 URL을 QR PNG로 생성하는 보조 스크립트 포함(슬라이드 QR 교체용).
- **Deploy**: Streamlit Community Cloud (무료, 공개 URL).
- **환경**: 저사양 노트북 가정 — 의존성 최소화, 무거운 빌드 금지.
- **Secrets**: API 키/서비스계정 JSON은 코드에 하드코딩 금지 → `st.secrets` (`.streamlit/secrets.toml`, Cloud에서는 Secrets UI) 사용.

---

## 5. 데이터 저장소 — 두 가지 옵션

### 옵션 A — Google Sheets (권장) ✅
**이유**: 모든 폰 제출이 같은 시트에 append → 대시보드가 실시간 read. Streamlit 앱이 재시작돼도 데이터 보존. 발표 중 시트 자체를 백업 비주얼로도 보여줄 수 있음.

**셋업 단계 (문서화하고, README에 적을 것):**
1. Google Cloud에서 서비스 계정(service account) 생성 → JSON 키 발급.
2. Google Sheet 1개 생성 (예: `qr-unipass-attendance`), 시트(worksheet) 이름 `attendance`.
3. 그 Sheet를 서비스 계정 이메일과 **편집 권한으로 공유**.
4. JSON 키를 `st.secrets`(로컬: `.streamlit/secrets.toml`, Cloud: Secrets UI)에 넣음.
5. `gspread` + `google-auth`로 연결. append/read 함수 작성.

> ⚠️ 사용자가 직접 해야 하는 부분(서비스계정 생성, 시트 공유, secrets 입력)은 **코드로 하지 말고**, README에 단계별로 명확히 안내할 것. 키 값은 절대 코드/깃에 커밋 금지.

### 옵션 B — SQLite / CSV 로컬 파일 (제로 설정 대안) 🟡
**이유**: 외부 계정·secrets 불필요. Streamlit Community Cloud는 단일 인스턴스라 모든 사용자가 같은 서버 파일에 기록 → 대시보드가 같은 파일 read 가능.
**주의(README에 명시)**: Cloud 파일시스템은 재배포/재시작 시 **초기화(ephemeral)**됨. 동시 쓰기 레이스 가능. → 데모 직전에 리셋되며, 한 세션 동안만 보장. 리허설·본 발표 전 "Reset" 버튼으로 비우고 시작.

> **기본값: 옵션 A로 구현하되, 환경변수/플래그(`USE_SHEETS=true/false`)로 옵션 B로 전환 가능하게 추상화**할 것. 저장 로직은 `storage.py` 한 곳에 모아 인터페이스(`add_checkin()`, `get_checkins()`, `reset()`)로 분리.

---

## 6. 데이터 모델 (Data model)

`attendance` 레코드 1건:

| field | type | 예시 | 비고 |
|---|---|---|---|
| `name` | string | "Nguyen Van A" | 필수 |
| `student_id` | string | "20231234" | 선택(있으면 중복판별에 사용) |
| `timestamp` | ISO datetime | "2026-07-03T14:05:11" | 서버 시각, 자동 |
| `source` | string | "classroom" | 모듈 구분(기본 "classroom") |

- 같은 `student_id`(없으면 `name`)가 다시 제출하면 **중복 카운트하지 않음**(이미 체크인됨 안내). 단, 데모 편의를 위해 이 중복방지는 토글 가능하게.

---

## 7. 화면별 요구사항 (UI는 전부 영어)

### 7-1. Check-in page = `app.py` (QR이 가리키는 기본 화면)
- **모바일 우선** 레이아웃. 한 화면에 끝나야 함(스크롤 최소).
- 구성:
  - 헤더: **"QR UniPass"** + 부제 **"Classroom Check-in"**
  - 이름 입력: 사전 로딩된 roster에서 **selectbox로 선택** + "name not listed?"일 때 **text input**으로 직접 입력 옵션. (roster는 `roster.csv` 또는 시트 `roster` 탭에서 로드; 없으면 자유 입력만.)
  - (선택) student ID text input.
  - 큰 버튼: **"Check in"**
  - 제출 성공: **"✅ You're checked in! — {name}, {time}"** 초록 메시지.
  - 이미 체크인된 경우: **"You're already checked in ✓"** 안내.
- 제출 시 `storage.add_checkin(...)` 호출 → 저장.
- **로그인 없음.** 최소 입력. 3초 안에 끝나는 경험.

### 7-2. Admin dashboard = `pages/1_Admin_Dashboard.py` (발표자용)
- 가벼운 접근 게이트(선택): `?key=...` 쿼리파라미터 또는 secrets의 패스코드. 강한 인증 불필요.
- **자동 새로고침**(예: 2~3초)으로 실시간 반영.
- 구성:
  - 헤더: **"QR UniPass — Live Attendance Dashboard"**
  - 큰 KPI 카드 3개: **Checked-in count**(대형 숫자), **Last check-in time**, **Check-in rate**(roster 대비 %, roster 없으면 생략).
  - **실시간 명단 테이블**: name · student_id · time (최신순).
  - **시간 추이 라인/바 차트**: 분 단위 누적 체크인.
  - 버튼: **"Reset"** (저장소 비우기 — 리허설/본 발표 직전 사용; 확인 후 실행).
  - 작은 캡션: 현재 데이터 소스 표시("Source: Google Sheets" / "Local store").
- 디자인 톤: 슬라이드와 통일감 — 네이비(#14294C) + 틸(#0CA678) + 코랄(#FA5252) 액센트. 과한 꾸밈 금지.

### 7-3. QR 생성 보조 스크립트 = `make_qr.py`
- 입력: 배포된 앱의 공개 URL.
- 출력: `qr.png` (네이비 on 흰색). 이걸 슬라이드 5·12의 임시 QR과 교체.
- 실행법 README에 기재.

---

## 8. 비기능 요구사항 (Non-functional)

- **신뢰성 최우선**: 발표장에서 절대 에러 화면이 뜨면 안 됨. 모든 외부 호출(시트 등)은 try/except로 감싸고, 실패 시 사용자에게는 부드러운 메시지, 콘솔에는 로그.
- **동시성**: 약 10~30명 동시 제출에도 안정. Sheets append는 순차 처리, 충돌 시 1회 재시도.
- **모바일**: 작은 화면에서 버튼·글자 충분히 큼. 가로/세로 모두 OK.
- **속도**: 체크인 페이지 로딩 1~2초 내. 무거운 import 지양.
- **리셋 용이**: 리허설 때마다 한 버튼으로 초기화.
- **시간대**: timestamp는 현지(Asia/Ho_Chi_Minh 또는 Asia/Seoul) 기준으로 표기.

---

## 9. 배포 (Deployment — Streamlit Community Cloud)

README에 단계별로:
1. GitHub에 public repo로 push (사용자 계정: `chan026-normal`).
2. share.streamlit.io에서 repo 연결 → `app.py`를 엔트리로 배포.
3. Secrets UI에 (옵션 A면) 서비스계정 JSON / 패스코드 입력.
4. 발급된 공개 URL 확보 → `make_qr.py`로 QR 생성 → 슬라이드 교체.
5. **발표 전 체크**: 실제 폰으로 QR 1회 스캔해 end-to-end 확인. URL 만료·오타 점검.

---

## 10. 인수 기준 / 데모데이 체크리스트 (Acceptance criteria)

구현 완료로 간주하려면 아래가 전부 참이어야 함:
- [ ] QR 스캔 → 설치 없이 브라우저에서 Check-in page 열림.
- [ ] 이름 선택/입력 후 "Check in" → 성공 메시지 표시.
- [ ] 같은 사람 재제출 시 중복 카운트 안 됨(토글로 끌 수 있음).
- [ ] Admin dashboard가 **2~3초 내 자동 갱신**되어 카운트·명단·차트 반영.
- [ ] 두 화면이 같은 저장소를 공유(한 폰 제출이 발표자 화면에 반영).
- [ ] 약 20건 동시 제출 시뮬레이션에서 에러 없음.
- [ ] "Reset" 버튼으로 깨끗이 비워짐.
- [ ] Streamlit Cloud 공개 URL에서 위 전부 동작.
- [ ] `make_qr.py`가 그 URL로 스캔 가능한 QR 생성.
- [ ] 어떤 단계에서도 사용자에게 raw 에러 트레이스가 보이지 않음.

---

## 11. 권장 파일 구조 (Suggested structure)

```
qr-unipass-demo/
├── CLAUDE.md                  # 이 문서
├── README.md                  # 셋업·배포·데모 진행 안내 (Claude Code가 작성)
├── requirements.txt           # streamlit, gspread, google-auth, streamlit-autorefresh, qrcode[pil], altair, pandas
├── app.py                     # Check-in page (QR 타깃, 기본 화면)
├── pages/
│   └── 1_Admin_Dashboard.py   # 발표자용 실시간 대시보드
├── storage.py                 # add_checkin / get_checkins / reset  (Sheets ↔ SQLite 추상화)
├── roster.csv                 # (선택) 사전 명단; 없으면 자유 입력
├── make_qr.py                 # 배포 URL → qr.png
└── .streamlit/
    ├── config.toml            # 테마(네이비/틸/코랄)
    └── secrets.toml.example    # 시크릿 양식(실제 키는 커밋 금지)
```

---

## 12. Claude Code 시작 지시 (First prompt)

이 repo에서 Claude Code에게:

> "Read CLAUDE.md. Build the attendance demo exactly as specified.
> Start with `storage.py` using the Google Sheets option behind a `USE_SHEETS` flag (with a local SQLite fallback), then `app.py` (check-in), then `pages/1_Admin_Dashboard.py` with auto-refresh, then `make_qr.py`. All UI text in English. Write a README covering Google service-account setup, Streamlit Cloud deploy, and the demo-day checklist. Do not implement login, real payments, or the library/dormitory modules. Keep it simple and reliable. When done, run through the acceptance checklist in section 10."

---

### 메모 (사용자용, 앱과 무관)
- 데이터 저장 방식은 옵션 A(Sheets) 권장이지만, 시간이 촉박하면 옵션 B(로컬)로 먼저 작동시키고 나중에 전환해도 됨 — `storage.py`만 바꾸면 됨.
- 발표장 와이파이가 불안하면 **폰 핫스팟을 백업**으로 준비.
- 본 발표 직전 반드시 **Reset** 후 시작(리허설 데이터 제거).
