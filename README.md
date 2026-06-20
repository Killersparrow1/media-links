# Media Link Manager

Free, hosted, unlimited media link manager. Browse, search, and organize your download links with TMDB metadata auto-fill.

**Stack:** GitHub Pages (frontend) + Google Sheets (database) + Apps Script (API)

## Quick Start

1. Create a Google Sheet at https://sheets.new
2. **Extensions > Apps Script** → paste `Code.gs` → Deploy > Web app (Execute as: Me, Access: Anyone)
3. Copy the Web App URL
4. Push this repo to GitHub → enable Pages from `/docs`
5. Open your live site → click **⚙️** → paste the Web App URL + (optional) TMDB API key

## Features

- Card grid with posters, badges, filters
- Bulk import (parses filename `[size]` and URL pairs)
- TMDB auto-fill for poster, overview, rating
- Search, sort, pagination
- Export/import JSON backups
- Offline mode via localStorage fallback

## Files

| File | Purpose |
|------|---------|
| `docs/index.html` | Frontend app (deployed to Pages) |
| `Code.gs` | Apps Script backend |
| `SETUP.md` | Full setup guide |

No API keys in source code — config is stored in your browser.
