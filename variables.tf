variable "aws_region" {
  type    = string
  default = "us-east-1" # Bedrock features like Claude 3.5 Sonnet are universally stable here
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "project_name" {
  type    = string
  default = "genai-secure-firewall"
}