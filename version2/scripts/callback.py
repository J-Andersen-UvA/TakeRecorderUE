import requests
import json

class Callback:
    """
    A class to handle callback functionality for various endpoints.
    
    This class allows you to send notifications to specified Flask app endpoints
    when certain events occur.
    """

    def __init__(self, host='localhost', port=5011, endpoint='/convertToGLTF'):
        """
        Initializes the Callback instance with a host, port, and endpoint.
        
        Args:
            host (str): The host where the Flask app is running.
            port (int): The port where the Flask app is listening.
            endpoint (str): The initial endpoint for POST requests.
        """
        self._callback = None
        self.location = {"host": host, "port": port}
        self.endpoint = endpoint
        self.base_url = f"http://{self.location['host']}:{self.location['port']}{self.endpoint}"

    def change_location(self, host, port):
        """
        Change the host and port of the Flask app location.
        
        Args:
            host (str): New host address.
            port (int): New port number.
        """
        self.location = {"host": host, "port": port}
        self.base_url = f"http://{self.location['host']}:{self.location['port']}{self.endpoint}"

    def set_endpoint(self, endpoint):
        """
        Change the endpoint for POST requests.
        
        Args:
            endpoint (str): The new endpoint to send requests to.
        """
        self.endpoint = endpoint
        self.base_url = f"http://{self.location['host']}:{self.location['port']}{self.endpoint}"

    def send_message(self, handler, data):
        """
        Sends a POST request with JSON data to the Flask app.
        
        Args:
            data (dict): The data to send in the POST request.
            
        Returns:
            response (requests.Response): The response object from the Flask app.
        """
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.base_url, headers=headers, data=json.dumps({handler: data}))
        
        # Print the response status and content for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

        return response

# # Example usage
# if __name__ == "__main__":
#     # Create an instance of Callback
#     notifier = Callback(host='localhost', port=5000, endpoint='/exportCompleted')
    
#     # Send an export completed message
#     notifier.send_message({"handler": "exportCompleted"})
    
#     # Change endpoint and send a message
#     notifier.set_endpoint('/anotherEndpoint')
#     notifier.send_message({"handler": "anotherAction"})
    
#     # Change the Flask app location and endpoint, then send a message
#     notifier.change_location('localhost', 6000)
#     notifier.set_endpoint('/newEndpoint')
#     notifier.send_message({"handler": "newAction"})
