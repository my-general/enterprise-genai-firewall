import streamlit as st
import requests
import json

# 1. Page Configuration
st.set_page_config(
    page_title="GenAI Firewall | Syed Taher",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Replace this with your actual API Gateway URL if it changes
API_URL = "https://1jj0ccz71l.execute-api.us-east-1.amazonaws.com/dev/dispute"

# 2. Header Section
st.title("🛡️ Enterprise GenAI Tokenization Firewall")
st.markdown("### Zero-Trust PII Masking & Rehydration Architecture")
st.caption("Architected & Built by **Syed Taher** | FinTech Security Portfolio")
st.markdown("---")

# 3. Layout layout (Split Screen)
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("💬 Customer Interface")
    st.markdown("Simulate a user chatting with the banking assistant.")
    
    with st.form("chat_form"):
        customer_name = st.text_input("Customer Name", value="Jane Smith")
        user_prompt = st.text_area(
            "Message to AI Agent", 
            value="Hello, I am Jane Smith. I lost my wallet! Please freeze my Visa card 4111222233334444 immediately. You can reach me at +1-555-123-4567. My PAN is ABCDE1234F.",
            height=150
        )
        submit_button = st.form_submit_button("Send to Secure Agent", type="primary")

with col2:
    st.subheader("🔍 Security Inspector (Backend)")
    st.markdown("Watch the firewall intercept, mask, and rehydrate the data in real-time.")
    
    # Placeholder for the results
    inspector_placeholder = st.empty()
    inspector_placeholder.info("Awaiting traffic... Send a message to intercept the payload.")

# 4. Action Logic
if submit_button:
    with st.spinner("Encrypting payload and querying Bedrock Agent..."):
        try:
            # Send the request to your Terraform API Gateway
            payload = {
                "name": customer_name,
                "prompt": user_prompt
            }
            response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
            
            if response.status_code == 200:
                data = response.json()
                
                # Update the Chat UI with the final rehydrated response
                with col1:
                    st.success("**Agent Response (Rehydrated):**")
                    st.write(data.get("final_response", "No response received."))
                
                # Update the Inspector UI with the behind-the-scenes magic
                with inspector_placeholder.container():
                    st.warning("🚨 **Ingress Firewall Triggered**")
                    st.metric(label="Sensitive Entities Masked via FPE", value=data.get("entities_masked_count", 0))
                    
                    st.markdown("**1. What the AI actually saw (FPE Synthetic Data):**")
                    st.code(data.get("safe_agent_payload", ""), language="text")
                    
                    st.markdown("**2. Session State ID (DynamoDB TTL Vault):**")
                    st.code(data.get("sessionId", ""), language="text")
                    
                    st.markdown("**3. Raw JSON Payload:**")
                    st.json(data)
                    
            else:
                st.error(f"API Error {response.status_code}: {response.text}")
                
        except Exception as e:
            st.error(f"Failed to connect to the firewall API. Error: {str(e)}")