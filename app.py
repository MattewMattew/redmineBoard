from flask import Flask, render_template, jsonify, request
import math
import requests
import json
import calendar
from datetime import datetime, timedelta
import os

app = Flask(__name__)

redmine_url = "https://helpdesk.fenix-it.ru/"
tracker_url = "https://tracker.fenix-it.ru/"

# Проверка существования файлов с ключами
def check_api_keys():
    helpdesk_exists = os.path.exists("helpdesk_key.txt")
    tracker_exists = os.path.exists("tracker_key.txt")
    
    helpdesk_key = ""
    tracker_key = ""
    
    if helpdesk_exists:
        with open("helpdesk_key.txt", "r") as f:
            helpdesk_key = f.read().strip()
    
    if tracker_exists:
        with open("tracker_key.txt", "r") as f:
            tracker_key = f.read().strip()
    
    return helpdesk_key, tracker_key, helpdesk_exists, tracker_exists

# Получаем ключи из файлов (если они существуют)
api_key, api_key_tracker, _, _ = check_api_keys()

users = [369, 338, 207, 84, 86, 14, 83, 73, 164, 21, 38]
statuses_ids = [1, 4, 8, 9, 10, 11, 12, 13, 27, 15, 16, 23, 24, 25, 26, 28, 29, 30, 31, 33, 34, 35, 36, 37, 38, 39]
project_ids = "50"

@app.route('/')
def load():
    return render_template('load.html')

# Новый endpoint для проверки ключей
@app.route('/check-api-keys')
def check_keys():
    _, _, helpdesk_exists, tracker_exists = check_api_keys()
    return jsonify({
        'helpdesk_exists': helpdesk_exists,
        'tracker_exists': tracker_exists
    })

# Новый endpoint для сохранения ключей
@app.route('/save-api-keys', methods=['POST'])
def save_keys():
    try:
        data = request.get_json()
        
        # Сохраняем ключ Helpdesk, если он предоставлен
        if 'helpdesk_key' in data and data['helpdesk_key']:
            with open("helpdesk_key.txt", "w") as f:
                f.write(data['helpdesk_key'])
            global api_key
            api_key = data['helpdesk_key']
        
        # Сохраняем ключ Tracker, если он предоставлен
        if 'tracker_key' in data and data['tracker_key']:
            with open("tracker_key.txt", "w") as f:
                f.write(data['tracker_key'])
            global api_key_tracker
            api_key_tracker = data['tracker_key']
        
        return jsonify({'success': True, 'message': 'Ключи успешно сохранены'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/report')
def index():
    issues_per_user = []
    issues_per_open = {}
    issues_current_open = []
    issues_per_last_week_closed = []
    issues_per_last_week_open = 0
    tickets_per_last_week_closed = []
    tickets_data_on_week = {}
    users_info = []
    headers = {
        "Content-Type": "application/json",
        "X-Redmine-API-Key": api_key
    }
    
    # Создаем заголовки для трекера только если есть API-ключ
    headers_tracker = None
    if api_key_tracker:
        headers_tracker = {
            "Content-Type": "application/json",
            "X-Redmine-API-Key": api_key_tracker
        }
    
    today = datetime.today().date()
    week_ago = today - timedelta(weeks=1)

    cal = calendar.Calendar()
    dates_in_month = cal.monthdatescalendar(week_ago.year, week_ago.month) 
    
    dates = []
    for date_list in dates_in_month:
        if week_ago in date_list:
            for date_on_week in date_list:
                dates.append(date_on_week)

    url = f"{redmine_url}/issues.json?status_id=open&limit=100"
    response = requests.get(url, headers=headers) 

    if response.status_code == 200:
        root = response.json()
        print(f"test {root['total_count']}") 
        if math.ceil(root['total_count'] / 100) > 1:
            for i in range(2, math.ceil(root['total_count'] / 100) + 1):
                url_page = f"{url}&page={i}"
                response_page = requests.get(url_page, headers=headers)
                root['issues'].extend(response_page.json()['issues'])
        for issue in root['issues']:
            status_name = issue['status']['name']
            if status_name in issues_per_open:
                issues_per_open[status_name] += 1
            else:
                issues_per_open[status_name] = 1
            issues_current_open.append({
                'id': issue['id'],
                'priority': issue['priority']['id'],
                'subject': issue['subject'],
                'assigned_to': issue['assigned_to']['name'] if 'assigned_to' in issue else '-',
                'status': status_name,
                'project': issue['project']
            })
    url = f"{redmine_url}/issues.json?created_on=%3E%3C{dates[0]}|{dates[6]}&status_id=*&limit=100&sort=created_on"
    response = requests.get(url, headers=headers)
    root = response.json()
    if math.ceil(root['total_count'] / 100) > 1:
        for i in range(2, math.ceil(root['total_count'] / 100) + 1):
            url_page = f"{url}&page={i}"
            response_page = requests.get(url_page, headers=headers)
            root['issues'].extend(response_page.json()['issues'])
    for issue in root['issues']:
        if issue['status']['id'] in statuses_ids:
            issues_per_last_week_closed.append(issue)
        else:
            issues_per_last_week_open += 1
        day_on_week = ""
        if datetime.fromisoformat(issue['created_on']).strftime("%Y-%m-%d") == dates[0].strftime("%Y-%m-%d"):
            day_on_week = "Понедельник"
        elif datetime.fromisoformat(issue['created_on']).strftime("%Y-%m-%d") == dates[1].strftime("%Y-%m-%d"):
            day_on_week = "Вторник"
        elif datetime.fromisoformat(issue['created_on']).strftime("%Y-%m-%d") == dates[2].strftime("%Y-%m-%d"):
            day_on_week = "Среда"
        elif datetime.fromisoformat(issue['created_on']).strftime("%Y-%m-%d") == dates[3].strftime("%Y-%m-%d"):
            day_on_week = "Четверг"
        elif datetime.fromisoformat(issue['created_on']).strftime("%Y-%m-%d") == dates[4].strftime("%Y-%m-%d"):
            day_on_week = "Пятница"
        elif datetime.fromisoformat(issue['created_on']).strftime("%Y-%m-%d") == dates[5].strftime("%Y-%m-%d"):
            day_on_week = "Суббота"
        elif datetime.fromisoformat(issue['created_on']).strftime("%Y-%m-%d") == dates[6].strftime("%Y-%m-%d"):
            day_on_week = "Воскресенье"
        if day_on_week in tickets_data_on_week.keys():
            tickets_data_on_week.update({
                day_on_week: tickets_data_on_week.get(day_on_week) + 1
            })
        else:
            tickets_data_on_week.update({
                day_on_week: 1
            })
    url = f"{redmine_url}/issues.json?closed_on=%3E%3C{dates[0]}|{dates[6]}&status_id=closed&limit=100"
    response = requests.get(url, headers=headers)
    root = response.json()
    if math.ceil(root['total_count'] / 100) > 1:
        for i in range(2, math.ceil(root['total_count'] / 100) + 1):
            url_page = f"{url}&page={i}"
            response_page = requests.get(url_page, headers=headers)
            root['issues'].extend(response_page.json()['issues'])
    for issue in root['issues']:
        tickets_per_last_week_closed.append(issue)
    for user_id in users:
        url_users = f"{redmine_url}/users/{user_id}.json"
        response_users = requests.get(url_users, headers=headers)
        root_users = response_users.json()
        count_tickets = 0
        time_user = 0
        time_user_tracker = 0
        current_tickets = 0
        url_assigned_issues = f"{redmine_url}/issues.json?assigned_to_id={user_id}"
        response_assigned_issues = requests.get(url_assigned_issues, headers=headers)
        root_assigned_issues = response_assigned_issues.json()
        current_tickets = len(root_assigned_issues['issues'])
        url_time_entries = f"{redmine_url}/time_entries.json?spent_on=%3E%3C{dates[0]}|{dates[6]}&user_id={user_id}&limit=100"
        response_time_entries = requests.get(url_time_entries, headers=headers)
        root_time_entries = response_time_entries.json()
        if math.ceil(root_time_entries['total_count'] / 100) > 1:
            for i in range(2, math.ceil(root_time_entries['total_count'] / 100) + 1):
                url_time_entries_page = f"{url_time_entries}&page={i}"
                response_time_entries_page = requests.get(url_time_entries_page, headers=headers)
                root_time_entries['time_entries'].extend(response_time_entries_page.json()['time_entries'])
        for time in root_time_entries['time_entries']:
            time_user += float(time['hours'])
        
        # Добавляем время из трекера только если есть API-ключ и headers_tracker
        user_tracker_id = {
            369: 224,
            338: 211,
            207: 189,
            84: 91,
            86: 109,
            14: 14,
            83: 101,
            73: 86,
            164: 268
        }.get(user_id, None)
        
        if user_tracker_id and headers_tracker:
            try:
                url_time_entries_tracker = f"{tracker_url}/time_entries.json?spent_on=%3E%3C{dates[0]}|{dates[6]}&user_id={user_tracker_id}&limit=100"
                response_time_entries_tracker = requests.get(url_time_entries_tracker, headers=headers_tracker)
                
                if response_time_entries_tracker.status_code == 200:
                    root_time_entries_tracker = response_time_entries_tracker.json()
                    if math.ceil(root_time_entries_tracker['total_count'] / 100) > 1:
                        for i in range(2, math.ceil(root_time_entries_tracker['total_count'] / 100) + 1):
                            url_time_entries_tracker_page = f"{url_time_entries_tracker}&page={i}"
                            response_time_entries_tracker_page = requests.get(url_time_entries_tracker_page, headers=headers_tracker)
                            if response_time_entries_tracker_page.status_code == 200:
                                root_time_entries_tracker['time_entries'].extend(response_time_entries_tracker_page.json()['time_entries'])
                    for time in root_time_entries_tracker.get('time_entries', []):
                        time_user_tracker += float(time['hours'])
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при запросе к трекеру для пользователя {user_id}: {e}")
        
        url_closed_issues = f"{redmine_url}/issues.json?closed_on=%3E%3C{dates[0]}|{dates[6]}&cf_36={user_id}&status_id=closed&limit=100"
        response_closed_issues = requests.get(url_closed_issues, headers=headers)
        root_closed_issues = response_closed_issues.json()
        if response_closed_issues.status_code == 200 and response_users.status_code == 200:
            if math.ceil(root_closed_issues['total_count'] / 100) > 1:
                for i in range(2, math.ceil(root_closed_issues['total_count'] / 100) + 1):
                    url_closed_issues_page = f"{url_closed_issues}&page={i}"
                    response_closed_issues_page = requests.get(url_closed_issues_page, headers=headers)
                    root_closed_issues['issues'].extend(response_closed_issues_page.json()['issues'])
            count_tickets = len(root_closed_issues['issues'])
            for issue in root_closed_issues['issues']:
                issues_per_user.append({
                    'id': issue['id'],
                    'priority': issue['priority']['id'],
                    'subject': issue['subject'],
                    'assigned_to_id': issue['assigned_to']['id'] if 'assigned_to' in issue else None,
                    'custom_fields': issue['custom_fields'],
                })
        users_info.append({
            'id': root_users['user']['id'],
            'firstname': root_users['user']['firstname'],
            'lastname': root_users['user']['lastname'],
            'count_tickets': count_tickets,
            'time_entries': time_user + time_user_tracker,
            'current_tickets_count': current_tickets
        })
    return render_template('index.html', users=users_info, issues=issues_per_user,
                           issues_per_open=issues_per_open,
                           issues_per_last_week_closed=issues_per_last_week_closed,
                           tickets_per_last_week_closed=tickets_per_last_week_closed,
                           issues_open=len(issues_per_open),
                           issues_open_count=issues_per_last_week_open,
                           tickets_closed=len(tickets_per_last_week_closed),
                           issues_closed=len(issues_per_last_week_closed),
                           issues_current_open=issues_current_open,
                           tickets_data_on_week=tickets_data_on_week)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')