import os
import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
print('OPENAI_API_KEY at runtime:', os.getenv('OPENAI_API_KEY'))

model = ChatOpenAI(temperature=0)

prompt = ChatPromptTemplate.from_template("""
You are a loyalty assistant that extracts user intent and identifiers from messages.

Return your response as strict JSON in this exact format:
{{
  "intent": "get_point_balance" | "get_active_campaigns" | "get_active_offers" | "get_offer_expiry" | "show_offers" | "show_campaigns" | "identify_user",
  "value": "string or null"
}}

Respond with only the JSON.

Message: "{message}"

Examples:
Message: "Here's my email claire.braun267@sessionmdemo.com"
Output: {{ "intent": "identify_user", "value": "claire.braun267@sessionmdemo.com" }}

Message: "When does my offer expire?"
Output: {{ "intent": "get_offer_expiry", "value": null }}

Message: "Show me the offers"
Output: {{ "intent": "show_offers", "value": null }}

Message: "Show them"
Output: {{ "intent": "show_offers", "value": null }}

Message: "Show me my campaigns"
Output: {{ "intent": "show_campaigns", "value": null }}

Message: "Show campaigns"
Output: {{ "intent": "show_campaigns", "value": null }}

Message: "Show them"
Output: {{ "intent": "show_campaigns", "value": null }}
""")

chain: RunnableSequence = prompt | model

async def extract_intent_and_value(message: str) -> dict:
    response = await chain.ainvoke({"message": message})
    print("🧠 Agent interpretation:", response.content)

    try:
        parsed = json.loads(response.content)
        if not isinstance(parsed, dict) or "intent" not in parsed:
            raise ValueError("Bad format")
        return parsed
    except Exception as e:
        print("❌ Failed to parse LLM output:", response.content)
        return {"intent": None, "value": None}
