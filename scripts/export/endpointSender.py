# ws_sender.py
import asyncio
import websockets
import json

async def send_json(data, endpoint_url="wss://signcollect.nl/unrealServer/"):
    try:
        async with websockets.connect(endpoint_url) as ws:
            payload = {
                "handler": "log",
                "data": data  # full JSON object of your log
            }
            await ws.send(json.dumps(payload))
            # Optionally wait for acknowledgment
            # response = await ws.recv()
            # print("Response:", response)
    except Exception as e:
        print("[WebSocket] send failed:", e)

def send(data, endpoint_url="wss://signcollect.nl/unrealServer/"):
    """
    Convenience wrapper so you can call this from sync code easily.
    """
    try:
        asyncio.run(send_json(data, endpoint_url))
    except RuntimeError:
        # In case an asyncio loop is already running (e.g. inside Tkinter)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(send_json(data, endpoint_url))
        else:
            raise
