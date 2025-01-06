#!/usr/bin/python3
import sys
import os
import logging
LOG_FILE = '/var/log/openvpn/openvpn_client_connects.log'

# Инициируем логирование
logging.basicConfig(level=logging.INFO, filename=LOG_FILE, filemode="a", format="%(asctime)s %(levelname)s %(message)s",force=True)
# Из переменных окружения получаем имя пользователя
username = os.getenv('common_name')
trusted_ip = os.getenv('trusted_ip')
bytes_received = os.getenv('bytes_received')
bytes_sent = os.getenv('bytes_sent')
ifconfig_local = os.getenv('ifconfig_local')
time_duration = os.getenv('time_duration')

logging.info(f"Disconnected session '{username}' ip: {ifconfig_local}, remote ip: {trusted_ip}, time duration: {time_duration} sec, bytes recieved: {bytes_received}, bytes sent: {bytes_sent}")


