import os
import json
from groq import Groq
from backend.rag_engine import get_retriever
from backend.finance_tools import get_stock_price
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Initialize client only if key is available to avoid crash on import
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Condensed system prompt to minimize token usage
SYSTEM_PROMPT = """AI Investment Assistant.
Rules:
1. Add disclaimer: "Not financial advice."
2. No guarantees. Focus on stable strategies.
3. Use context/market data.
4. Consider user profile. Keep structured & concise.

Profile:
{user_profile}

Context:
{context}
"""

def generate_response(query: str, profile_data: dict, chat_history: list):
    if not client:
        return "GROQ_API_KEY is not set."
        
    retriever = get_retriever()
    context = ""
    if retriever:
        try:
            # Retrieve only 1 doc, limit text length to save tokens
            docs = retriever.invoke(query)
            if docs:
                context = docs[0].page_content[:300]
        except Exception as e:
            pass

    try:
        spy_data = get_stock_price("SPY")
        market_context = f"\nSPY: {spy_data.get('price', 'N/A')}"
    except:
        market_context = ""

    system_instruction = SYSTEM_PROMPT.format(
        user_profile=json.dumps(profile_data, default=str),
        context=context + market_context
    )

    messages = [{"role": "system", "content": system_instruction}]
    
    # Only keep the last 2 messages for token efficiency
    for msg in chat_history[-2:]:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})
        
    messages.append({"role": "user", "content": query})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="llama-3.1-8b-instant",
        temperature=0.5,
        max_tokens=300,
    )
    return chat_completion.choices[0].message.content
