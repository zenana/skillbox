"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def send_history(self):
        for mes in self.server.story:
            self.transport.write(mes.encode())
            self.transport.write("\r\n".encode())

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                temp_login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == temp_login:
                        self.transport.write(
                             f"Логин {temp_login} занят, попробуйте другой".encode()
                            )
                        self.transport.close()
                else:
                    self.login = temp_login
                    self.send_history()
                    self.transport.write(
                    f"Привет, {self.login}!".encode()
                    )

        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.story.append(format_string)
        if len(self.server.story) > 10:
            self.server.story = self.server.story[1:]

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    story: list

    def __init__(self):
        self.clients = []
        self.story = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")


