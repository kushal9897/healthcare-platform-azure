# ADR-003: Event-Driven Architecture with Azure Service Bus

## Status
**Accepted**  -  2024-02-01

## Context
The healthcare platform needs asynchronous communication between microservices for:
- Decoupled service interactions (patient-service <-> clinical-service <-> notification-service)
- Reliable message delivery (assessments, alerts must not be lost)
- Event sourcing for audit trail (HIPAA)
- Scaling services independently based on workload

## Decision
Use **Azure Service Bus** as the event mesh between microservices.

## Rationale
- **Reliability**: At-least-once delivery with dead-letter queues
- **Ordering**: Session-based FIFO ordering for patient events
- **Azure native**: Managed service, no operational overhead
- **HIPAA compliant**: Encryption at rest/transit, Azure AD auth
- **Dead-letter queue**: Failed messages are preserved for investigation
- **Topics + Subscriptions**: Fan-out pattern for multiple consumers

## Event Flow
```
patient-service -> [patient.created] -> Service Bus Topic
                                         |-- clinical-service (trigger assessment)
                                         |-- notification-service (send welcome)
                                         +-- analytics-service (update metrics)

clinical-service -> [assessment.completed] -> Service Bus Topic
                                              |-- notification-service (send results)
                                              +-- analytics-service (track outcomes)
```

## Consequences
- Eventual consistency between services (not immediately consistent)
- Need to handle duplicate messages (idempotent consumers)
- Dead-letter queue monitoring required
- Service Bus cost (~$0.05 per million operations)
