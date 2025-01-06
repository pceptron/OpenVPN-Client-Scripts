#!/usr/bin/python3

import sys
import os
from ruamel.yaml import YAML
import ipaddress
import logging

DIR = '/etc/openvpn/scripts'
PUSH_IPTVP = '/configs/subnets_iptv+'
PUSH_DEFAULT = '/configs/subnets_default'
CONFIG_PATH = DIR + '/configs/config.yaml'
LOG_FILE = '/var/log/openvpn/openvpn_client_connects.log'
config = []


def validate_username(user_name):
    """ Проверяем username на корректность """
    if not user_name or '/' in user_name or ' ' in user_name:
        raise ValueError(f"Некорректное имя пользователя: {user_name}")

def read_yaml(config_path):
    """ Считываем конфиг """
    yaml = YAML()
    with open(config_path, "r", encoding="utf-8") as file:
        data = yaml.load(file)
    return data, yaml

def add_to_yaml(config_path, default_user_config):
    """ Добавляем новый бок данных """
    data, yaml = read_yaml(config_path)
    if not isinstance(data, dict):
        raise ValueError("Конфигурация должна быть словарем (YAML с корневым объектом dict).")

    # Добавляем новый блок
    data.update(default_user_config)

    # Перезаписываем файл с сохранением структуры и комментариев
    with open(config_path, "w", encoding="utf-8") as file:
        yaml.dump(data, file)

def read_routes(file_path):
    """ Считываем профили маршрутов из файла с профилями """
    with open(file_path, 'r') as file:
        return [line.rstrip() for line in file if line.startswith('push')]


def push_routes (user_name = 'default', config = 'NONE'):
   """ Формируем список push команд, которые передаются на сторону клиента,
       конфигурации пользователей хранятся в файле DIR+CONFIG_PATH.
       Cтруктура файла конфигураци представляет из себя yaml записи вида:
       user1:
  	ip_address: 172.18.30.10
  	vpn_rights: iptv+
       user2:
        vpn_rights: default
       ...
       При появлении нового авторизованного пользовате, для которого нет конфигурации
       Создается новая шаблонная конфигурация. Пользователю присваивается ip address = 
       mar(ip address) +1, Права устанавливаются в соответствии с профилем iptv+
       Обновленная конфигурация записывается в конфигурационный файл 

   """
   output = []
   if user_name in config:
      if 'vpn_rights' not in config[user_name]:
         raise KeyError(f"'vpn_rights' отсутствует у пользователя {user_name}")
      match config[user_name]['vpn_rights']:
           case 'iptv+': # Выдаем в сорону клиента набор маршрутов для youtube, онлайн кино-сервисов и соц сетей.
             # Выдаем директивы клиенту
             output = read_routes(DIR + PUSH_IPTVP)
             # Выдаем адрес клиенту
             if config[user_name]['ip_address']:
                output.append(f'ifconfig-push {config[user_name]["ip_address"]} 255.255.255.0')
             return output
           case 'default': # Выдаем шлюз по умолчанию
             # Выдаем директивы клиенту
             output = read_routes(DIR + PUSH_DEFAULT)
             # Выдаем адрес клиенту
             if config[user_name]['ip_address']:
                output.append(f'ifconfig-push {config[user_name]["ip_address"]} 255.255.255.0')
             return output
           case 'reject': # Профиль для отключенных пользователей
             # Выдаем директивы клиенту
                logging.info(f"Rejected session for '{user_name}'. Rights revoked!")
                sys.exit(1)
           case 'personal': # Персональный шаблон маршрутов
             # Выдаем директивы клиенту
             output = read_routes(DIR + "/configs/" + config[user_name]["push_file"])
             # Выдаем адрес клиенту
             if config[user_name]['ip_address']:
                output.append(f'ifconfig-push {config[user_name]["ip_address"]} 255.255.255.0')
             return output
           case _:
             print ("Неизвестный тип данных")
             return
   else:
      # Для пользователя отсутствует конфигурация, добавляем. IP = MAX(IP)+1
      ip_addresses = [entry['ip_address'] for entry in config.values() if 'ip_address' in entry]
      ip_objects = [ipaddress.IPv4Address(ip) for ip in ip_addresses]
      max_ip = max(ip_objects)
      new_ip = max_ip + 1
      default_user_config = {
          user_name: {
             "ip_address": str(new_ip),
             "vpn_rights": "iptv+",
             "vpn_logs" : "yes"
              }
          }
      add_to_yaml(CONFIG_PATH, default_user_config)

if __name__ == "__main__":
    # Инициируем логирование
    logging.basicConfig(level=logging.INFO, filename=LOG_FILE, filemode="a", format="%(asctime)s %(levelname)s %(message)s",force=True)
    try:
       # Считываем конфигурации пользователей
       config, yaml = read_yaml(CONFIG_PATH)

       # Из переменных окружения получаем имя пользователя
       user_name = os.getenv('common_name')

       validate_username(user_name)

       trusted_ip = os.getenv('trusted_ip')
       # Получаем директивы для пользователя
       directives = push_routes(user_name, config)
       # Передаем push-команды для передачи маршрута
       with open(sys.argv[1], "a") as file:
          for command in directives:
             file.write(f"{command}\n")
       logging.info(f"Established session '{user_name}' ip: {config[user_name]['ip_address']} profile: {config[user_name]['vpn_rights']} from {trusted_ip}")

    except KeyError as ke:
        logging.error(f"Ошибка в конфигурации: {ke}")
        sys.exit(1)
    except Exception as e:
        logging.exception("Неизвестная ошибка:")
        sys.exit(1)

