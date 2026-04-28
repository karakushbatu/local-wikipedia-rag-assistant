# Production Deployment Recommendation — WikiRAG

**Version:** 1.0  
**Date:** 2026-04-28  
**Scope:** Migration path from local Ollama + ChromaDB prototype to a production-grade, scalable deployment

---

## 1. Current Limitations of Local Deployment

| Limitation | Impact |
|---|---|
| Single-user only | Cannot serve multiple concurrent users |
| Ollama on consumer hardware | mistral:7b inference is slow (~5–30s/query) without GPU |
| ChromaDB on local disk | No replication, no backup, single point of failure |
| SQLite for tracking | Not safe for concurrent writes; single file |
| No authentication | Anyone on localhost can access all data |
| No monitoring | No visibility into query latency, error rates, or model quality |
| Manual ingestion | No scheduled re-ingestion when Wikipedia content changes |
| No caching | Identical queries re-embed and re-retrieve every time |

---

## 2. Recommended Cloud Architecture

### AWS Stack (Primary Recommendation)

```
┌──────────────────────────────────────────────────────────────┐
│                        AWS Cloud                             │
│                                                              │
│  CloudFront CDN                                              │
│      ↓                                                       │
│  ALB (Application Load Balancer)                             │
│      ↓                                                       │
│  ECS Fargate (Streamlit app — auto-scaled containers)        │
│      ├── Embedding Service (GPU-backed EC2 / Bedrock)        │
│      ├── Pinecone (managed vector DB)                        │
│      ├── RDS PostgreSQL (replaces SQLite)                    │
│      └── ElastiCache Redis (query result cache)              │
│                                                              │
│  S3 (artifact storage, ingestion logs)                       │
│  EventBridge + Lambda (scheduled re-ingestion)               │
│  CloudWatch (monitoring, alerting)                           │
└──────────────────────────────────────────────────────────────┘
```

### GCP Alternative

- Cloud Run for the Streamlit app (auto-scaling, pay-per-request)
- Vertex AI Embeddings API (text-embedding-004) — drop-in replacement for nomic-embed-text
- AlloyDB or Cloud SQL for metadata tracking
- Vertex AI Vector Search (formerly Matching Engine) for managed vector storage
- Cloud Scheduler + Cloud Functions for scheduled ingestion

---

## 3. Recommended Hosted LLM Alternatives

| Option | Latency | Cost | Privacy | Notes |
|---|---|---|---|---|
| **Anthropic Claude API (claude-sonnet-4-6)** | ~1–3s | ~$3/M tokens in | High (SOC2) | Best reasoning, strong instruction following, grounded answers |
| **OpenAI GPT-4o** | ~1–2s | ~$5/M tokens in | Medium | Strong general performance, wide ecosystem |
| **Google Gemini 1.5 Pro** | ~1–3s | ~$3.50/M tokens in | Medium | Good for factual grounding |
| **AWS Bedrock (Llama 3 70B)** | ~2–5s | ~$2.65/M tokens in | High (VPC) | Stays in your AWS account; no data leaves |
| **Azure OpenAI** | ~1–2s | Same as OpenAI | High (enterprise) | HIPAA/GDPR compliant tiers available |

**Primary recommendation:** Anthropic Claude API (`claude-sonnet-4-6`) via the Anthropic SDK. The grounded system prompt and "do not hallucinate" instruction pair especially well with Claude's instruction-following quality. Switch the `generation/llm.py` module to use `anthropic.Anthropic().messages.create()`.

---

## 4. Recommended Managed Vector Database

| Option | Highlights | Free tier | Notes |
|---|---|---|---|
| **Pinecone** | Easiest migration from ChromaDB; metadata filtering; serverless tier | 2M vectors | Direct drop-in via `pinecone-client`; cosine similarity |
| **Weaviate Cloud** | Open-source core; BM25 hybrid search; strong metadata | 14-day trial | Good for mixed keyword + semantic retrieval |
| **Qdrant Cloud** | Rust core; very fast; excellent payload filtering | 1GB free | Best performance per dollar |
| **pgvector (RDS/AlloyDB)** | SQL-native; reuse existing Postgres infra | Included in RDS | Best if already on Postgres; no new service to manage |

**Primary recommendation:** **Pinecone Serverless** for the simplest migration path. Replace `vectorstore/chroma_store.py` with a Pinecone client that uses the same function signatures — minimal changes to the rest of the codebase.

---

## 5. Scaling Considerations

### Embedding Throughput
- The current sequential embedding (one chunk at a time) will become a bottleneck at scale
- Use batch embedding APIs (Bedrock, Vertex AI, Voyage AI) that accept hundreds of texts per call
- For re-ingestion of 40 entities (~5,000 chunks), a parallel async embedder reduces time from 30 min to ~2 min

### Query Concurrency
- Deploy Streamlit as a stateless container behind a load balancer
- Move session state to Redis (using `st.session_state` backed by a Redis store or switching to a FastAPI backend + React frontend)
- Cache embedding of frequent queries in Redis with a 1-hour TTL

### Vector Store Scaling
- ChromaDB supports ~1M documents comfortably; beyond that, switch to Pinecone or Qdrant
- For a production Wikipedia RAG over all of English Wikipedia (~6.7M articles), use Qdrant's distributed mode or Pinecone's pod-based deployment

### Ingestion Pipeline
- Move to an async pipeline: `asyncio` + `aiohttp` for concurrent Wikipedia fetches
- Use a job queue (SQS + Lambda or Celery + Redis) for large-scale re-ingestion
- Store raw Wikipedia content in S3 as a cache to avoid refetching on re-embedding

---

## 6. Security Considerations

### API Keys
- Store all API keys in AWS Secrets Manager or HashiCorp Vault — never in environment files or code
- Rotate keys automatically with a 90-day policy
- Use IAM roles for service-to-service authentication within AWS (no static keys)

### Authentication & Authorization
- Add OAuth2 / SSO (Auth0, AWS Cognito, Google OAuth) in front of the Streamlit app
- For internal tools: use Streamlit's `st.experimental_user` with OIDC
- For public deployment: add rate limiting per user (API Gateway, Nginx)

### Data Privacy
- Wikipedia content is CC BY-SA licensed and can be stored in cloud without copyright issues
- User query logs should be opt-in and pseudonymized before storage
- Do not log raw user queries to CloudWatch without a data retention policy

### Network Security
- Run the Streamlit container in a private subnet; expose only via ALB with HTTPS
- Restrict Pinecone/Qdrant access to the VPC CIDR block
- Enable VPC flow logs for audit trails

---

## 7. Cost Estimation

### Small Deployment (100 users/day, 500 queries/day)

| Component | Monthly Cost |
|---|---|
| ECS Fargate (2 vCPU, 4GB, ~50% utilization) | ~$35 |
| Pinecone Serverless (40K vectors, 500 queries/day) | ~$0 (free tier) |
| Claude API (claude-sonnet-4-6, avg 2K tokens/query) | ~$3/day → ~$90 |
| Voyage AI embeddings (500 queries × 500 tokens) | ~$0.01/day → ~$0.30 |
| RDS PostgreSQL t3.micro | ~$15 |
| ElastiCache Redis t3.micro | ~$12 |
| ALB + CloudFront | ~$20 |
| **Total** | **~$175/month** |

### Medium Deployment (1,000 users/day, 5,000 queries/day)

| Component | Monthly Cost |
|---|---|
| ECS Fargate (auto-scaled, 4–8 vCPU) | ~$120 |
| Pinecone Serverless | ~$70 |
| Claude API | ~$900 |
| RDS PostgreSQL r6g.large | ~$150 |
| ElastiCache Redis cluster | ~$80 |
| ALB + CloudFront + WAF | ~$50 |
| **Total** | **~$1,370/month** |

---

## 8. Migration Path from Local to Production

### Phase 1: Containerize (Week 1)
1. Write a `Dockerfile` for the Streamlit app
2. Extract all configuration (Ollama URL, model names, DB paths) to environment variables
3. Run locally with `docker-compose` (app + Ollama + ChromaDB containers)
4. Verify all 13 example queries still work

### Phase 2: Replace Core Services (Week 2)
1. Swap `generation/llm.py` → Claude API via `anthropic` SDK
2. Swap `embeddings/embedder.py` → Voyage AI or Bedrock Titan Embeddings
3. Swap `vectorstore/chroma_store.py` → Pinecone (same function signatures)
4. Swap `database/sqlite_tracker.py` → PostgreSQL via `psycopg2` or SQLAlchemy

### Phase 3: Deploy to AWS (Week 3)
1. Push Docker image to ECR
2. Deploy ECS Fargate service with ALB
3. Configure RDS PostgreSQL and run schema migration
4. Create Pinecone index and re-run ingestion pipeline
5. Set up CloudWatch dashboards and alarms

### Phase 4: Harden & Monitor (Week 4)
1. Add Cognito authentication
2. Configure Redis caching for frequent queries
3. Set up EventBridge rule for weekly Wikipedia re-ingestion
4. Enable CloudWatch Container Insights
5. Add Datadog or Grafana for query latency tracking

---

## 9. Monitoring and Observability

### Key Metrics to Track

| Metric | Tool | Alert Threshold |
|---|---|---|
| Query p95 latency | CloudWatch / Datadog | > 10s |
| LLM API error rate | CloudWatch | > 1% |
| Embedding API error rate | CloudWatch | > 0.5% |
| Vector store query latency | Pinecone metrics | > 500ms |
| Cache hit rate | Redis metrics | < 20% (investigate) |
| Ingestion failure rate | Custom CloudWatch metric | > 5% |

### Logging Strategy
- Structured JSON logs (entity name, query type, retrieval count, latency, model used)
- Ship logs to CloudWatch Logs → S3 for long-term retention
- Index logs in OpenSearch for ad-hoc analysis
- Trace queries end-to-end with AWS X-Ray or OpenTelemetry

### Quality Monitoring
- Periodically run the 13 example queries against a golden answer set
- Alert if any answer diverges significantly (LLM-as-judge evaluation)
- Track "I don't know" rate — too high suggests retrieval is broken
