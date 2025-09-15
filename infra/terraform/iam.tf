data "aws_iam_policy_document" "task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals { type = "service" identifiers = ["ecs-tasks.amazonaws.com"] }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${var.project_name}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
}

resource "aws_iam_role_policy_attachment" "task_exec_attach" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task_role" {
  name               = "${var.project_name}-task-role"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
}

data "aws_iam_policy_document" "task_policy" {
  statement {
    sid     = "S3Access"
    actions = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
    resources = [
      aws_s3_bucket.docs.arn,
      "${aws_s3_bucket.docs.arn}/*",
    ]
  }
  statement {
    sid     = "KMSUse"
    actions = ["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey*", "kms:DescribeKey"]
    resources = [aws_kms_key.s3_kms.arn]
  }
  statement {
    sid     = "SQS"
    actions = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.main.arn]
  }
  statement {
    sid     = "Dynamo"
    actions = ["dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:GetItem", "dynamodb:Query"]
    resources = [
      aws_dynamodb_table.cases.arn,
      aws_dynamodb_table.events.arn,
      "${aws_dynamodb_table.events.arn}/index/*"
    ]
  }
  statement {
    sid     = "Textract"
    actions = ["textract:AnalyzeDocument", "textract:AnalyzeID"]
    resources = ["*"]
  }
  statement {
    sid     = "Rekognition"
    actions = ["rekognition:DetectFaces", "rekognition:CompareFaces"]
    resources = ["*"]
  }
  statement {
    sid     = "Secrets"
    actions = ["secretsmanager:GetSecretValue"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "secretsmanager:SecretId"
      values   = [var.api_key_secret_name]
    }
  }
  statement {
    sid     = "CloudWatchMetrics"
    actions = ["cloudwatch:PutMetricData"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "task_policy" {
  name   = "${var.project_name}-task-policy"
  policy = data.aws_iam_policy_document.task_policy.json
}

resource "aws_iam_role_policy_attachment" "task_role_attach" {
  role       = aws_iam_role.task_role.name
  policy_arn = aws_iam_policy.task_policy.arn
}

output "task_role_arn" { value = aws_iam_role.task_role.arn }
output "task_execution_role_arn" { value = aws_iam_role.task_execution.arn }

