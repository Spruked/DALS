import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI(title="DALS Dashboard")

# Setup templates
templates_dir = Path(__file__).parent / "iss_module" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the DALS dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "dals-dashboard"}

if __name__ == "__main__":
    print("🚀 Starting DALS Dashboard on http://127.0.0.1:8005")
    uvicorn.run(app, host="127.0.0.1", port=8005, log_level="info")