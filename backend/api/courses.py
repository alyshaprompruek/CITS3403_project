from flask import Blueprint, jsonify
import json
import os

# print("this is a message for testing.  courses.py imported")

courses_api = Blueprint("courses_api", __name__)

@courses_api.route("/api/units", methods=["GET"])
def get_units():
    # backend/data/fake_data.json
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fake_data.json')

    with open(file_path, 'r') as f:
        data = json.load(f)

    return jsonify(data["admin"]["units"])