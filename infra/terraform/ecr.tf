resource "aws_ecr_repository" "api" {
  name                 = var.api_ecr_repo
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "worker" {
  name                 = var.worker_ecr_repo
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

output "api_ecr_repo_url" { value = aws_ecr_repository.api.repository_url }
output "worker_ecr_repo_url" { value = aws_ecr_repository.worker.repository_url }

