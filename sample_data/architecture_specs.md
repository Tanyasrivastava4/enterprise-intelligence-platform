# Enterprise Cloud Architecture Specification v3.4

## 1. Core Microservices Topology
The enterprise platform operates on a distributed microservices topology deployed across multi-zone Kubernetes clusters:
- **Authentication Service (AuthService):** Handles user session verification, JWT signing, and RBAC policies. Listens on port `8080`.
- **Primary Relational Database:** Managed PostgreSQL 16 cluster configured for high-availability multi-region replication. Listens on port `5432`.
- **In-Memory Cache Cluster:** Distributed Redis cluster for session caching and rate-limiting counters. Listens on port `6379`.
- **Document Processing Worker:** Asynchronous Celery worker pool processing PDF and CSV extractions.

## 2. Scalability Limits and Thresholds
- **Maximum API Latency Budget:** 250ms for P95 read queries.
- **Database Connection Pool:** Allocated with a strict maximum of 120 concurrent connections per cluster pod.
- **Rate Limiting:** Enforces a hard limit of 500 requests per minute per IP address before issuing HTTP 429 Too Many Requests.
- **Failover SLA:** In case of master database degradation, automated failover to the hot standby replica completes within 28 seconds.
