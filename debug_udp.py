import socket
import json

UDP_IP = "127.0.0.1"
UDP_PORT = 9999  # Certifique-se de que bate com o que o outro script usa

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"🟢 A escutar em {UDP_IP}:{UDP_PORT}... (CTRL+C para parar)")

try:
    while True:
        data, addr = sock.recvfrom(1024)  # buffer de 1024 bytes
        try:
            message = json.loads(data.decode("utf-8"))
            print(f"📩 Recebido de {addr}: {message}")
        except json.JSONDecodeError:
            print(f"❌ Mensagem inválida de {addr}: {data}")
except KeyboardInterrupt:
    print("\n🛑 Encerrado pelo utilizador.")
finally:
    sock.close()
