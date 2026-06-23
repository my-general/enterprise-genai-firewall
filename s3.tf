# 1. Generate a random suffix for global uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# 2. Create the S3 Bucket for Knowledge Base Documents
resource "aws_s3_bucket" "knowledge_base" {
  bucket        = "${var.project_name}-kb-docs-${random_id.bucket_suffix.hex}-${var.environment}"
  force_destroy = true # Allows Terraform to delete the bucket later even if it has files
}

# 3. Enable Versioning (Enterprise Best Practice for SOPs)
resource "aws_s3_bucket_versioning" "kb_versioning" {
  bucket = aws_s3_bucket.knowledge_base.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 4. Enforce strict server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "kb_encryption" {
  bucket = aws_s3_bucket.knowledge_base.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Output the bucket name so we can upload to it
output "s3_knowledge_base_bucket" {
  value       = aws_s3_bucket.knowledge_base.bucket
  description = "The S3 bucket for Bedrock RAG documents"
}