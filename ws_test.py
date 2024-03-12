import websocket
import ssl
import json

host = "wss://leffe.science.uva.nl:8043/unrealServer/"


def on_message(ws, message):
    print(f"Received message: {message}")


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws):
    print("Connection closed")


def on_open(ws):
    print("Connection established")
    message = "Hello, server!"
    data = json.dumps({"msg": message})
    ws.send(data)


if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        host,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )

    ws.on_open = on_open
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
