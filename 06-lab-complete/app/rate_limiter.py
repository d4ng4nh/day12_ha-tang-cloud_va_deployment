import time
import redis
from fastapi import HTTPException
from app.config import settings

if settings.redis_url:
    r = redis.from_url(settings.redis_url)
else:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def check_rate_limit(user_id: str):
    now = time.time()
    key = f"rate_limit:{user_id}"
    
    try:
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, '-inf', now - 60)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, 60)
        results = pipe.execute()
        
        request_count = results[2]
        
        if request_count > settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
                headers={"Retry-After": "60"},
            )
    except redis.exceptions.ConnectionError:
        # Fallback logic if redis is not available in development
        pass
