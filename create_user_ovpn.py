#!/usr/bin/env python3

import os
import sys
import subprocess

# Пути к сертификатам и ключам
CA_CERT = '/usr/share/easy-rsa/pki/ca.crt'
TA_KEY = '/usr/share/easy-rsa/pki/ta.key'
DH_PEM = '/usr/share/easy-rsa/pki/dh.pem'
CA_KEY = '/usr/share/easy-rsa/pki/private/ca.key'

# Функция для создания нового пользователя OpenVPN
def create_openvpn_user(username):
    # Путь к Easy-RSA для генерации сертификатов
    easyrsa_path = '/usr/share/easy-rsa'
    user_cert_dir = f'{easyrsa_path}/pki/issued/{username}.crt'
    user_key_dir = f'{easyrsa_path}/pki/private/{username}.key'
    
    # Генерация сертификатов для пользователя
    subprocess.run([f'{easyrsa_path}/easyrsa', 'gen-req', username, 'nopass'], check=True)
    subprocess.run([f'{easyrsa_path}/easyrsa', 'sign-req', 'client', username], check=True)

    # Формирование файла .ovpn
    ovpn_file = f'{username}.ovpn'
    
    with open(ovpn_file, 'w') as f:
        # Запись стандартных настроек OpenVPN
        f.write("client\n")
        f.write("dev tun\n")
        f.write("proto udp\n")
        f.write("remote <VPN SERVER IP> <PORT>\n")
        f.write("remote-cert-tls server\n")
        f.write("#comp-lzo yes\n")

        # Вставка сертификата CA
        f.write("<ca>\n")
        with open(CA_CERT, 'r') as ca_file:
            f.write(ca_file.read())
        f.write("</ca>\n")

        # Вставка сертификата пользователя
        f.write("<cert>\n")
        with open(user_cert_dir, 'r') as cert_file:
            f.write(cert_file.read())
        f.write("</cert>\n")

        # Вставка приватного ключа пользователя
        f.write("<key>\n")
        with open(user_key_dir, 'r') as key_file:
            f.write(key_file.read())
        f.write("</key>\n")

        # Вставка ключа tls-auth
        f.write("<tls-auth>\n")
        with open(TA_KEY, 'r') as ta_file:
            f.write(ta_file.read())
        f.write("</tls-auth>\n")

    print(f'Файл {ovpn_file} был успешно создан!')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Использование: python3 create_user.py <имя_пользователя>")
        sys.exit(1)

    username = sys.argv[1]
    create_openvpn_user(username)

