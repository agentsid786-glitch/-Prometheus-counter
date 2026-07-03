import time
import uuid
from collections import deque
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()

# Enable CORS for the grader
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Global State & Observability
START_TIME = time.time()
REQUEST_COUNTER = Counter("http_requests_total", "Total HTTP requests")
# Keep the last 1000 logs in memory
request_logs = deque(maxlen=1000)

# 2. Middleware to track metrics and logs for EVERY request
@app.middleware("http")
async def instrumentation_middleware(request: Request, call_next):
    # Get or generate a Request ID
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # Create the structured JSON log entry
    log_entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": req_id
    }
    request_logs.append(log_entry)
    
    # Increment the Prometheus counter
    REQUEST_COUNTER.inc()

    # Process the request
    response = await call_next(request)
    
    # Return the request ID in headers
    response.headers["X-Request-ID"] = req_id
    return response

# ==========================================
# Endpoints
# ==========================================

@app.get("/work")
async def do_work(n: int = 0):
    return {
        "email": "22ds2000150@ds.study.iitm.ac.in",
        "done": n
    }

@app.get("/metrics")
async def get_metrics():
    # Return Prometheus metrics in standard text format
    return Response(
        content=generate_latest(), 
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/healthz")
async def health_check():
    # Return uptime in seconds
    return {
        "status": "ok",
        "uptime_s": time.time() - START_TIME
    }

@app.get("/logs/tail")
async def tail_logs(limit: int = 10):
    # Return the last N logs (most recent at the end)
    return list(request_logs)[-limit:]
