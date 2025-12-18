# ScienceWizard Web Frontend

**Status:** Phase I Complete - Awaiting stakeholder feedback from Omri and Bar

**Live URL:** https://sciencewizard.onrender.com (free tier - 15-30s cold start after inactivity)

**GitHub:** https://github.com/mastervb99/sciencewizard-web

## Current State (December 2025)

Phase I static mockup deployed. Shows visual design only - no backend functionality.

### What's Live
- Landing page with upload UI mockup
- Login/signup form appearance (non-functional)
- Feature cards (Manuscripts, Stats, Figures, Export)
- About page with founder bios (Omri CEO, Vafa CTO)

### What's NOT Implemented Yet
- Actual file uploads
- Authentication
- Report generation
- Downloads
- Section-by-section review flow

## How to Modify

### Quick Edits (HTML/CSS only)
```bash
cd /Users/vafabayat/Dropbox/Financial/0ScienceWizard/sciencewizard_web

# Edit files
# - static/index.html     → Landing page
# - static/about.html     → About/founders page
# - static/css/style.css  → All styling
# - static/js/app.js      → Basic interactions

# Test locally
source venv/bin/activate
python server.py
# Visit http://localhost:8000

# Deploy
git add -A && git commit -m "Description of changes" && git push
# Render auto-deploys from GitHub (1-2 min)
```

### Adding New Pages
1. Create `static/newpage.html`
2. Add route in `server.py`:
   ```python
   @app.get("/newpage.html")
   async def newpage():
       return FileResponse(STATIC_DIR / "newpage.html")
   ```
3. Commit and push

## Project Structure

```
sciencewizard_web/
├── server.py              # FastAPI server
├── render.yaml            # Render deployment config
├── requirements.txt       # fastapi, uvicorn
├── .gitignore
├── README.md              # This file
├── venv/                  # Local virtual environment (not in git)
└── static/
    ├── index.html         # Landing page
    ├── about.html         # Founders page
    ├── css/
    │   └── style.css      # All styles (~700 lines)
    └── js/
        └── app.js         # Tab switching, drag/drop visuals
```

## Deployment Details

### Render Configuration
- **Service:** Web Service (Python)
- **Plan:** Free ($0/month)
- **Build:** `pip install -r requirements.txt`
- **Start:** `python server.py`
- **Auto-deploy:** Yes, from GitHub main branch

### Free Tier Limitations
- Spins down after 15 min inactivity
- Cold start: 15-30 seconds
- 512MB RAM, 0.1 CPU
- For demos: warn users about initial load time
- Upgrade to Starter ($7/mo) for always-on

## Next Steps (Pending Feedback)

### Phase II: Authentication
- Add `/api/auth/register` and `/api/auth/login` endpoints
- JWT token handling
- User session persistence

### Phase III: File Upload
- Actual file upload to server
- File validation (type, size)
- Temporary storage

### Phase IV: Report Generation
- Connect to ScienceWizard agents
- Background job processing
- Progress polling

### Phase V: Review Flow
- Section-by-section approval (per Omri's design)
- Feedback collection
- Regeneration with feedback

## Key Contacts

- **Omri Weisman** (CEO) - Product/design decisions
- **Bar** - Stakeholder feedback
- **Vafa Bayat** (CTO) - Technical implementation

## Related Documents

- `/Users/vafabayat/Dropbox/Financial/0ScienceWizard/ScienceWizard_Web_Deployment_Plan.md` - Full architecture plan
- `/Users/vafabayat/Dropbox/Financial/0ScienceWizard/Startup design Omri.docx` - Original UI spec from Omri
- `/Users/vafabayat/Dropbox/Financial/0ScienceWizard/Presentations/` - Preseed deck and materials
