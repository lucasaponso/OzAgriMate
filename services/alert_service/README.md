# Alert service (not implemented)

Container: Python / FastAPI. Evaluates telemetry against thresholds, creates alerts and sends them through the
notification provider with retries (runtime diagram A). Consumes `ReadingAccepted`; owns the Alert DB.
