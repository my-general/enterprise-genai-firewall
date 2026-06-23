import os
import re
import json
import uuid
import time
import random
import string
import boto3
import traceback

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TOKEN_VAULT_TABLE', 'genai-secure-firewall-token-vault-dev')
table = dynamodb.Table(TABLE_NAME)

PAN_REGEX = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b') 
CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,16}\b')    
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b') 

def generate_luhn_valid_card():
    """Generates a synthetic 16-digit Visa card that passes the Luhn check"""
    card = [4] + [random.randint(0, 9) for _ in range(14)]
    checksum = 0
    for i, digit in enumerate(card[::-1]):
        if i % 2 == 0:
            doubled = digit * 2
            checksum += doubled if doubled <= 9 else doubled - 9
        else:
            checksum += digit
    check_digit = (10 - (checksum % 10)) % 10
    card.append(check_digit)
    return ''.join(map(str, card))

def generate_fake_pan():
    """Generates a synthetic PAN matching the format ABCDE1234F"""
    letters1 = ''.join(random.choices(string.ascii_uppercase, k=5))
    numbers = ''.join(random.choices(string.digits, k=4))
    letter2 = random.choice(string.ascii_uppercase)
    return letters1 + numbers + letter2

def generate_fake_phone():
    """Generates a synthetic standard phone number"""
    return f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

def mask_text(text: str):
    token_map = {}
    sanitized_text = text
    
    # Replace real cards with synthetic Luhn-valid cards
    cards = CARD_REGEX.findall(sanitized_text)
    for card in set(cards):
        clean_card = card.strip()
        synthetic_token = generate_luhn_valid_card()
        token_map[synthetic_token] = clean_card
        sanitized_text = sanitized_text.replace(clean_card, synthetic_token)

    # Replace real PANs with synthetic PANs
    pans = PAN_REGEX.findall(sanitized_text)
    for pan in set(pans):
        synthetic_token = generate_fake_pan()
        token_map[synthetic_token] = pan
        sanitized_text = sanitized_text.replace(pan, synthetic_token)

    # Replace real phones with synthetic phones
    phones = PHONE_REGEX.findall(sanitized_text)
    for phone in set(phones):
        synthetic_token = generate_fake_phone()
        token_map[synthetic_token] = phone
        sanitized_text = sanitized_text.replace(phone, synthetic_token)

    return sanitized_text, token_map

def lambda_handler(event, context):
    try:
        print("DEBUG [1]: Received Event Payload")
        body = json.loads(event.get('body', '{}'))
        raw_prompt = body.get('prompt', '')
        customer_name = body.get('name', 'Unknown')
        session_id = body.get('sessionId', str(uuid.uuid4()))
        
        print("DEBUG [2]: Running Masking Engine")
        masked_prompt, token_map = mask_text(raw_prompt)
        
        if customer_name and customer_name != 'Unknown':
            token_map["[NAME_1]"] = customer_name
            masked_prompt = masked_prompt.replace(customer_name, "[NAME_1]")

        print(f"DEBUG [3]: Token Map Generated -> {token_map}")
        
        ttl_expiry = int(time.time()) + 300 
        if token_map:
            table.put_item(
                Item={
                    'SessionId': session_id,
                    'TokenMap': token_map,
                    'ttl': ttl_expiry
                }
            )
            
        print("DEBUG [4]: DynamoDB State Saved Successfully")
            
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        agent_id = os.environ.get('AGENT_ID')
        agent_alias_id = os.environ.get('AGENT_ALIAS_ID', 'TSTALIASID')
        
        print(f"DEBUG [5]: Invoking Bedrock Agent (ID: {agent_id}, Alias: {agent_alias_id})")
        
        agent_response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=masked_prompt
        )
        
        print("DEBUG [6]: Bedrock API Call Successful, parsing stream...")
        ai_generated_text = ""
        for event_stream in agent_response.get('completion'):
            if 'chunk' in event_stream:
                ai_generated_text += event_stream['chunk']['bytes'].decode('utf-8')

        print(f"DEBUG [7]: AI Raw Tokenized Output -> {ai_generated_text}")

        # Fetch the token map from DynamoDB for rehydration
        response_item = table.get_item(Key={'SessionId': session_id})
        saved_map = response_item.get('Item', {}).get('TokenMap', {})
        
        rehydrated_response = ai_generated_text
        
        # DEBUG [8]: Advanced Sub-String Rehydration Loop
        for token, real_value in saved_map.items():
            # 1. Replace the exact full token if it exists in the text
            rehydrated_response = rehydrated_response.replace(token, real_value)
            
            # 2. Check for LLM string truncations (e.g., "ending in 1549")
            if len(token) == 16 and token.isdigit():
                synthetic_last_4 = token[-4:]
                real_last_4 = real_value[-4:]
                
                # Replace the fake last 4 digits with the real last 4 digits
                rehydrated_response = rehydrated_response.replace(synthetic_last_4, real_last_4)

        print("DEBUG [8]: Rehydration Complete. Sending Payload to Client.")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'sessionId': session_id,
                'input_was_masked': len(token_map) > 0,
                'entities_masked_count': len(token_map),
                'safe_agent_payload': masked_prompt,
                'final_response': rehydrated_response
            })
        }

    except Exception as e:
        print("--- DEBUG SYSTEM FAILURE TRACEBACK ---")
        traceback.print_exc()
        print(f"ERROR DETAILS: {str(e)}")
        print("--------------------------------------")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'debug_hint': "Check Amazon CloudWatch Logs for the full traceback."
            })
        }