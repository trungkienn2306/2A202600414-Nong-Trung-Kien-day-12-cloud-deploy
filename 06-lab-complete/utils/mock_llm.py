"""
Mock LLM — không cần API key thật.
Trả lời giả lập để focus vào deployment concept.
Hỗ trợ cả call thường và streaming (SSE).
"""
import time
import random


MOCK_RESPONSES = {
    "default": [
        "Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.",
        "Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.",
        "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.",
    ],
    "docker": [
        "Container là cách đóng gói app để chạy ở mọi nơi. "
        "Docker build once, run anywhere — kernel của host được chia sẻ, "
        "image chứa app + dependencies, container chạy isolated."
    ],
    "deploy": [
        "Deployment là quá trình đưa code từ máy bạn lên server để người khác dùng được. "
        "Các bước: build image → push registry → pull trên server → run container."
    ],
    "health": ["Agent đang hoạt động bình thường. All systems operational."],
    "cloud": [
        "Cloud deployment cho phép scale horizontal — thêm instance khi traffic tăng, "
        "giảm khi thấp. Stateless design + Redis là chìa khóa để scale."
    ],
    "redis": [
        "Redis là in-memory data store dùng cho rate limiting, session, cache. "
        "Key-value, cực nhanh (~100k ops/sec), hỗ trợ expiry tự động."
    ],
    "rate": [
        "Rate limiting bảo vệ API khỏi abuse. Sliding window: đếm request trong 60s gần nhất, "
        "reject nếu vượt ngưỡng. Redis ZADD + ZCOUNT cho distributed rate limit."
    ],
    "scale": [
        "Horizontal scaling: chạy nhiều instance song song đằng sau load balancer. "
        "Yêu cầu stateless — không lưu state trong RAM của app, dùng Redis thay."
    ],
}


def ask(question: str, history: list | None = None, delay: float = 0.1) -> str:
    """Mock LLM call với delay giả lập latency thật."""
    time.sleep(delay + random.uniform(0, 0.05))

    question_lower = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in question_lower:
            return random.choice(responses)

    return random.choice(MOCK_RESPONSES["default"])


def ask_stream(question: str, history: list | None = None):
    """Mock streaming — yield từng token (word) với delay."""
    response = ask(question, history, delay=0.0)
    words = response.split()
    for word in words:
        time.sleep(0.04)
        yield word + " "
