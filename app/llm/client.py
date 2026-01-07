import os
import json
from typing import List, Dict, Any, Optional, Generator, Union
from app.config.settings import get_settings

class LLMClient:
    """
    Unified client for interacting with various LLM providers.
    """
    def __init__(self):
        self.settings = get_settings()
        self.provider = self.settings.LLM_PROVIDER.lower()

    def generate(self, system_prompt: str, user_prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        if self.provider == "openai":
            return self._generate_openai(system_prompt, user_prompt, stream)
        elif self.provider == "gemini":
            return self._generate_gemini(system_prompt, user_prompt, stream)
        elif self.provider == "ollama":
            return self._generate_ollama(system_prompt, user_prompt, stream)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _generate_openai(self, system_prompt: str, user_prompt: str, stream: bool) -> Union[str, Generator[str, None, None]]:
        from openai import OpenAI
        client = OpenAI(api_key=self.settings.OPENAI_API_KEY, base_url=self.settings.OPENAI_BASE_URL)
        
        response = client.chat.completions.create(
            model=self.settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=stream
        )
        
        if stream:
            def gen():
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
            return gen()
        else:
            return response.choices[0].message.content

    def _generate_gemini(self, system_prompt: str, user_prompt: str, stream: bool) -> Union[str, Generator[str, None, None]]:
        import google.generativeai as genai
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(self.settings.GEMINI_MODEL)
        
        # Combine system prompt with user prompt for Gemini-compatible instruction
        full_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}"
        
        response = model.generate_content(full_prompt, stream=stream)
        
        if stream:
            def gen():
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            return gen()
        else:
            return response.text

    def _generate_ollama(self, system_prompt: str, user_prompt: str, stream: bool) -> Union[str, Generator[str, None, None]]:
        import requests
        url = f"{self.settings.OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": self.settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": stream
        }
        
        if stream:
            response = requests.post(url, json=payload, stream=True)
            def gen():
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
            return gen()
        else:
            response = requests.post(url, json=payload)
            return response.json()["message"]["content"]

