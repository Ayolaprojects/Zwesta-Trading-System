import socket
for port in [3389, 22, 5985, 5986]:
    s = socket.socket()
    s.settimeout(3)
    r = s.connect_ex(('148.113.5.39', port))
    status = 'OPEN' if r == 0 else 'CLOSED'
    print('Port', port, ':', status)
    s.close()
