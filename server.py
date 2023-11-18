from flask import Flask, request, jsonify
from flask_cors import CORS
import json


app = Flask(__name__)

CORS(app, origins="*")


@app.route("/", methods=["GET"])
def simulation():
    return


if __name__ == "__main__":
    app.run(debug=True)

