#!/usr/bin/env python3
import paramiko
import yaml
import json
import requests
import uuid
# Скрипт обновляет графики в дашборде grafana. При появлении нового пользователя создается новый график. Скрипт закускается по крону. Графики удаляются ручками

# Параметры подключения
hostname = '<HOSTNAME>'  # Хост
username = 'user'  # Ваше имя пользователя на удаленной системе
key_file = '/home/user/.ssh/id_rsa'  # Путь к вашему приватному SSH ключу
remote_file_path = '/<PATH>/config.yaml'  # Путь к файлу на удаленном хосте

# Конфигурация API Grafana
grafana_host = 'GRAFANA_HOST:3000'
api_token = '<TOKEN>'  # Ваш токен API
dashboard_uid = '<DASHBOARD_ID>'  # UID вашего существующего дашборда ("VPN sessions")
dst_host = '172.18.10.15'  # Новый хост для отслеживания


# Создаем SSH клиент
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Загружаем приватный ключ
    key = paramiko.RSAKey.from_private_key_file(key_file)
    
    # Подключаемся к удаленному хосту
    ssh.connect(hostname, username=username, pkey=key)

    # Выполняем команду для чтения файла
    stdin, stdout, stderr = ssh.exec_command(f'cat {remote_file_path}')
    
    # Читаем содержимое файла
    yaml_content = stdout.read().decode('utf-8')
    
    # Преобразуем YAML в Python-словарь
    data = yaml.safe_load(yaml_content)

    # Получение существующего дашборда
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(f'http://{grafana_host}/api/dashboards/uid/{dashboard_uid}', headers=headers)

    if response.status_code != 200:
        print("Ошибка при получении дашборда:", response.status_code, response.text)
        exit(1)

    existing_dashboard = response.json()['dashboard']  # Извлекаем дашборд из ответа

    # Проходим по всем пользователям в YAML
    for user in data:
        user_name = user
        user_ip = data[user]["ip_address"]

        # Проверка на существование графика для данного пользователя
        if any(panel['title'] == f"Traffic {user_name} ({user_ip})" for panel in existing_dashboard["panels"]):
            print(f"График для пользователя '{user_name}' ({user_ip}) уже существует, пропуск...")
            continue  # Пропустите создание графика для этого пользователя

        # Создание нового графика для dst_host
        new_panel = {
            "datasource": {
                "type": "grafana-postgresql-datasource",
                "uid": "ddwcr8beifklcb"  # UID вашего источника данных
            },
            "fieldConfig": {
                "defaults": {
                    "color": {
                        "mode": "palette-classic"
                    },
                    "custom": {
                        "axisBorderShow": False,
                        "axisCenteredZero": False,
                        "axisColorMode": "text",
                        "axisLabel": "",
                        "axisPlacement": "auto",
                        "barAlignment": 0,
                        "barWidthFactor": 0.6,
                        "drawStyle": "line",
                        "fillOpacity": 55,
                        "gradientMode": "none",
                        "hideFrom": {
                            "legend": False,
                            "tooltip": False,
                            "viz": False
                        },
                        "insertNulls": False,
                        "lineInterpolation": "smooth",
                        "lineWidth": 2,
                        "pointSize": 5,
                        "scaleDistribution": {
                            "type": "linear"
                        },
                        "showPoints": "auto",
                        "spanNulls": False,
                        "stacking": {
                            "group": "A",
                            "mode": "none"
                        },
                        "thresholdsStyle": {
                            "mode": "off"
                        }
                    },
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {
                                "color": "green",
                                "value": None
                            },
                            {
                                "color": "red",
                                "value": 80
                            }
                        ]
                    },
                    "unit": "decbytes"  # Единицы, которые необходимо отобразить
                },
                "overrides": []
            },
            "gridPos": {
                "h": 6,
                "w": 24,
                "x": 0,
                "y": len(existing_dashboard['panels']),  # Устанавливаем y в конец списка панелей
            },
            "id": len(existing_dashboard['panels']) + 1,  # Уникальный ID на основе количества панелей
            "options": {
                "legend": {
                    "calcs": [
                        "mean",
                        "max"
                    ],
                    "displayMode": "list",
                    "placement": "bottom",
                    "showLegend": True
                },
                "tooltip": {
                    "mode": "single",
                    "sort": "none"
                }
            },
            "targets": [
                {
                    "datasource": {
                        "type": "grafana-postgresql-datasource",
                        "uid": "ddwcr8beifklcb"
                    },
                    "editorMode": "code",
                    "format": "table",
                    "rawQuery": True,
                    "rawSql": f"select time, sum(octets) from ingress_octets_by_dst where dst_host = '{user_ip}' and time >= now() - interval '6 hours' group by time order by time;",
                    "refId": "A"
                }
            ],
            "title": f"Traffic {user_name} ({user_ip})",  # Название графика с учетом нового хоста
            "type": "timeseries"
        }

        # Добавляем новый график в панели
        existing_dashboard["panels"].append(new_panel)

    # Подготовка итогового JSON для запроса на обновление
    update_payload = {
        "dashboard": existing_dashboard,
        "folderId": 0,  # Установите в 0, если хотите сохранить в корневой папке
        "overwrite": True  # Установите, если хотите перезаписать существующий дашборд
    }

    # Отправка запроса на обновление дашборда
    response = requests.post(f'http://{grafana_host}/api/dashboards/db', headers=headers, json=update_payload)

    # Проверка результата
    if response.status_code == 200:
        print("Графики успешно добавлены в дашборд.")
    else:
        print("Ошибка при добавлении графиков в дашборд:", response.status_code, response.text)
        print("Отправленный JSON:", json.dumps(update_payload, indent=2))

except Exception as e:
    print(f"Error: {e}")

finally:
    # Закрываем соединение
    ssh.close()

