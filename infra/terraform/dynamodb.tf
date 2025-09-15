resource "aws_dynamodb_table" "cases" {
  name         = var.cases_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "case_id"

  attribute { name = "case_id" type = "S" }
}

resource "aws_dynamodb_table" "events" {
  name         = var.events_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "case_id"
  range_key    = "ts"

  attribute { name = "case_id" type = "S" }
  attribute { name = "ts" type = "N" }
  attribute { name = "device_hash" type = "S" }

  ttl { attribute_name = "ttl" enabled = true }

  global_secondary_index {
    name            = "gsi_device"
    hash_key        = "device_hash"
    range_key       = "ts"
    projection_type = "ALL"
  }
}

output "cases_table_name" { value = aws_dynamodb_table.cases.name }
output "events_table_name" { value = aws_dynamodb_table.events.name }

