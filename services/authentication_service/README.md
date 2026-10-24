# Authentication service (not implemented)

Container: Python / FastAPI. User authentication and authorisation (ADR 06), backed by User DB.
Called by the Irrigation control service to check a user's permissions for a farm (runtime diagram B).
See `irrigation_control_service/infrastructure/authorization_client.py` for the client port.
