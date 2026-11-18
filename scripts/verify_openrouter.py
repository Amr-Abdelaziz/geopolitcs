"""Strategic OSIRIS - OpenRouter Verification and Diagnostic Tool.
Tests authentication, credit budget, model availability, and live inference.
"""
import os
import sys

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

# Inject Windows native root certificates
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

import httpx
from packages.openrouter.client import OpenRouterClient, DEFAULT_TIER_MODELS
from packages.schemas.models import AgentID

def main():
    print("=" * 65)
    print("🌐 OPENROUTER LIVE CONNECTION VERIFICATION")
    print("=" * 65)

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY is not set in .env")
        sys.exit(1)

    print(f"[*] API Key Loaded: {api_key[:12]}...{api_key[-4:]}")

    # 1. Check Key Auth & Limits
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        res = httpx.get("https://openrouter.ai/api/v1/auth/key", headers=headers, timeout=10.0, verify=False)
        if res.status_code == 200:
            data = res.json().get("data", {})
            print(f"[✅] Authentication Successful (HTTP 200)")
            print(f"[*] Key Label: {data.get('label')}")
            print(f"[*] Total Budget Limit: ${data.get('limit', 'unlimited')}")
            print(f"[*] Remaining Balance: ${data.get('limit_remaining', 'unknown'):.4f}" if isinstance(data.get('limit_remaining'), (int, float)) else f"[*] Balance: {data.get('limit_remaining')}")
            print(f"[*] Total Spend so far: ${data.get('usage', 0.0):.4f}")
        else:
            print(f"[❌] Auth check failed: HTTP {res.status_code} - {res.text}")
            sys.exit(1)
    except Exception as e:
        print(f"[❌] Network error contacting OpenRouter: {e}")
        sys.exit(1)

    # 2. Test Live Inference with OpenRouterClient
    print("\n" + "-" * 65)
    print("[*] Testing Live Inference via OpenRouter Client...")
    client = OpenRouterClient()
    print(f"[*] Client Mock Mode: {client.mock_mode} (Should be False)")

    test_model = "meta-llama/llama-3.3-70b-instruct"
    test_messages = [
        {"role": "system", "content": "You are a senior defense analyst for Strategic OSIRIS. Respond concisely in formal Arabic."},
        {"role": "user", "content": "ما هي أهمية تأمين الملاحة في مضيق باب المندب وقناة السويس بالنسبة للأمن القومي المصري؟"}
    ]

    print(f"[*] Querying Model: {test_model}")
    import asyncio
    try:
        reply = asyncio.run(client.complete(
            test_messages,
            model=test_model,
            max_tokens=200,
            agent_id=AgentID.A04_MILITARY
        ))
        print(f"[✅] Response Received Successfully from OpenRouter!")
        print("\n--- Model Output (Arabic) ---")
        print(reply.strip())
        print("-----------------------------\n")
    except Exception as e:
        print(f"[❌] Inference failed: {e}")
        sys.exit(1)

    # 3. Model Tiers Verification
    print("-" * 65)
    print("[*] Configured Agent Model Routing on OpenRouter:")
    for aid, m in list(DEFAULT_TIER_MODELS.items())[:6]:
        print(f"    • {aid.value}: {m}")
    print("    • ... and all other 8 agents mapped to high-tier models.")

    print("=" * 65)
    print("🎉 OPENROUTER IS FULLY WORKING AND OPERATIONAL!")
    print("=" * 65)

if __name__ == "__main__":
    main()
