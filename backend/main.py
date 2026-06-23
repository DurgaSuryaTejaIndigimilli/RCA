"""
Main FastAPI application for AI Root Cause Analyzer
"""
import os
import json
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from core.rca_generator import RCAGenerator
from data.sample_logs import SAMPLE_INCIDENT_LOGS, SAMPLE_DEMO_LOGS
from data.historical_incidents import HISTORICAL_INCIDENTS

load_dotenv()

app = FastAPI(
    title="AI Root Cause Analyzer",
    description="AI-powered incident root cause analysis for distributed systems",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the RCA generator
rca_generator = RCAGenerator()


# ==================== Request/Response Models ====================

class LogAnalysisRequest(BaseModel):
    logs: str
    query: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None
    analysis_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    analysis_id: str
    rating: int  # 1-5
    feedback: Optional[str] = None
    rca_accurate: bool = True
    fix_helpful: bool = True


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "name": "AI Root Cause Analyzer",
        "version": "1.0.0",
        "status": "operational",
        "llm_provider": os.getenv('LLM_PROVIDER', 'mock'),
        "endpoints": {
            "analyze": "POST /api/analyze",
            "chat": "POST /api/chat",
            "demo": "GET /api/demo",
            "demo_scenarios": "GET /api/demo/scenarios",
            "feedback": "POST /api/feedback",
            "health": "GET /api/health"
        }
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "log_parser": "operational",
            "anomaly_detector": "operational",
            "correlation_engine": "operational",
            "rag_engine": "operational",
            "llm_client": os.getenv('LLM_PROVIDER', 'mock')
        }
    }


@app.post("/api/analyze")
async def analyze_logs(request: LogAnalysisRequest):
    """
    Analyze logs and generate Root Cause Analysis.
    """
    try:
        if not request.logs or not request.logs.strip():
            raise HTTPException(status_code=400, detail="No logs provided")

        result = rca_generator.analyze(request.logs, request.query)

        # Add analysis ID for feedback tracking
        result['analysis_id'] = f"ana_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result['timestamp'] = datetime.now().isoformat()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Interactive chat about incident analysis.
    """
    try:
        response = rca_generator.chat(request.message, request.context)
        return {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/api/demo")
async def run_demo():
    """
    Run a demo analysis with sample incident data.
    """
    try:
        result = rca_generator.analyze(SAMPLE_DEMO_LOGS)
        result['analysis_id'] = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result['timestamp'] = datetime.now().isoformat()
        result['demo'] = True
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


@app.get("/api/demo/scenarios")
async def get_demo_scenarios():
    """
    Get all available demo scenarios.
    """
    return {
        "scenarios": [
            {
                "id": "db_pool_exhaustion",
                "title": "Database Connection Pool Exhaustion",
                "description": "API response time spike caused by DB pool exhaustion after deployment",
                "severity": "high",
                "logs": SAMPLE_DEMO_LOGS
            },
            {
                "id": "iot_device_fleet",
                "title": "IoT Device Fleet Outage",
                "description": "Massive device disconnection due to MQTT broker failure",
                "severity": "critical",
                "logs": SAMPLE_INCIDENT_LOGS
            }
        ]
    }


@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback on analysis quality for model improvement.
    """
    # In production, this would store in a database for model retraining
    feedback_entry = {
        "analysis_id": request.analysis_id,
        "rating": request.rating,
        "feedback": request.feedback,
        "rca_accurate": request.rca_accurate,
        "fix_helpful": request.fix_helpful,
        "timestamp": datetime.now().isoformat()
    }

    # Store to file (in production, use proper DB)
    feedback_file = "feedback_store.jsonl"
    with open(feedback_file, "a") as f:
        f.write(json.dumps(feedback_entry) + "\n")

    return {
        "status": "received",
        "message": "Thank you for your feedback! This helps improve our model."
    }


@app.get("/api/historical-incidents")
async def get_historical_incidents():
    """Get historical incident patterns for reference."""
    return {"incidents": HISTORICAL_INCIDENTS}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)