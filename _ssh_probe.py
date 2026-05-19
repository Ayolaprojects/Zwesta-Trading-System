import paramiko
import socket

HOST = '148.113.5.39'
USER = 'Administrator'
PASS = 'Zwesta1985'
PORTS = [2222, 22, 2200, 2201, 2220, 2223, 50022]

for port in PORTS:
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((HOST, port))
        s.close()
        print(f'Socket connect on port {port} succeeded, trying SSH...')
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, port=port, username=USER, password=PASS, timeout=10)
        print(f'SSH connected on port {port}!')
        stdin, stdout, stderr = client.exec_command('hostname')
        print(stdout.read().decode())
        client.close()
        break
    except socket.timeout:
        print(f'Port {port}: socket timeout')
    except ConnectionRefusedError:
        print(f'Port {port}: refused')
    except Exception as e:
        print(f'Port {port}: {e}')
