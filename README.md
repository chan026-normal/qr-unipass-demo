# QR UniPass — Live Attendance Demo

A tiny, reliable web app for the GYBM pitch: the audience scans a QR code, checks
in from their phone (no install, no login), and the presenter's dashboard count
goes up in real time.

- **Check-in page** (`app.py`) — what the QR points to. Pick/type a name → **Check in**.
- **Admin dashboard** (`pages/1_Admin_Dashboard.py`) — projector view, auto-refreshes every 3s.
- Both share one data store, so a phone check-in shows up on the dashboard within ~3 seconds.

All on-screen text is **English** (to match the pitch). This README is the operator's manual.

---

## 1. Quick start (run on your laptop)

Requires Python 3.11 (3.12 also fine).

```bash
cd qr-unipass-demo
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Streamlit opens a browser tab:
- **Check-in page** = the page that opens (`app.py`).
- **Admin dashboard** = pick **"Admin Dashboard"** in the left sidebar.

Open both in two tabs, check in on one, and watch the other update. That's the whole demo.

> By default the app uses a **local file** (`attendance.db`) — no accounts, no setup.

---

## 2. Settings (all optional)

Settings are read from `.streamlit/secrets.toml` (local) or the Secrets UI (cloud).
Copy the template to start:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

| Setting | Default | What it does |
|---|---|---|
| `USE_SHEETS` | `false` | `true` switches storage to Google Sheets (section 4). |
| `ADMIN_KEY` | empty | If set, the dashboard requires `?key=YOUR_KEY` in the URL. |
| `ALLOW_DUPLICATES` | `false` | `true` lets the same person check in repeatedly. |
| `TIMEZONE` | `Asia/Ho_Chi_Minh` | Timezone for the times shown on screen. |

**Optional roster (dropdown of names):** rename `roster.csv.example` to `roster.csv`.
When present, the check-in page shows a name dropdown plus a "not listed" text box.
Leave it absent (the default) for a simple free-text name field — best when judges
type their own names.

---

## 3. Deploy to Streamlit Community Cloud (free public URL)

1. Push this folder to a **public GitHub repo** (account: `chan026-normal`).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select the repo.
3. Set **Main file path** to `app.py` → **Deploy**.
4. (Optional) Open **Settings → Secrets** and paste any settings from section 2.
5. Copy the public URL (e.g. `https://qr-unipass.streamlit.app`).
6. Generate the slide QR:
   ```bash
   python make_qr.py https://YOUR-APP.streamlit.app
   ```
   This writes `qr.png` (navy on white). Put it on slides 5 and 12.
7. The dashboard lives at `https://YOUR-APP.streamlit.app/Admin_Dashboard`.

> **Note on the default local store:** Streamlit Cloud runs one shared instance, so
> all phone check-ins land in the same `attendance.db` and the dashboard reads it.
> But the cloud filesystem is **wiped on restart/redeploy**, so data only lasts for
> a session. That's fine for a live demo — just hit **Reset** before you start.
> Want data that survives restarts? Use Google Sheets (section 4).

---

## 4. Optional: Google Sheets storage (persistent)

Only if you want check-ins to persist across restarts. Skip for a normal demo.

1. In **Google Cloud Console**, create a **Service Account** and download its **JSON key**.
2. Create a Google Sheet named **`qr-unipass-attendance`** with a worksheet/tab named **`attendance`**.
3. **Share** that Sheet with the service account's email (the `client_email` from the JSON),
   giving it **Editor** access.
4. Paste the JSON into your secrets under `[gcp_service_account]` and set `USE_SHEETS = "true"`
   (see `.streamlit/secrets.toml.example` for the exact layout). On the cloud, do this in the
   **Secrets UI**.
5. Redeploy / rerun. The dashboard caption will read **"Source: Google Sheets"**.

> 🔒 Never commit the JSON key or a real `secrets.toml`. They are in `.gitignore`.

---

## 5. Demo-day checklist

Before the talk:
- [ ] Open the **Admin dashboard** on the laptop → projector (shows 0).
- [ ] In **⚙️ Admin controls**, click **Reset** to clear any rehearsal data.
- [ ] Test once on a real phone: scan the slide QR → check in → confirm the dashboard ticks up.
- [ ] Confirm the QR on slides 5 and 12 points to the live URL (no typos / expired link).
- [ ] Backup plan: phone **hotspot** ready in case venue Wi-Fi is flaky.

During the talk:
- Slide 5 ("Scan now") → audience scans → check-ins appear.
- Slide 12 ("The data you just created") → show the dashboard again.

---

## 6. File map

```
qr-unipass-demo/
├── app.py                      # Check-in page (QR target)
├── pages/1_Admin_Dashboard.py  # Presenter dashboard (auto-refresh)
├── storage.py                  # add_checkin / get_checkins / reset (Sheets <-> SQLite)
├── make_qr.py                  # deployed URL -> qr.png
├── roster.csv.example          # rename to roster.csv to enable the name dropdown
├── requirements.txt
├── .streamlit/
│   ├── config.toml             # navy/teal theme
│   └── secrets.toml.example    # settings template (copy to secrets.toml)
├── CLAUDE.md                   # the original build spec
└── README.md                   # this file
```

---

## 7. Troubleshooting

- **Dashboard not updating** — it refreshes every 3s; give it a moment. Check the
  bottom caption shows the expected source.
- **"You're already checked in"** — duplicate blocking is on. Use a different name,
  or set `ALLOW_DUPLICATES = "true"` for rehearsals.
- **Sheets error** — make sure the Sheet is shared with the service-account email and
  the tab is named exactly `attendance`. If unsure, set `USE_SHEETS = "false"` to fall
  back to local storage instantly.
- **Wrong times** — set `TIMEZONE` (e.g. `Asia/Seoul`).
