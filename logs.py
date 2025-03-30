import os
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model

# ✅ 1. Fix the typo
text = "Masked person walking at main gate"

class Person(BaseModel):
    Object: Optional[str] = Field(default=None, description="The type of object in the description e.g. car, security guard, include any information or adjective specifying the object")
    location: Optional[str] = Field(default=None, description="Location near object is present")
    activity: Optional[str] = Field(default=None, description="What the object is doing e.g. walking, inspecting")

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are an expert extraction algorithm. Only extract relevant information from the text. "
               "If you do not know the value of an attribute asked to extract, return null."),
    ("human", "{text}"),
])

os.environ["GROQ_API_KEY"] = "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"

# ✅ 2. Use a stronger model
llm = init_chat_model("llama-3.3-70b-versatile", model_provider="groq")
structured_llm = llm.with_structured_output(schema=Person)

prompt = prompt_template.invoke({"text": text})
# # ✅ 3. Extract the text and debug
# prompt_text = prompt.text
# print(f"Final Prompt Sent to LLM: {prompt_text}")

# ✅ 4. Invoke and print the response
response = structured_llm.invoke(prompt)
print(response)
