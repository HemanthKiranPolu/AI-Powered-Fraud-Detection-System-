resource "aws_ecs_cluster" "this" {
  name = "${var.project_name}-cluster"
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}-api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.project_name}-worker"
  retention_in_days = 30
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.api_image != "" ? var.api_image : aws_ecr_repository.api.repository_url
      essential = true
      portMappings = [{ containerPort = 8080, hostPort = 8080 }]
      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET", value = aws_s3_bucket.docs.id },
        { name = "KMS_KEY_ARN", value = aws_kms_key.s3_kms.arn },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.main.id },
        { name = "DYNAMO_CASES_TABLE", value = aws_dynamodb_table.cases.name },
        { name = "DYNAMO_EVENTS_TABLE", value = aws_dynamodb_table.events.name },
        { name = "API_KEY_SECRET_NAME", value = var.api_key_secret_name },
        { name = "LOG_LEVEL", value = "INFO" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project_name}-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task_role.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = var.worker_image != "" ? var.worker_image : aws_ecr_repository.worker.repository_url
      essential = true
      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "S3_BUCKET", value = aws_s3_bucket.docs.id },
        { name = "KMS_KEY_ARN", value = aws_kms_key.s3_kms.arn },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.main.id },
        { name = "DYNAMO_CASES_TABLE", value = aws_dynamodb_table.cases.name },
        { name = "DYNAMO_EVENTS_TABLE", value = aws_dynamodb_table.events.name },
        { name = "RULES_PATH", value = "/app/config/rules.yaml" },
        { name = "LOG_LEVEL", value = "INFO" }
      ]
      command = ["python", "-m", "worker.main"]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

output "ecs_cluster_name" { value = aws_ecs_cluster.this.name }
output "api_task_family" { value = aws_ecs_task_definition.api.family }
output "worker_task_family" { value = aws_ecs_task_definition.worker.family }

