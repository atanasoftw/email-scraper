# 📧 Email Scraper for Roundcube Webmail

This Python app automates the process of scraping **name**, **phone number**, and **email** from messages in a Roundcube Webmail inbox.

It logs into your mailbox, cycles through emails containing a specific keyword (e.g., `Giftlab`), extracts the necessary details, and saves them into `.xlsx` files — one for each page of results.

---

## 🚀 Features

- ✅ Selenium-powered automation
- ✅ Extracts structured customer data
- ✅ Auto-pagination across inbox
- ✅ Saves output in `.xlsx` format
- ✅ Easy to run in a container

---

## 🛠 Requirements

- Roundcube Webmail access
- Docker installed
- A valid Roundcube login (email + password)

---

## ⚙️ Setup

1. **Clone or download this repo** to your machine.
2. **Edit environment variables** in `scraper.py`:
   ```python
   EMAIL = "your-email@example.com"
   PASSWORD = "your-password"
   ROUNDCUBE_URL = "https://your-roundcube-url.com/"
