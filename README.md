# ScienceWizard Web Frontend

Phase I static frontend for ScienceWizard - appearance mockup for stakeholder review.

## Phase I Scope

This deployment shows the visual design only. No backend functionality is implemented.

**What works:**
- Landing page with upload UI mockup
- Login/signup form appearance
- Feature cards display
- Basic interactions (tab switching, button clicks show alerts)

**What does NOT work (Phase II):**
- Actual file uploads
- Authentication
- Report generation
- Downloads

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python server.py

# Visit http://localhost:8000
```

## Deploy to Render

1. Push this folder to a GitHub repository
2. Go to render.com and create a New Web Service
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml` configuration
5. Click Deploy

**Note:** Free tier has 15-30 second cold starts after inactivity.

## Project Structure

```
sciencewizard_web/
├── server.py           # FastAPI server (minimal)
├── render.yaml         # Render deployment config
├── requirements.txt    # Python dependencies
├── .gitignore
├── README.md
└── static/
    ├── index.html      # Landing page
    ├── css/
    │   └── style.css   # All styles
    └── js/
        └── app.js      # Basic interactions
```

## Next Phases

**Phase II:** Add authentication endpoints, file upload handling
**Phase III:** Connect to ScienceWizard agents for report generation
**Phase IV:** Section review and regeneration workflow
**Phase V:** Token tracking and billing integration

## Contact

PlanetMed Clinical Research Consultancy
omri@planetmed.pro
