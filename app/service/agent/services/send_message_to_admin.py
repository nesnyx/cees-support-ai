from typing import Any, Dict
import aiohttp
import asyncio
import logging
import json
import textwrap

logger = logging.getLogger(__name__)


async def send_message_to_admin_service_async(message: str) -> Dict[str, str]:
    """
    Async version dengan JSON format
    """
    try:
        url = "http://arisbara.cloud:3414/send-message"
        payload = {
            "session_id": "edb0439d-2bb2-44fd-94b7-272c2a166506",
            "to": "082157704435",
            "message": textwrap.dedent(message),
        }
        logger.info(f"🚀 Sending async JSON payload: {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CEES-AI-Agent/1.0",
                },
            ) as response:
                logger.info(f"📊 Status: {response.status}")
                if response.status == 200:
                    try:
                        result = await response.json()
                        logger.info(f"✅ Success: {result}")
                        return {"success": True, "result": result}
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        logger.info(f"✅ Success (non-JSON): {text}")
                        return {
                            "success": True,
                            "result": {"message": "sent", "response": text},
                        }
                else:
                    text = await response.text()
                    logger.error(f"❌ HTTP {response.status}: {text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response": text,
                    }

    except asyncio.TimeoutError:
        logger.error("⏰ Request timeout")
        return {"success": False, "error": "timeout"}
    except aiohttp.ClientError as e:
        logger.error(f"📡 Client error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return {"success": False, "error": str(e)}


async def send_image_to_admin_service_async(caption: str, image_url : str) -> Dict[str, str]:
    """
    Async version dengan JSON format
    """
    try:
        url = "http://arisbara.cloud:3414/send-image"
        payload = {
            "session_id": "edb0439d-2bb2-44fd-94b7-272c2a166506",
            "to": "120363398210860666@g.us",
            "image_url" : image_url,
            "caption": caption,
        }
        logger.info(f"🚀 Sending async JSON payload: {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "CEES-AI-Agent/1.0",
                },
            ) as response:
                logger.info(f"📊 Status: {response.status}")
                if response.status == 200:
                    try:
                        result = await response.json()
                        logger.info(f"✅ Success: {result}")
                        return {"success": True, "result": result}
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        logger.info(f"✅ Success (non-JSON): {text}")
                        return {
                            "success": True,
                            "result": {"message": "sent", "response": text},
                        }
                else:
                    text = await response.text()
                    logger.error(f"❌ HTTP {response.status}: {text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response": text,
                    }

    except asyncio.TimeoutError:
        logger.error("⏰ Request timeout")
        return {"success": False, "error": "timeout"}
    except aiohttp.ClientError as e:
        logger.error(f"📡 Client error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return {"success": False, "error": str(e)}



# async def run_service_async():
#     result = await send_message_to_admin_service_async("Test async dengan JSON")
#     print(f"Async result: {result}")

# asyncio.run(run_service_async())
