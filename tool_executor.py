import json

def lambda_handler(event, context):
    """
    This function is invoked directly by the Amazon Bedrock Agent when it 
    determines that a tool needs to be used based on the user's prompt.
    """
    # Bedrock sends a specific event structure for Action Groups
    action_group = event.get('actionGroup', '')
    function_name = event.get('function', '')
    parameters = event.get('parameters', [])
    
    response_body = {}
    
    if function_name == 'freeze_card':
        # Extract the token passed by the LLM
        card_token = next((param['value'] for param in parameters if param['name'] == 'card_token'), None)
        
        # In a real FinTech app, we would call an internal banking microservice here.
        # Notice we are operating strictly on the token (e.g., [CARD_1]), not the real PII!
        print(f"Executing core banking API to freeze token: {card_token}")
        
        response_body = {
            "TEXT": {
                "body": f"SUCCESS: The core banking system has frozen card token {card_token}."
            }
        }
    else:
        response_body = {"TEXT": {"body": "Function not recognized."}}
        
    # The required response format to send data back to the Bedrock Agent
    action_response = {
        "actionGroup": action_group,
        "function": function_name,
        "functionResponse": {
            "responseBody": response_body
        }
    }
    
    return {"response": action_response, "messageVersion": event.get('messageVersion', '1.0')}