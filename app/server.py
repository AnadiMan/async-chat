#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports

users_list = []
messages_list = []


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):

        login = data.decode()[:-2]

        if self.login is not None:
            self.send_message(login)
        else:
            if login not in users_list:
                self.login = login
                users_list.append(self.login)
                hystorys = self.send_history()
                if hystorys:
                    self.transport.write(
                        f"Последние сообщения\n".encode()
                    )

                    for hystory in hystorys:
                        self.transport.write(
                            f"{hystory}\n".encode()
                        )
                    self.transport.write(
                        f"------------------\n".encode()
                    )

                self.transport.write(
                    f"Привет, {self.login}!\n".encode()
                )
            else:
                self.transport.write(

                    f"Логин: <<{login}>> занят, попробуйте другой.\n".encode()
                )
                try:
                    self.connection_lost(login)
                except ValueError:
                    print("Занятый логин введен повторно")

    def send_history(self):
        if len(messages_list) > 0:
            return messages_list[-10:]
        else:
            return ''

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        try:
            self.server.clients.remove(self)
            print("Клиент вышел")
        except ValueError:
            print('Повторно введен имеющийся логин')

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        if message not in messages_list:
            messages_list.append(message[:-1])

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
