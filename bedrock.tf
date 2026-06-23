# 1. Zip the Tool Executor Python code
data "archive_file" "tool_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/tool_executor.py"
  output_path = "${path.module}/tool_executor.zip"
}

# 2. Tool Executor Lambda (Uses the role you defined in lamda.tf!)
resource "aws_lambda_function" "tool_executor" {
  filename         = data.archive_file.tool_zip.output_path
  function_name    = "${var.project_name}-tool-executor-${var.environment}"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "tool_executor.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.tool_zip.output_base64sha256
}

# 3. Bedrock Agent Role
resource "aws_iam_role" "bedrock_agent_role" {
  name = "${var.project_name}-bedrock-role-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "bedrock.amazonaws.com" } }]
  })
}
# 4. Allow Agent unrestricted access to Bedrock models and the Tool Lambda
resource "aws_iam_role_policy" "bedrock_agent_policy" {
  name   = "${var.project_name}-bedrock-policy-${var.environment}"
  role   = aws_iam_role.bedrock_agent_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        # Bypasses all hidden sub-action requirements for Claude 4.5
        Action   = ["bedrock:*"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        # Explicitly grants the Agent role permission to fire the tool
        Action   = ["lambda:InvokeFunction"]
        Resource = aws_lambda_function.tool_executor.arn
      }
    ]
  })
}

# 5. Grant Agent permission to invoke Tool Lambda
resource "aws_lambda_permission" "allow_bedrock_tool" {
  statement_id  = "AllowBedrockInvokeTool"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tool_executor.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = aws_bedrockagent_agent.financial_agent.agent_arn
}

# 6. Bedrock Agent
resource "aws_bedrockagent_agent" "financial_agent" {
  agent_name              = "${var.project_name}-agent-${var.environment}"
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn
  foundation_model        = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
  instruction             = "You are a professional banking assistant. When responding, always start by greeting the customer using the exact name token they provided. When a user asks to freeze their card, use the 'freeze_card' tool and pass the 16-digit credit card number they provided in their prompt."
}

# 7. Action Group
resource "aws_bedrockagent_agent_action_group" "freeze_card_action" {
  action_group_name          = "FreezeCardAction"
  agent_id                   = aws_bedrockagent_agent.financial_agent.id
  agent_version              = "DRAFT"
  skip_resource_in_use_check = true
  
  action_group_executor { 
    lambda = aws_lambda_function.tool_executor.arn 
  }
  
  function_schema {
    member_functions {
      functions {
        name        = "freeze_card"
        description = "Freezes a credit card"
        parameters {
          map_block_key = "card_token"
          type          = "string"
          description   = "The tokenized card number (e.g. [CARD_1])"
          required      = true
        }
      }
    }
  }
}