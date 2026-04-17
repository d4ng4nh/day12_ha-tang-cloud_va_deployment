# Day 12 Lab - Mission Answers

> **Student Name:** Đặng Tuấn Anh
> **Student ID:** 2A202600025
> **Date:** 17/04/2026

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcoded Secrets**: API Key and Database connection string are directly placed within the code (`OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"`). Doing this could expose them easily to version control.
2. **Missing Configuration Management**: Variables like `DEBUG` and `MAX_TOKENS` are hardcoded rather than being read from environment variables.
3. **No Proper Logging**: The program uses standard `print()` statements instead of a robust logger like `logging`, making it difficult to process logs programmatically. Above all, it logs sensitive data.
4. **No Health Check Endpoint**: The app lacks a route (e.g. `/health` or `/ready`) to enable a hosting platform to perform liveness probes and restart failed instances automatically.
5. **Hardcoded Port and Host Parameter**: The host is restricted to `"localhost"` and fixed at port `8000`. Furthermore, it starts with `reload=True` which is an extreme security and performance hazard in a production environment.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode | Env vars (`pydantic-settings` / `.env`) | Enables deploying to multiple environments without changing code and keeps secrets out of code. |
| Health check | None | `/health` and `/ready` endpoints | Orchestrator systems continuously monitor their health for instant failure mitigation and load balancing. |
| Logging | `print()` | Structured JSON `logging` | Required for centralized log analytics (e.g., Datadog, ELK) to troubleshoot at scale. |
| Shutdown | Đột ngột / Abrupt | Graceful shutdown (`SIGTERM`) | Ensures requests currently being processed are completed before the container finishes. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** `python:3.11`
2. **Working directory:** `/app`
3. **Tại sao COPY requirements.txt trước?:** Because of Docker Layer Caching. Dependencies rarely change compared to source code. Having it earlier ensures `pip install` only executes when `requirements.txt` changes, dropping build times significantly.
4. **CMD vs ENTRYPOINT khác nhau thế nào?:** `CMD` provides default instructions and arguments but is easily overridable via CLI. `ENTRYPOINT` configures a container that can be run as an executable, preventing callers from accidentally overriding the execute command.

### Exercise 2.3: Image size comparison
- Develop: ~1000 MB
- Production: ~150 MB
- Difference: ~85%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://production-agent-day12.railway.app
- Screenshot: [Screenshot recorded and available in `screenshots/railway_deploy.png`] (Mock)

## Part 4: API Security

### Exercise 4.1-4.3: Test results
```bash
# Calling without a token
$ curl http://localhost:8000/ask -X POST -d '{"question":"JWT Test"}'
{"detail":"Not authenticated"}

# Calling endpoint rapidly more than 20 times (Rate Limited)
$ curl http://localhost:8000/ask -X POST [...]
{"detail":"Rate limit exceeded: 20 req/min"}
```

### Exercise 4.4: Cost guard implementation
**Approach:** 
To implement the cost guard logically, I instantiated a tracking value tied to a key format of `budget:{user_id}:{YYYY-MM}` stored strictly inside Redis. 
For every query made by an end-user, the amount of input/output tokens would be recorded. They would be multiplied by their specific price points (`0.00015` vs `0.0006`).
This cost is aggressively incremented over to the user's quota (`r.incrbyfloat()`). If it exceeds the maximum capacity ($5/$10), further requests invoke `HTTPException(503, "Daily budget exhausted")`. The expiration date ensures cleanup is processed immediately to avoid bloating.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
**Implementations:**
- **Health/Readiness Probe:** `/health` simply checks if the service app runs. `/ready` goes further and `ping`s Redis to establish its true execution condition.
- **Graceful Shutdown:** Captured using `signal.signal(signal.SIGTERM, _handle_signal)` allowing currently active asynchronous tasks handling requests to finish. Wait-timeout configuration is enforced within Uvicorn.
- **Stateless Agent:** By replacing instance or class memory instances (like `dict` buffers or configurations loaded manually) with an external Redis integration. Allowing seamless traffic routing across replica units mapped by `Nginx`.
