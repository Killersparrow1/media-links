# Media Link Manager — Setup Guide

Free, hosted, unlimited media link manager using Google Sheets + GitHub Pages.

## Architecture

```
GitHub Pages ──fetch()──► Google Apps Script ──► Google Sheets
(frontend)                  (API backend)        (database)
```

## Step 1: Create the Google Sheet

1. Go to https://sheets.new
2. Rename the sheet to `Media Link Manager`
3. You don't need to create columns manually — the Apps Script will do it automatically

## Step 2: Deploy the Apps Script Backend

1. In your Google Sheet, go to **Extensions > Apps Script**
2. Delete any placeholder code
3. Paste the entire contents of `Code.gs` into the editor
4. Click **Save** (💾 icon)
5. Click **Deploy > New deployment**
6. Set:
   - **Type:** Web app
   - **Description:** `Media Link Manager API` (or anything you like)
   - **Execute as:** Me
   - **Who has access:** Anyone
7. Click **Deploy**
8. **Copy the Web App URL** — you'll need it in the next step

> ⚠️ If you see "Anyone with link" instead of "Anyone", choose that — same thing.
> On first deploy, you may need to **Review permissions** and approve access to your own Google Sheet.

## Step 3: Deploy to GitHub Pages

1. Create a GitHub repository (e.g. `media-links`)
2. Push the files:

```
your-repo/
├── docs/
│   └── index.html
├── Code.gs
└── SETUP.md
```

3. Go to your repo **Settings > Pages**
4. Under **Branch**, select `main` and folder `/docs`
5. Click **Save**
6. Your site will be live at: `https://yourusername.github.io/media-links`

## Step 4: Configure In Browser

1. Open your live GitHub Pages site
2. Click **⚙️** (Settings) button in the header
3. Paste your Apps Script Web App URL
4. (Optional) Paste your free TMDB API key (get one at themoviedb.org)
5. Click **Save**

Config is stored in your browser's localStorage — not in source code. Safe for public repos.

## Usage

- **Add Link** — Manually enter title, URL, and metadata
- **TMDB Auto-Fill** — Search TMDB by title to auto-populate poster, overview, year, rating
- **Bulk Import** — Paste filename/URL pairs to parse metadata automatically
- **Search & Filter** — Filter by resolution, codec, or search by title
- **Export/Import** — Backup or restore your links as JSON files
- **Offline Mode** — Works from localStorage if the Apps Script API isn't available

## Import Format

```
Movie.Name.2026.1080p.WEB-DL.H.265.DDP5.1-GROUP.mkv [4.39 GB]
https://example.com/file
```

You can paste either:
- `filename [size] URL` on one line, or
- `filename` on one line and `URL` on the next

## Free Resources Used

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| GitHub Pages | Frontend hosting | Unlimited bandwidth, free forever |
| Google Sheets | Database | 15GB, free forever |
| Apps Script | API backend | 20k URL fetch calls/day, free |
| TMDB | Movie metadata | Unlimited API requests (free key) |

## License

MIT
