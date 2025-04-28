from flask import Flask, render_template, jsonify
import math
import requests
import json
import calendar
from datetime import datetime, timedelta
import datetime

app = Flask(__name__)

redmine_url = "https://helpdesk.fenix-it.ru/"
tracker_url = "https://tracker.fenix-it.ru/"
with open('helpdesk_key.txt', 'r') as file:
    key_redmine = file.readlines()
with open('tracker_key.txt', 'r') as file:
    key_tracker = file.readlines()
api_key = key_redmine[0]
api_key_tracker = key_tracker[0]
users = [369, 297, 338]

statuses_ids = [1, 4, 8, 9, 10, 11, 12, 13, 27, 15, 16, 23, 24, 25, 26, 28, 29, 30, 31, 33, 34, 35, 36, 37, 38, 39]


@app.route('/')
def index():
    headers = {
        "Content-Type": "text/json",
        "X-Redmine-API-Key": api_key
    }
    url = f"{redmine_url}/issues.json?status_id=open&limit=100&project_id=49"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
            root = json.loads(response.content)
            if math.ceil(root['total_count']/100) > 1:
                for i in range(2, math.ceil(root['total_count']/100) + 1):
                    url = f"{redmine_url}/issues.json?status_id=open&page={i}&limit=100&project_id=49"
                    response = requests.get(url, headers=headers)
                    root['issues'].extend(json.loads(response.content)['issues'])
    return render_template('load.html')

if __name__ == '__main__':
    app.run(debug=True)