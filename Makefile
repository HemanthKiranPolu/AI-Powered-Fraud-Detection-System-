PROJECT?=fraud
AWS_REGION?=us-east-1

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: run-api
run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

.PHONY: run-worker
run-worker:
	python -m worker.main

.PHONY: run-local
run-local:
	(uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload &) && \
	python -m worker.main

.PHONY: docker-build
docker-build:
	docker build -f docker/api.Dockerfile -t $(PROJECT)-api:local .
	docker build -f docker/worker.Dockerfile -t $(PROJECT)-worker:local .

.PHONY: tf-init
tf-init:
	cd infra/terraform && terraform init

.PHONY: tf-apply
tf-apply:
	cd infra/terraform && terraform apply -auto-approve -var="aws_region=$(AWS_REGION)"
