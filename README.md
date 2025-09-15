# AI-Powered Fraud Detection System (AWS Textract + Rekognition + Python)

This repo implements an end-to-end, production-ready fraud detection pipeline using AWS Textract, AWS Rekognition, FastAPI, S3, SQS, DynamoDB, and Terraform. It ingests ID documents, extracts structured fields, compares faces, computes fraud signals, and scores each case with configurable rules. Packaged as Docker containers and deployable to ECS Fargate.

## Directory Tree

- `app/` — FastAPI service (ingest, get case, review)
- `worker/` — SQS worker (Textract/Rekognition, features, scoring)
- `config/` — Scoring config (`rules.yaml`)
- `infra/terraform/` — Terraform IaC (S3, SQS, KMS, DynamoDB, ECS, ECR, IAM)
- `docker/` — Dockerfiles for API and Worker
- `scripts/` — Evaluation script
- `tests/` — Unit tests (MRZ, scoring)

## API Endpoints

- `POST /v1/ingest` — Upload base64 images `{doc_front_b64, doc_back_b64?, selfie_b64?, metadata?}`
- `GET /v1/case/{id}` — Retrieve case status, score, reasons
- `POST /v1/review/{id}` — Record human decision `{APPROVE|DENY|ESCALATE}`

All endpoints require header `x-api-key`.

## Security & Compliance

- S3 objects encrypted with SSE-KMS; KMS key rotates.
- DynamoDB stores scores, reasons, and references to artifacts; no raw PII.
- Logs exclude raw PII; hashes only.
- S3 lifecycle expiry for case images; set via `IMAGE_TTL_DAYS`.

## Deploy (Terraform + ECS Fargate)

Prereqs:
- AWS account and credentials with permissions for ECR, ECS, IAM, S3, SQS, DynamoDB, KMS.
- Existing VPC and private subnets (pass to Terraform).

Steps:
1) Build and push images (GitHub Actions provided) or locally.
2) `cd infra/terraform && terraform init`
3) `terraform apply -var="aws_region=us-east-1" -var="vpc_id=..." -var='private_subnet_ids=["subnet-...","subnet-..."]' -var='public_subnet_ids=["subnet-...","subnet-..."]'`

Outputs include: S3 bucket, KMS key ARN, SQS URL, DynamoDB table names, ECS cluster and task families, ECS services, and ALB DNS name, plus ECR URLs. Wire the produced ECR image URIs into the ECS task definitions via CI or `-var api_image=... -var worker_image=...`.

## Local Run (for development)

- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- Set env vars:
  - `AWS_REGION`, `S3_BUCKET`, `KMS_KEY_ARN`, `SQS_QUEUE_URL`, `DYNAMO_CASES_TABLE`, `DYNAMO_EVENTS_TABLE`, `API_KEY`.
- Start API: `make run-api`
- Start Worker: `python -m worker.main`

## Configuration

- `config/rules.yaml` — feature weights, thresholds, and explanation rules.
- Env vars:
  - `AWS_REGION` — AWS region, e.g., `us-east-1`
  - `S3_BUCKET` — S3 bucket for documents
  - `KMS_KEY_ARN` — KMS key for S3 SSE-KMS
  - `SQS_QUEUE_URL` — SQS queue URL
  - `DYNAMO_CASES_TABLE` — cases table (default `fraud_cases`)
  - `DYNAMO_EVENTS_TABLE` — events table (default `fraud_events`)
  - `API_KEY_SECRET_NAME` or `API_KEY` — API key (Secrets Manager preferred)
  - `RISKY_IPS` — comma-separated list

## Data Model

- DynamoDB `cases`: `case_id (PK)`, `status`, `fraud_score`, `reasons`, `decision`, `s3_keys`, `metadata`, `artifact_key`, `created_at`, `updated_at`.
- DynamoDB `events`: `case_id (PK)`, `ts (SK)`, `type`, `payload`, `device_hash`, `ip`, `ttl`. GSI `gsi_device` on `device_hash, ts` for velocity.

## Scoring Engine

- Features: `face_similarity`, `textract_conf_avg`, `mrz_valid`, `expiry_valid`, `template_geom_score`, `blur_score`, `glare_score`, `velocity_count_24h`, `device_hash_dup`, `field_consistency_flags`.
- Weighted sum to 0..1 fraud score. Thresholds: approve < 0.25, reject >= 0.6, else review.
- Explanations evaluated from YAML expressions.

## AWS Calls

- Textract `AnalyzeID` preferred; fallback `AnalyzeDocument`.
- Rekognition `DetectFaces` to crop document portrait; `CompareFaces` selfie vs doc face.

## Evaluation

- `scripts/eval.py --features-csv path/to/features.csv` computes confusion matrix, metrics and ROC-AUC. Provide features CSV with `is_fraud` column.

## CI/CD

- `.github/workflows/ci-cd.yml` builds images, pushes to ECR, then `terraform apply` with image tags.
- Configure `secrets.AWS_ROLE_ARN`, `secrets.AWS_REGION`, `vars.API_ECR_REPO`, `vars.WORKER_ECR_REPO`, `vars.TF_VAR_vpc_id`, `vars.TF_VAR_private_subnet_ids`, `vars.TF_VAR_public_subnet_ids`.

## Notes & Stretch

- Liveness detection, template forgery detection, and a review UI can be added.
- For Postgres on RDS, replace DynamoDB calls in `app/persistence.py` and `worker/persistence.py` with SQL equivalents; update Terraform accordingly.

## Runbook

- Metrics: CloudWatch `FraudDetection/CasesProcessed`.
- Alarms: SQS DLQ non-empty, Textract/Rekognition error rates, API 5xx.
- Dashboards: stage latencies, score distributions, auto decision rates.
