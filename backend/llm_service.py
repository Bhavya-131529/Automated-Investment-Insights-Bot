import os
from openai import OpenAI
from backend.rag_engine import get_retriever
from backend.finance_tools import get_stock_price
import json

client = OpenAI()

SYSTEM_PROMPT = """You are a professional AI Investment Insights Assistant. 
Your goal is to provide personalized, risk-aware investment strategies based on user profiles and financial knowledge.

Rules:
1. Always include a disclaimer: "This is for informational purposes only and not financial advice."
2. Do not guarantee returns.
3. Prioritize stable, diversified strategies over stock tips.
4. Use the provided context from our knowledge base and live market data.
5. If the user asks for specific stock prices, use the tool data if available.
6. If the user provides 'existing_holdings', provide portfolio insights and suggest rebalancing if necessary to align with their risk tolerance.
7. Ensure your suggestions are structured and easy to read.

User Profile:
{user_profile}

Context from Knowledge Base:
{context}
"""

def generate_response(query: str, profile_data: dict, chat_history: list):
    # 1. Retrieve context from RAG
    retriever = get_retriever()
    context = ""
    if retriever:
        docs = retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in docs])
    
    # 2. Get live market data (example: check SPY and AGG for base indices)
    spy_data = get_stock_price("SPY")
    agg_data = get_stock_price("AGG")
    market_context = f"\nMarket Data:\nSPY (S&P 500): {spy_data}\nAGG (Total Bond Market): {agg_data}"
    
    # 3. Construct messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(
            user_profile=json.dumps(profile_data),
            context=context + market_context
        )}
    ]
    
    # Add chat history
    for msg in chat_history[-5:]: # Last 5 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": query})
    
    # 4. Call LLM
    response = client.chat.completions.create(
        model="gpt-4o", # or gpt-3.5-turbo
        messages=messages,
        temperature=0.7
    )
    
    return response.choices[0].message.content
