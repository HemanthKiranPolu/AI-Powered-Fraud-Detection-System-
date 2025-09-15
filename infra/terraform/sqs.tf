resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-dlq"
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "main" {
  name                      = "${var.project_name}-queue"
  message_retention_seconds = 345600
  visibility_timeout_seconds = 120
  redrive_policy            = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn,
    maxReceiveCount     = 5
  })
}

output "sqs_queue_url" { value = aws_sqs_queue.main.id }
output "sqs_queue_arn" { value = aws_sqs_queue.main.arn }

