# 1. Automatically zip the Python source code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/interceptor.zip"
}

# 2. Define the IAM Execution Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# 3. Define the strict IAM Policy (DynamoDB, CloudWatch, Bedrock)
resource "aws_iam_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Allow reading/writing to our specific Token Vault
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.token_vault.arn
      },
      {
        # Allow logging to CloudWatch
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # Allow invoking Bedrock models and agents (Prep for Phase 2)
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeAgent"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# 4. Provision the Lambda Function
resource "aws_lambda_function" "interceptor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-interceptor-${var.environment}"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "interceptor.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.12" 
  timeout          = 30 # Generous timeout for Bedrock agent invocations

  environment {
    variables = {
      TOKEN_VAULT_TABLE = aws_dynamodb_table.token_vault.name
      AGENT_ID          = aws_bedrockagent_agent.financial_agent.id
      AGENT_ALIAS_ID    = "TSTALIASID" # TSTALIASID is the default alias 
    }
  }
}

resource "aws_iam_role_policy" "lambda_bedrock_execution_policy" {
  name = "${var.project_name}-lambda-bedrock-policy-${var.environment}"
  role = aws_iam_role.lambda_exec_role.id 

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["bedrock:*"]
        Resource = "*"
      }
    ]
  })
}