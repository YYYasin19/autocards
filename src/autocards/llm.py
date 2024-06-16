import openai
import os
import json
from typing import List, Dict


class OpenAI:
    context_length = 128_000

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        assert os.environ.get("OPENAI_API_KEY"), "Please set the OPENAI_API_KEY environment variable"
        self.client = openai.Client(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_json(self, system_prompt, prompt: str) -> List[Dict]:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        response_text = response.choices[0].message.content
        try:
            return json.loads(response_text) if response_text else [{}]
        except Exception as e:
            raise RuntimeError(f"Error loading response for: {e}\n---\n{response_text}")
