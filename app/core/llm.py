from __future__ import annotations

from typing import Any

from openai import NotFoundError, OpenAI

from .config import Settings


class OpenAITextGenerator:
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY 未配置，请先复制 .env.example 为 .env 并填写密钥。")

        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self.api_mode = settings.openai_api_mode.strip().lower() or "auto"
        self.model_name = settings.model_name
        self.temperature = settings.temperature

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.api_mode == "responses":
            return self._generate_with_responses(system_prompt, user_prompt)
        if self.api_mode == "chat":
            return self._generate_with_chat(system_prompt, user_prompt)

        try:
            return self._generate_with_chat(system_prompt, user_prompt)
        except NotFoundError:
            return self._generate_with_responses(system_prompt, user_prompt)

    def _generate_with_chat(self, system_prompt: str, user_prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model_name,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content or ""

    def _generate_with_responses(self, system_prompt: str, user_prompt: str) -> str:
        resp = self.client.responses.create(
            model=self.model_name,
            temperature=self.temperature,
            instructions=system_prompt,
            input=user_prompt,
        )

        output_text = getattr(resp, "output_text", None)
        if output_text:
            return output_text

        parts: list[str] = []
        for item in getattr(resp, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = self._extract_text(content)
                if text:
                    parts.append(text)
        return "".join(parts)

    @staticmethod
    def _extract_text(content: Any) -> str:
        if isinstance(content, dict):
            text = content.get("text")
            if isinstance(text, dict):
                return str(text.get("value", ""))
            if text:
                return str(text)
            return str(content.get("value", ""))

        text = getattr(content, "text", None)
        if isinstance(text, str):
            return text

        if text is not None:
            value = getattr(text, "value", None)
            if value:
                return str(value)

        value = getattr(content, "value", None)
        return str(value or "")
