from typing import Type, Optional
from crewai.tools import BaseTool
from mem0 import MemoryClient
import os
import logging
from typing import Any
from pydantic import BaseModel, Field

auth0_id = "111865405383405721093"
thread_id = "2394241c-f27e-4f79-adae-8d8a67c089e4"

client = MemoryClient(api_key="m0-DF90O1P1ad5pbj0DMspbqyor68M4VMpcelQeIMIh")

results = client.get_all(
    user_id=auth0_id,
    agent_id=f"essay_feedback_{thread_id}",
    filters={
        "metadata": {
            "thread_id": thread_id,
            "type": "essay_feedback"
        }
    }
)

print(results)

 