"""
Anthropic 端点 流式/非流式 大输入大输出测试
"""
import asyncio
import aiohttp
import json
import time

BASE_URL = "https://anti-ts.zeabur.app"
API_KEY = "sk-antigravity-924e62942f5140819579feba416203d8"
MODEL = "claude-opus-4-6-thinking"

# 大输入 prompt（约 500+ tokens）
BIG_PROMPT = """You are a senior software engineer. Please write a detailed, comprehensive guide about building a production-ready REST API using Rust with the Axum framework. Your guide should cover ALL of the following topics in depth:

1. Project setup and Cargo.toml configuration with all necessary dependencies
2. Router setup with nested routes, path parameters, and query parameters
3. Middleware implementation (logging, authentication, CORS, rate limiting)
4. Database integration with SQLx and connection pooling
5. Error handling with custom error types and proper HTTP status codes
6. Request validation and serialization/deserialization with serde
7. Authentication using JWT tokens with refresh token rotation
8. WebSocket support for real-time features
9. Graceful shutdown handling
10. Docker deployment configuration

For each topic, provide complete, compilable code examples with detailed comments explaining every line. Make the guide at least 2000 words long. Include best practices and common pitfalls to avoid."""


async def test_non_streaming():
    """测试 1: 非流式请求（大输入 + 大输出）"""
    print("=" * 70)
    print("  测试 1: 非流式 Anthropic 请求")
    print("=" * 70)

    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": BIG_PROMPT}],
        "max_tokens": 4096,
        "stream": False,
    }

    t0 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/v1/messages",
            json=body,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=300),
        ) as resp:
            status = resp.status
            data = await resp.json()
            elapsed = time.perf_counter() - t0

    model_returned = data.get("model", "N/A")
    stop_reason = data.get("stop_reason", "N/A")
    content_blocks = data.get("content", [])
    full_text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
    est_input_tokens = len(BIG_PROMPT) // 4
    est_output_tokens = len(full_text) // 4

    print(f"  HTTP 状态:     {status}")
    print(f"  返回 model:    {model_returned}")
    ok = "✅" if model_returned == MODEL else "❌ 不匹配!"
    print(f"  model 匹配:    {ok}")
    print(f"  stop_reason:   {stop_reason}")
    print(f"  输入 tokens:   ~{est_input_tokens}")
    print(f"  输出 tokens:   ~{est_output_tokens}")
    print(f"  输出字符数:    {len(full_text)}")
    print(f"  总耗时:        {elapsed:.1f}s")
    print(f"  内容预览:      {full_text[:120]}...")
    print()
    return model_returned == MODEL


async def test_streaming():
    """测试 2: 流式请求（大输入 + 大输出）"""
    print("=" * 70)
    print("  测试 2: 流式 Anthropic 请求")
    print("=" * 70)

    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": BIG_PROMPT}],
        "max_tokens": 4096,
        "stream": True,
    }

    t0 = time.perf_counter()
    ttfb = None
    full_text = ""
    chunk_count = 0
    model_returned = None
    stop_reason = None

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/v1/messages",
            json=body,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=300),
        ) as resp:
            status = resp.status
            buffer = ""
            async for raw in resp.content.iter_any():
                if ttfb is None:
                    ttfb = (time.perf_counter() - t0) * 1000

                text = raw.decode("utf-8", errors="ignore")
                buffer += text

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload == "[DONE]":
                        continue
                    try:
                        evt = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    chunk_count += 1
                    evt_type = evt.get("type", "")

                    if evt_type == "message_start":
                        msg = evt.get("message", {})
                        model_returned = msg.get("model")

                    elif evt_type == "content_block_delta":
                        delta = evt.get("delta", {})
                        if delta.get("type") == "text_delta":
                            full_text += delta.get("text", "")

                    elif evt_type == "message_delta":
                        delta = evt.get("delta", {})
                        stop_reason = delta.get("stop_reason")

    elapsed = time.perf_counter() - t0
    est_input_tokens = len(BIG_PROMPT) // 4
    est_output_tokens = len(full_text) // 4

    print(f"  HTTP 状态:     {status}")
    print(f"  返回 model:    {model_returned or 'N/A (流式无 model)'}")
    print(f"  stop_reason:   {stop_reason or 'N/A'}")
    print(f"  SSE chunks:    {chunk_count}")
    print(f"  TTFB:          {ttfb:.0f}ms" if ttfb else "  TTFB:          N/A")
    print(f"  输入 tokens:   ~{est_input_tokens}")
    print(f"  输出 tokens:   ~{est_output_tokens}")
    print(f"  输出字符数:    {len(full_text)}")
    print(f"  总耗时:        {elapsed:.1f}s")
    print(f"  内容预览:      {full_text[:120]}...")
    print()
    return len(full_text) > 100


async def main():
    print()
    print("🔬 Anthropic 端点全面测试 (claude-opus-4-6-thinking)")
    print(f"   端点: {BASE_URL}/v1/messages")
    print()

    r1 = await test_non_streaming()
    r2 = await test_streaming()

    print("=" * 70)
    print("  测试汇总")
    print("=" * 70)
    print(f"  非流式 (大输出): {'✅ 通过' if r1 else '❌ 失败'}")
    print(f"  流式   (大输出): {'✅ 通过' if r2 else '❌ 失败'}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
