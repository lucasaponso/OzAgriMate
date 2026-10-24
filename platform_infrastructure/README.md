# Platform infrastructure containers (not implemented, brief Note 4)

Kept here so the repository mirrors the deployment view.

- `api_gateway/`: Nginx. Authenticates requests and routes `/api/v1/*` to the services (behind the AWS ALB).
- `messaging/mqtt_broker/`: AWS IoT Core. Secure MQTT endpoint for farm gateways (readings in, irrigation commands out).
- `messaging/event_broker/`: RabbitMQ (HA), AMQP. Durable event messaging between services.
- `databases/`: Amazon RDS PostgreSQL. One database per service (ADR 07).
