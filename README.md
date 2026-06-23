# 🛡️ Enterprise GenAI Tokenization Firewall
**Architected & Built by: Syed Taher**

A zero-trust data privacy architecture for Enterprise Generative AI. This infrastructure acts as a bidirectional firewall, allowing Large Language Models (LLMs) to process sensitive customer requests without ever exposing plaintext Personally Identifiable Information (PII) or Payment Card Industry (PCI) data to the AI provider.

## 🚀 Key Engineering Features
* **Format-Preserving Encryption (FPE):** Uses dynamic regex to intercept sensitive data (Credit Cards, Phone Numbers, PANs) and swaps them with mathematically valid synthetic tokens (e.g., Luhn-valid decoy cards). This prevents downstream third-party API crashes while keeping real data hidden.
* **Stateful Ephemeral Vault (DynamoDB TTL):** Token mappings are stored in DynamoDB with a strict 5-minute Time-To-Live (TTL). AWS automatically destroys the plaintext mapping once the session expires, ensuring zero long-term data retention footprint.
* **Sub-String Rehydration Logic:** Built advanced egress filters to catch AI data truncations (e.g., when the AI summarizes a 16-digit card to "ending in 4444"). The firewall seamlessly maps the synthetic last-4 digits back to the customer's real last-4 digits.
* **Serverless Infrastructure as Code:** 100% modular AWS infrastructure provisioned via Terraform.

## 🏗️ Architecture Flow
1. **Ingress:** API Gateway receives the raw customer payload.
2. **Masking:** Interceptor Lambda strips PII, generates FPE tokens, and stores the mapping in DynamoDB.
3. **AI Execution:** AWS Bedrock (Claude 4.5 Sonnet) reads the sanitized prompt, determines the user's intent, and invokes the `freeze_card` Lambda tool using the synthetic token.
4. **Egress:** The Interceptor catches the AI's response stream, queries DynamoDB, rehydrates the structural and FPE tokens back to plaintext, and returns the secure payload to the client.

## 🛠️ Technology Stack
* **Cloud:** AWS Bedrock, AWS Lambda, Amazon DynamoDB, Amazon API Gateway, AWS IAM
* **Infrastructure as Code:** HashiCorp Terraform
* **Backend:** Python 3.12 (Boto3)
* **Frontend/UI:** Streamlit (For simulated user/inspector dashboard)

## 💻 Live Demonstration
The project includes a Streamlit UI to demonstrate the bidirectional firewall in real-time. 
* The **Customer UI** shows the natural language experience.
* The **Security Inspector** reveals the masked JSON payloads, synthetic tokens, and DynamoDB session IDs under the hood.

*(Note: Add a screenshot of your Streamlit UI here once it is uploaded to GitHub!)*
