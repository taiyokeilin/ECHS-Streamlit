# ⚾ Pitcher Metrics Dashboard — Setup Guide

## 1. Install dependencies
```bash
pip install streamlit pandas gspread google-auth
```

## 2. Run locally (CSV mode)
Place `lev_test.csv` in the same folder as `pitcher_dashboard.py`, then:
```bash
streamlit run pitcher_dashboard.py
```

## 3. Connect to Google Sheets

### a) Create a Google Cloud service account
1. Go to https://console.cloud.google.com → **APIs & Services → Credentials**
2. Create a **Service Account**, download the JSON key file
3. Enable the **Google Sheets API** and **Google Drive API** in your project

### b) Share your sheet
- Open your Google Sheet → Share → paste the service account email (ends in `@...iam.gserviceaccount.com`)
- Give it **Viewer** (read-only) or **Editor** access

### c) Add credentials to Streamlit secrets
Create `.streamlit/secrets.toml` in your project folder:
```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```
(Copy values directly from your downloaded JSON key file)

### d) Activate the Google Sheets loader
In `pitcher_dashboard.py`, uncomment the `gspread` block near the top and replace:
```python
SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"
```
with the ID from your sheet's URL:
`https://docs.google.com/spreadsheets/d/THIS_PART_HERE/edit`

Then comment out (or delete) the local CSV `load_data()` function below it.

## 4. Deploy to Streamlit Community Cloud (free, shareable link)
1. Push your project to a **GitHub repo** (include `requirements.txt` and `.streamlit/secrets.toml` — add secrets via the Streamlit Cloud dashboard, not the repo)
2. Go to https://share.streamlit.io → **New app** → point to your repo & `pitcher_dashboard.py`
3. Add your `gcp_service_account` secrets in the Streamlit Cloud **Secrets** settings
4. Share the generated URL with anyone on your staff

## requirements.txt
```
streamlit
pandas
gspread
google-auth
```
