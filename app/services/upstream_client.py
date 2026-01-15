"""
上游API客户端（OpenAI/Azure OpenAI）
"""
import httpx
import json
from typing import AsyncGenerator, Optional, Dict, Any
from app.config import settings
from app.utils.logger import logger


class UpstreamClient:
    """上游API客户端"""
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = httpx.Timeout(timeout, connect=settings.UPSTREAM_CONNECT_TIMEOUT)
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def chat_completions(
        self,
        model: str,
        messages: list,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        调用chat completions接口
        
        Yields:
            dict: SSE事件数据或完整响应
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            async with self.client.stream("POST", url, headers=headers, json=data) as response:
                response.raise_for_status()
                
                if stream:
                    # SSE流式响应
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]  # 去掉 "data: " 前缀
                            if data_str == "[DONE]":
                                yield {"type": "done"}
                                break
                            try:
                                event_data = json.loads(data_str)
                                yield {"type": "data", "data": event_data}
                            except json.JSONDecodeError:
                                continue
                else:
                    # 非流式响应
                    result = await response.json()
                    yield {"type": "complete", "data": result}
                    
        except httpx.HTTPStatusError as e:
            error_data = {
                "type": "error",
                "status_code": e.response.status_code,
                "error": await e.response.aread() if hasattr(e.response, 'aread') else str(e)
            }
            yield error_data
        except Exception as e:
            logger.error(f"Upstream request failed: {e}")
            yield {"type": "error", "error": str(e)}
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


class AzureUpstreamClient(UpstreamClient):
    """Azure OpenAI客户端"""
    
    def __init__(self, endpoint: str, api_key: str, deployment_name: str, api_version: str, timeout: int = 300):
        # Azure OpenAI的URL格式
        base_url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment_name}"
        super().__init__(base_url, api_key, timeout)
        self.api_version = api_version
    
    async def chat_completions(
        self,
        model: str,  # 在Azure中，model参数会被忽略，使用deployment_name
        messages: list,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Azure OpenAI的chat completions"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "api-key": self.api_key,  # Azure使用api-key而不是Authorization
            "Content-Type": "application/json"
        }
        
        params = {
            "api-version": self.api_version
        }
        
        data = {
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            async with self.client.stream("POST", url, headers=headers, params=params, json=data) as response:
                response.raise_for_status()
                
                if stream:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                yield {"type": "done"}
                                break
                            try:
                                event_data = json.loads(data_str)
                                yield {"type": "data", "data": event_data}
                            except json.JSONDecodeError:
                                continue
                else:
                    result = await response.json()
                    yield {"type": "complete", "data": result}
                    
        except httpx.HTTPStatusError as e:
            error_data = {
                "type": "error",
                "status_code": e.response.status_code,
                "error": await e.response.aread() if hasattr(e.response, 'aread') else str(e)
            }
            yield error_data
        except Exception as e:
            logger.error(f"Azure upstream request failed: {e}")
            yield {"type": "error", "error": str(e)}
