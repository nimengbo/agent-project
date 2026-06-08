import json
from typing import Any, AsyncIterator

import httpx

from app.services.model_config_service import model_config_service


class DeepSeekNotConfiguredError(RuntimeError):
    pass


class DeepSeekAPIError(RuntimeError):
    pass


class DeepSeekService:
    def _headers(self) -> dict[str, str]:
        config = model_config_service.load()
        if not config.api_key:
            raise DeepSeekNotConfiguredError("DeepSeek API Key 未配置，请先在前端模型配置页填写。")
        return {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}

    async def chat(
        self,
        messages: list[dict[str, str]],
        use_reasoner: bool = False,
        temperature: float = 0.4,
        response_format: dict[str, str] | None = None,
    ) -> str:
        config = model_config_service.load()
        if not config.api_key:
            raise DeepSeekNotConfiguredError("DeepSeek API Key 未配置，请先在前端模型配置页填写。")
        model = config.reasoner_model if use_reasoner else config.chat_model
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{config.base_url.rstrip('/')}/v1/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = response.json().get("error", {}).get("message", response.text)
                raise DeepSeekAPIError(f"DeepSeek 调用失败（{response.status_code}）：{detail}") from exc
            payload = response.json()
            try:
                return payload["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise DeepSeekAPIError("DeepSeek 返回格式异常，请检查模型配置。") from exc

    async def json_chat(
        self,
        messages: list[dict[str, str]],
        use_reasoner: bool = False,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        content = await self.chat(
            messages,
            use_reasoner=use_reasoner,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return json.loads(content)

    async def stream_chat(self, messages: list[dict[str, str]], use_reasoner: bool = False) -> AsyncIterator[str]:
        config = model_config_service.load()
        if not config.api_key:
            raise DeepSeekNotConfiguredError("DeepSeek API Key 未配置，请先在前端模型配置页填写。")
        model = config.reasoner_model if use_reasoner else config.chat_model
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{config.base_url.rstrip('/')}/v1/chat/completions",
                headers=self._headers(),
                json={"model": model, "messages": messages, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ").strip()
                    if data == "[DONE]":
                        break
                    yield data


deepseek_service = DeepSeekService()
