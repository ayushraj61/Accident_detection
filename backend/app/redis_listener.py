import asyncio
import json
import httpx
import os

async def listen_to_redis():
    """Listens to Redis PubSub for accident alerts and forwards them to the API."""
    try:
        import redis.asyncio as redis
        
        # Fallback to localhost if not running inside Docker
        redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")
        r = redis.Redis.from_url(redis_url, decode_responses=True)
        
        async with r.pubsub() as pubsub:
            await pubsub.subscribe("emergency_alerts")
            print(f"[Backend] Successfully subscribed to Redis stream at {redis_url}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        print(f"[Backend] Alert received: {data['id']}")
                        
                        async with httpx.AsyncClient() as client:
                            await client.post("http://localhost:8000/api/v1/emergency/alert", json=data)
                    except Exception as e:
                        print(f"[Backend Redis Listener] Error processing message: {e}")

    except Exception as e:
        print(f"[Backend Redis Listener Critical Error]: {e}")
