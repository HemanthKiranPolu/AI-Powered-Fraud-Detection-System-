resource "aws_kms_key" "s3_kms" {
  description             = "KMS key for S3 objects (fraud docs)"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "s3_kms_alias" {
  name          = "alias/${var.project_name}-s3"
  target_key_id = aws_kms_key.s3_kms.id
}

