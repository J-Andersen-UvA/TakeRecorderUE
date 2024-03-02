const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 3000 });
let intervalId;  // This will hold the interval ID for clearing it later

wss.on('connection', function connection(ws) {
  console.log('Client connected');

  // Start sending a command every 1 second when a client connects
intervalId = setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    // First, send "startrecord"
    ws.send("startrecord", function ack(error) {
      if (error) {
        console.error('Error sending "startrecord":', error);
        return;
      }
      console.log('Sent command: startrecord');
    });

    // After 5 seconds, send "stoprecord"
    setTimeout(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("stoprecord", function ack(error) {
          if (error) {
            console.error('Error sending "stoprecord":', error);
            return;
          }
          console.log('Sent command: stoprecord');
        });
      }
    }, 5000); // 5000 milliseconds = 5 seconds
  }
}, 10000); 

  ws.on('message', function incoming(message) {
    console.log('received: %s', message);
  });

  ws.on('close', function close() {
    console.log('Client disconnected');
    // Clear the interval when the client disconnects
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
});
