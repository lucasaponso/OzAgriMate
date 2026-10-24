Not implemented. Each implemented service uses an in-memory repository in place of its database:

| Service | Database (deployment view) | In-memory stand-in |
|---|---|---|
| Farm management | Farm DB | infrastructure/farm_repository.py |
| Telemetry | Telemetry DB | infrastructure/reading_repository.py |
| Irrigation control | Command DB | infrastructure/command_repository.py |
