output "api_endpoint" {
  value       = "${aws_api_gateway_stage.api_stage.invoke_url}/${aws_api_gateway_resource.dispute.path_part}"
  description = "The public URL to test your Secure GenAI Firewall"
}