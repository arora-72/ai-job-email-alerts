# AI Job Email Alerts

Public repo name: `AI-job-email-alerts`

If you do not understand something, you can ask Claude, Codex, or whatever other vibe-coding tool you use to help you set this up in less than 10 minutes.

I hate looking for jobs, so I automated it.

This is a simple and free way to create your own system that emails you about jobs or internships.

This project helps you find jobs, score them, save them to Google Sheets, and email yourself a simple digest.

## What It Does

It does 4 small things:

1. looks for jobs
2. keeps the good ones
3. saves them to a Google Sheet
4. emails you the list

## Before You Start

You need:

- Python 3.12
- a Google Sheet
- a Google service account JSON file
- an email account that can send SMTP mail
- an OpenAI API key if you want AI scoring (uses GPT-4o-mini)

## Super Simple Setup

### 1. Download the project

```bash
git clone https://github.com/YOUR-USERNAME/AI-job-email-alerts.git
cd AI-job-email-alerts
```

### 2. Make a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the packages

```bash
pip install -r requirements.txt
```

### 4. Add your Google key

Make a folder called `keys`.

Put your Google service account file here:

```text
keys/google-credentials.json
```

### 5. Fill in your profile notes

Copy the example template and fill it in with your own details:

```bash
cp docs/profile_notes.example.md docs/profile_notes.md
```

Then edit `docs/profile_notes.md` and add:

- your target roles
- your preferred cities
- keywords you want to match
- keywords you want to avoid
- a few resume highlights so the AI understands your background

This file is gitignored and will never be committed.

### 6. Make a Google Sheet

Create a Google Sheet and copy its URL.

The bot will use these columns:

- Company Name
- Date applied
- Role Name
- Location
- Job Application Link
- LinkedIn Link 1
- LinkedIn Link 2
- LinkedIn Link 3
- AI Fit Score
- AI Reason

### 7. Add your secrets

Copy the example file:

```bash
cp .env.example .env
```

Then put your real values inside `.env`:

```bash
GOOGLE_SHEETS_URL="YOUR_GOOGLE_SHEET_URL"
GOOGLE_SHEET_TAB="Email Jobs"
RECRUITING_BOT_EMAIL_TO="you@example.com"
RECRUITING_BOT_EMAIL_FROM="you@example.com"
RECRUITING_BOT_SMTP_HOST="smtp.gmail.com"
RECRUITING_BOT_SMTP_PORT="587"
RECRUITING_BOT_SMTP_USERNAME="you@example.com"
RECRUITING_BOT_SMTP_PASSWORD="your-app-password"
RECRUITING_BOT_SMTP_USE_TLS="true"
OPENAI_API_KEY="your-openai-api-key"
```

## Run It

### Job sources

Use `--source` to control where jobs come from:

```bash
# JobSpy only — searches LinkedIn, Indeed, Google (default)
python3 bot.py --source jobspy --max-jobs 12 --sheets-url "YOUR_GOOGLE_SHEET_URL"

# Greenhouse only — hits target company boards directly via the Greenhouse API
python3 bot.py --source greenhouse --max-jobs 12 --sheets-url "YOUR_GOOGLE_SHEET_URL"

# Both at once
python3 bot.py --source both --max-jobs 12 --sheets-url "YOUR_GOOGLE_SHEET_URL"
```

Omitting `--source` defaults to `jobspy`.

### Full example

```bash
python3 bot.py --source both --max-jobs 12 --max-jobs-per-day 8 --hours-old 24 --sheets-url "YOUR_GOOGLE_SHEET_URL"
```

### Send a digest email

```bash
python3 bot.py --send-sheet-digest --sheets-url "YOUR_GOOGLE_SHEET_URL" --sheets-tab "Email Jobs"
```

### Send a test email

```bash
python3 bot.py --send-test-email --email-to you@example.com
```

## Greenhouse Setup

The Greenhouse source hits each company's public job board API directly — no scraping, no rate limits.

To add or change target companies, edit `GREENHOUSE_COMPANIES` in `app/config.py`:

```python
GREENHOUSE_COMPANIES = {
    "Databricks": "databricks",
    "Stripe": "stripe",
    # add more: "Company Name": "slug"
}
```

The slug is the short ID in the company's Greenhouse URL. For example, `https://boards.greenhouse.io/databricks` has slug `databricks`. You can verify any slug by visiting `boards.greenhouse.io/SLUG` in your browser.

## Make It Yours

If you want different jobs, edit `app/config.py`.

New runs default to `8` jobs per day. You can lower or raise that with `--max-jobs-per-day` or by changing `MAX_JOBS_PER_DAY`.

You can change:

- job titles
- cities
- filters
- scoring rules

## Put It On GitHub

1. Create a new repo called `AI-job-email-alerts`.
2. Push this code there.
3. Add your GitHub Actions secrets.
4. Keep it private or make it public if you want to share it.

More setup help is in `docs/cloud_setup.md`.

## Open Source

This repo is now set up to be shared publicly:

- personal resume removed
- personal profile replaced with a template
- private sheet link removed
- simple MIT license added
