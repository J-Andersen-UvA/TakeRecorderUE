from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/convertToGLTF', methods=['POST'])
def convert_to_gltf():
    """
    Handle the export completed notification.

    Expects a JSON payload with details about the export.
    """
    if request.is_json:
        data = request.get_json()
        # Process the data as needed
        print(f"Export completed with data: {data}")
        path = data.get("path")

        # Using subprocess to run the javascript conversion script, C:\Program Files\nodejs\node.exe .\..\tools\fbx2gltf.js
        subprocess.run(["C:\\Program Files\\nodejs\\node.exe", ".\\fbx2gltf.js", path])

        # Respond with a success message
        return jsonify({"status": "success", "message": "Export completed successfully"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid input format"}), 400

if __name__ == "__main__":
    app.run(host='localhost', port=5011)
