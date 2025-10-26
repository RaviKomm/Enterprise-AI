from fastapi import FastAPI, Request, Header, HTTPException, Response
from pydantic import BaseModel, conint
import time, os, logging, uuid, asyncio, random
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine import create_engine
from pythonjsonlogger import jsonlogger

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger("api")
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(LOG_LEVEL)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai_user:ai_pass@postgres:5432/ai_audit")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

REQUEST_COUNTER = Counter("ai_requests_total", "Total AI requests", ["outcome"])
REQUEST_LATENCY = Histogram("ai_request_duration_seconds", "Request latency seconds", buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2, 5))

app = FastAPI()

class InferRequest(BaseModel):
    prompt: str
    max_tokens: conint(gt=0, le=1024) = 128

def redact_payload(payload: dict) -> dict:
    redacted = payload.copy()
    if "prompt" in redacted:
        redacted["prompt"] = "[REDACTED]"
    return redacted

@app.on_event("startup")
def on_startup():
    with engine.begin() as conn:
        conn.execute(text("""CREATE TABLE IF NOT EXISTS audit (
            id SERIAL PRIMARY KEY,
            req_id TEXT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            length INT,
            duration_ms INT,
            outcome TEXT
        )"""))

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        raise HTTPException(status_code=503, detail="DB unreachable")

@app.post("/infer")
async def infer(req: InferRequest, request: Request, x_request_id: str | None = Header(None)):
    start = time.time()
    req_id = x_request_id or str(uuid.uuid4())
    payload = {"prompt": req.prompt, "max_tokens": req.max_tokens}
    logger.info("receive_infer", extra={"req_id": req_id, "payload": redact_payload(payload)})

    try:
        with REQUEST_LATENCY.time():
            await _simulate_inference(req.prompt, req.max_tokens)
        outcome = "success"
        REQUEST_COUNTER.labels(outcome=outcome).inc()
    except Exception as e:
        outcome = "error"
        REQUEST_COUNTER.labels(outcome=outcome).inc()
        logger.exception("inference_error", extra={"req_id": req_id})
        raise HTTPException(status_code=500, detail="inference failed")
    finally:
        duration_ms = int((time.time() - start) * 1000)
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO audit (req_id, length, duration_ms, outcome) VALUES (:r, :l, :d, :o)"),
                             {"r": req_id, "l": len(req.prompt), "d": duration_ms, "o": outcome})
        except Exception:
            logger.exception("audit_write_fail", extra={"req_id": req_id})

    logger.info("respond_infer", extra={"req_id": req_id, "duration_ms": duration_ms, "outcome": outcome})
    return {"req_id": req_id, "duration_ms": duration_ms, "result": "[SIMULATED]"}

async def _simulate_inference(prompt, max_tokens):
    base = random.uniform(0.02, 0.15)
    if "spike" in prompt:
        await asyncio.sleep(random.uniform(0.8, 1.5))
    else:
        await asyncio.sleep(base)

@app.get("/metrics")
def metrics():
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)
