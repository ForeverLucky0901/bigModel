"""
Chat Completions API（兼容OpenAI）
"""
import json
import time
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.base import get_db
from app.middleware.auth import verify_api_key
from app.services.key_pool import KeyPoolService
from app.services.upstream_client import UpstreamClient, AzureUpstreamClient
from app.services.usage_tracker import UsageTracker
from app.config import settings
from app.utils.logger import logger

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    user: Optional[str] = None


@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    db: Session = Depends(get_db),
    _: tuple = Depends(verify_api_key)
):
    """
    Chat Completions接口（兼容OpenAI）
    """
    start_time = time.time()
    user = request.state.user
    api_key = request.state.api_key
    
    # API Key限流检查（在鉴权之后）
    from app.services.rate_limiter import RateLimiter
    from app.config import settings
    estimated_tokens = sum(len(msg.content) * 0.25 for msg in body.messages) + (body.max_tokens or 1000)
    estimated_tokens = int(estimated_tokens)
    
    limit_rpm = api_key.rate_limit_rpm or settings.RATE_LIMIT_RPM
    limit_tpm = api_key.rate_limit_tpm or settings.RATE_LIMIT_TPM
    
    is_allowed, info = RateLimiter.check_rate_limit(
        identifier=api_key.key,
        limit_rpm=limit_rpm,
        limit_tpm=limit_tpm,
        current_tokens=estimated_tokens,
        prefix="key"
    )
    
    if not is_allowed:
        logger.warning(f"API key rate limit exceeded: {api_key.key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "message": "Rate limit exceeded",
                    "type": "rate_limit_error",
                    "code": "rate_limit_exceeded",
                    **info
                }
            }
        )
    
    # 检查模型是否允许
    if api_key.allowed_models:
        import json as json_lib
        allowed = json_lib.loads(api_key.allowed_models) if isinstance(api_key.allowed_models, str) else api_key.allowed_models
        if body.model not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {body.model} is not allowed for this API key"
            )
    
    # 估算token数（用于配额检查）
    estimated_tokens = sum(len(msg.content) * 0.25 for msg in body.messages) + (body.max_tokens or 1000)
    estimated_tokens = int(estimated_tokens)
    
    # 检查配额
    quota_ok, quota_error = UsageTracker.check_quota(db, user.id, estimated_tokens)
    if not quota_ok:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=quota_error
        )
    
    # 选择上游密钥
    upstream_key = KeyPoolService.select_key(db, settings.UPSTREAM_TYPE)
    if not upstream_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No healthy upstream keys available"
        )
    
    # 获取解密后的密钥
    try:
        decrypted_key = KeyPoolService.get_decrypted_key(upstream_key)
    except Exception as e:
        logger.error(f"Failed to decrypt upstream key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
    # 创建上游客户端
    if settings.UPSTREAM_TYPE == "azure":
        if not upstream_key.azure_endpoint or not upstream_key.azure_deployment_name:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Azure configuration incomplete"
            )
        client = AzureUpstreamClient(
            endpoint=upstream_key.azure_endpoint,
            api_key=decrypted_key,
            deployment_name=upstream_key.azure_deployment_name,
            api_version=upstream_key.azure_api_version or settings.AZURE_API_VERSION,
            timeout=settings.UPSTREAM_TIMEOUT
        )
    else:
        client = UpstreamClient(
            base_url=settings.OPENAI_BASE_URL,
            api_key=decrypted_key,
            timeout=settings.UPSTREAM_TIMEOUT
        )
    
    # 准备请求体
    request_data = {
        "model": body.model,
        "messages": [msg.dict() for msg in body.messages],
        "stream": body.stream
    }
    if body.temperature is not None:
        request_data["temperature"] = body.temperature
    if body.top_p is not None:
        request_data["top_p"] = body.top_p
    if body.n is not None:
        request_data["n"] = body.n
    if body.stop is not None:
        request_data["stop"] = body.stop
    if body.max_tokens is not None:
        request_data["max_tokens"] = body.max_tokens
    if body.presence_penalty is not None:
        request_data["presence_penalty"] = body.presence_penalty
    if body.frequency_penalty is not None:
        request_data["frequency_penalty"] = body.frequency_penalty
    if body.user is not None:
        request_data["user"] = body.user
    
    # 获取客户端IP和User-Agent
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    # 记录请求体（如果配置允许）
    request_body_str = None
    if settings.LOG_PROMPT_BODY:
        request_body_str = json.dumps(request_data, ensure_ascii=False)
    
    try:
        if body.stream:
            # 流式响应
            return StreamingResponse(
                stream_chat_completions(
                    client,
                    request_data,
                    db,
                    user.id,
                    api_key.id,
                    upstream_key.id,
                    body.model,
                    client_ip,
                    user_agent,
                    request_body_str,
                    start_time
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
                }
            )
        else:
            # 非流式响应
            return await handle_non_streaming(
                client,
                request_data,
                db,
                user.id,
                api_key.id,
                upstream_key.id,
                body.model,
                client_ip,
                user_agent,
                request_body_str,
                start_time
            )
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        KeyPoolService.record_failure(db, upstream_key.id, str(type(e).__name__))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    finally:
        await client.close()


async def stream_chat_completions(
    client: UpstreamClient,
    request_data: dict,
    db: Session,
    user_id: int,
    api_key_id: int,
    upstream_key_id: int,
    model: str,
    client_ip: Optional[str],
    user_agent: Optional[str],
    request_body_str: Optional[str],
    start_time: float
):
    """处理流式响应"""
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    error_occurred = False
    error_type = None
    error_message = None
    response_status = 200
    
    try:
        async for event in client.chat_completions(**request_data):
            if event["type"] == "error":
                error_occurred = True
                response_status = event.get("status_code", 500)
                error_type = "upstream_error"
                error_message = str(event.get("error", "Unknown error"))
                yield f"data: {json.dumps({'error': {'message': error_message, 'type': 'server_error'}})}\n\n"
                break
            elif event["type"] == "data":
                data = event["data"]
                # 提取token信息
                if "usage" in data:
                    usage = data["usage"]
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                # 转发SSE事件
                yield f"data: {json.dumps(data)}\n\n"
            elif event["type"] == "done":
                yield "data: [DONE]\n\n"
                break
        
        # 记录用量
        response_time_ms = (time.time() - start_time) * 1000
        UsageTracker.record_usage(
            db=db,
            user_id=user_id,
            api_key_id=api_key_id,
            upstream_key_id=upstream_key_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            response_status=response_status,
            response_time_ms=response_time_ms,
            client_ip=client_ip,
            user_agent=user_agent,
            request_body=request_body_str,
            error_type=error_type,
            error_message=error_message
        )
        
        # 更新上游密钥状态
        if error_occurred:
            KeyPoolService.record_failure(db, upstream_key_id, error_type or "unknown")
        else:
            KeyPoolService.record_success(db, upstream_key_id, total_tokens)
            
    except Exception as e:
        logger.error(f"Stream error: {e}")
        error_occurred = True
        error_type = "stream_error"
        error_message = str(e)
        response_status = 500
        
        # 记录错误
        response_time_ms = (time.time() - start_time) * 1000
        UsageTracker.record_usage(
            db=db,
            user_id=user_id,
            api_key_id=api_key_id,
            upstream_key_id=upstream_key_id,
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            response_status=response_status,
            response_time_ms=response_time_ms,
            client_ip=client_ip,
            user_agent=user_agent,
            request_body=request_body_str,
            error_type=error_type,
            error_message=error_message
        )
        KeyPoolService.record_failure(db, upstream_key_id, error_type)


async def handle_non_streaming(
    client: UpstreamClient,
    request_data: dict,
    db: Session,
    user_id: int,
    api_key_id: int,
    upstream_key_id: int,
    model: str,
    client_ip: Optional[str],
    user_agent: Optional[str],
    request_body_str: Optional[str],
    start_time: float
):
    """处理非流式响应"""
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    response_status = 200
    error_type = None
    error_message = None
    result = None
    
    try:
        async for event in client.chat_completions(**request_data):
            if event["type"] == "error":
                response_status = event.get("status_code", 500)
                error_type = "upstream_error"
                error_message = str(event.get("error", "Unknown error"))
                raise HTTPException(
                    status_code=response_status,
                    detail=error_message
                )
            elif event["type"] == "complete":
                result = event["data"]
                if "usage" in result:
                    usage = result["usage"]
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
        
        # 记录用量
        response_time_ms = (time.time() - start_time) * 1000
        UsageTracker.record_usage(
            db=db,
            user_id=user_id,
            api_key_id=api_key_id,
            upstream_key_id=upstream_key_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            response_status=response_status,
            response_time_ms=response_time_ms,
            client_ip=client_ip,
            user_agent=user_agent,
            request_body=request_body_str,
            error_type=error_type,
            error_message=error_message
        )
        
        # 更新上游密钥状态
        KeyPoolService.record_success(db, upstream_key_id, total_tokens)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Non-streaming error: {e}")
        error_type = "request_error"
        error_message = str(e)
        response_status = 500
        
        # 记录错误
        response_time_ms = (time.time() - start_time) * 1000
        UsageTracker.record_usage(
            db=db,
            user_id=user_id,
            api_key_id=api_key_id,
            upstream_key_id=upstream_key_id,
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            response_status=response_status,
            response_time_ms=response_time_ms,
            client_ip=client_ip,
            user_agent=user_agent,
            request_body=request_body_str,
            error_type=error_type,
            error_message=error_message
        )
        KeyPoolService.record_failure(db, upstream_key_id, error_type)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
