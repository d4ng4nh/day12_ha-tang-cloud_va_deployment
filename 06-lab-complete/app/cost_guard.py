import time
import redis
from fastapi import HTTPException
from app.config import settings

if settings.redis_url:
    r = redis.from_url(settings.redis_url)
else:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = time.strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    try:
        current = float(r.get(key) or 0)
        if current + estimated_cost > settings.daily_budget_usd:
            raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")
        
        r.incrbyfloat(key, estimated_cost)
        r.expire(key, 32 * 24 * 3600)  # 32 days
        return True
    except redis.exceptions.ConnectionError:
        # Fallback if redis is not available
        return True

def get_budget_used(user_id: str) -> float:
    month_key = time.strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    try:
        return float(r.get(key) or 0)
    except redis.exceptions.ConnectionError:
        return 0.0
