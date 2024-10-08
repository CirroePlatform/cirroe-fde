from openai import OpenAI
import json
from . import base
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    print("Please pass in OPENAI_API_KEY in the .env file")
    exit(1)


class GPTClient(base.AbstractLLM):
    """A client module to call the GPT API"""

    def __init__(self) -> None:
        super().__init__()

        self._client = OpenAI(api_key=OPENAI_API_KEY)

    def query(
        self,
        prompt: str,
        engine: str = "gpt-4",
        temperature: int = 0.1,
        sys_prompt: str = None,
        is_json: bool = False,
    ) -> str:
        """A simple wrapper to the gpt api"""

        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        if sys_prompt is not None:
            messages.append(
                {
                    "role": "system",
                    "content": sys_prompt,
                }
            )

        client_kwargs = {
            "messages": messages,
            "model": engine,
            "temperature": temperature,
        }

        if is_json:
            client_kwargs["response_format"] = {"type": "json_object"}
            client_kwargs["model"] = "gpt-4-1106-preview"

        response = self._client.chat.completions.create(**client_kwargs)

        generated_response = response.choices[0].message.content.strip()

        if is_json:
            return json.loads(generated_response)

        return generated_response
