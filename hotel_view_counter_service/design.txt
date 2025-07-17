# Hotel View Counter Service – System Design

## Overview

Design a scalable and fault-tolerant counter service that tracks the number of views per hotel. This service will be integrated into a high-traffic application (like Booking.com), where hotels are viewed frequently across different platforms and by different users.

Key goals:

* Accurate enough counters with eventual consistency.
* Real-time updates not strictly necessary, but visible after a few seconds.
* Support high QPS for view tracking.
* Handle regional failovers and disaster recovery.
* Optimize for read-heavy patterns with aggregation capabilities.

---

## Requirements

### Functional Requirements

* Record a hotel view event (`incrementCounter(hotel_id)`).
* Retrieve current hotel view count (`getViewCount(hotel_id)`).
* Support fetching view counts for multiple hotels in batch.

### Non-functional Requirements

* Highly available and eventually consistent.
* Scalable for millions of views per day.
* Low write latency.
* Approximate counters are acceptable for real-time reads.
* Stronger consistency for offline analytics.

---

## High-Level Architecture

```plaintext
Client → API Gateway → Write Path:
                             → Redis (local bucketed counter)
                             → Kafka Topic (async replication)
                             → RDS / DWH (periodic consolidation)

              Read Path:
                             → Redis for near real-time counts
                             → Fallback to RDS for exact counts
```

---

## Detailed Component Walkthrough

### 1. **API Layer**

* Stateless service exposing REST endpoints.
* Performs basic validation and forwards requests to backend components.

### 2. **Redis (Bucketed Counter Layer)**

* **Purpose**: To absorb high QPS writes quickly with minimal latency.
* Use time-bucketed keys: `hotel:{hotel_id}:views:{bucket_id}`.
* TTL on keys to avoid unbounded growth (e.g. 3 months).
* Sharded across multiple Redis instances (e.g. using Redis Cluster).

**Pros**:

* O(1) write latency.
* Easily horizontally scalable.
* Good for approximate real-time reads.

**Cons**:

* Data is eventually consistent.
* View counts may be stale or reset if Redis fails.

### 3. **Kafka (Write Log)**

* Every increment event is pushed into Kafka topic `hotel_view_events`.
* Kafka guarantees ordered, durable, replayable logs.
* Consumers process and batch insert into RDS/Data Warehouse.

**Pros**:

* Durable and persistent.
* Enables decoupling between ingest and storage.
* Good for downstream analytics or backup systems.

**Cons**:

* Adds operational complexity.
* Processing delay depends on consumer throughput.

### 4. **RDS / OLAP Data Store**

* Stores the canonical, exact hotel view counts.
* Updated periodically from Kafka events (via Flink/Spark consumers).
* Used for offline analytics and reports.

**Tradeoffs**:

* Strong consistency, but higher latency.
* Not used for real-time display due to latency.

---

## View Count Aggregation

* A scheduled job merges Redis bucketed keys into a single total count.
* This merged value can be pushed to RDS.
* Periodic cleanup of old keys to control Redis memory usage.

---

## Failure Modes & Disaster Recovery

### Redis Failure

* Impact: Real-time reads/writes are affected.
* Mitigation:

  * Fallback to Kafka + RDS counts (slightly stale).
  * Redis replication (Redis Sentinel or Cluster).

### Kafka Outage

* Impact: Writes can still go to Redis; async propagation paused.
* Mitigation:

  * Kafka retries and high replication factor.
  * Back-pressure mechanisms in API.

### RDS Failure

* Impact: Historical data aggregation paused.
* Mitigation:

  * RDS replicas in other AZs.
  * Periodic backups and cross-region replication.

### Region-Level Failure

* Multi-region deployment using global DNS.
* Redis deployed in each region for local low-latency access.
* Kafka with cross-region mirror topics (MirrorMaker 2).
* Asynchronous replication of view data across regions.

---

## Monitoring & Alerting

* Redis: Key eviction rate, memory pressure, replication lag.
* Kafka: Consumer lag, topic size, unacknowledged messages.
* RDS: Write latency, replication lag.
* API: QPS, 5xx rate, p95 latency.
* Alert if:

  * Redis memory usage > 80%.
  * Kafka consumer lag > threshold.
  * View API latency > SLA.

---

## Optimizations and Future Enhancements

* Move to a columnar store (e.g. BigQuery/ClickHouse) for analytics.
* Use probabilistic counters (HyperLogLog) for certain views.
* Batch view events client-side to reduce API calls.
* Support additional dimensions: views by country, device type.

---

## Tradeoffs Summary

| Option                  | Pros                                | Cons                                      |
| ----------------------- | ----------------------------------- | ----------------------------------------- |
| Redis Bucketed Counters | Low latency, scalable, region-local | Eventually consistent, data loss possible |
| Kafka                   | Durable, async processing           | Delay in processing, ops overhead         |
| RDS / OLAP Store        | Accurate, long-term storage         | High latency, not real-time               |
| Batched Aggregation     | Memory-efficient                    | May miss very recent events               |

---

## Sample API Contract

### `POST /views`

```json
{
  "hotel_id": "hotel_987"
}
```

### `GET /views?hotel_id=hotel_987`

```json
{
  "hotel_id": "hotel_987",
  "view_count": 10342
}
```

---

Let me know if you'd like an architectural diagram or markdown formatting for GitHub!
