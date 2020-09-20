import logging
import pickle
import threading

from FirstTask.CustomSocket import CustomSocket
from FirstTask.MessageValidator import MessageValidator

HOST = '127.0.0.1'
PORT = 8080
HEADER_LENGTH = 10
USERS_EXPECTED_NUMBER = 10

message_validator = MessageValidator()


def main():
    server_socket = CustomSocket()
    server_socket.setsockopt()
    server_socket.bind(HOST, PORT)
    server_socket.listen(USERS_EXPECTED_NUMBER)
    print('Listening for connections...')

    connections = {}
    connecting = False

    def _connect_users():
        nonlocal connecting
        for user in range(USERS_EXPECTED_NUMBER):
            conn, addr = server_socket.accept()

            if conn not in connections:
                connections[addr] = conn
                threading.Thread(target=_send_data, args=(addr,)).start()
            connecting = True
            print(f'user with address {addr} is connected')
            connecting = False
            threading.Thread(target=_connect_users).start()

    def _send_data(user):
        while True:
            try:
                data_header, data = _receive_data(user)

                if not data_header or not data or connecting:
                    _close_user_connection(user)
                    return False

                if not message_validator.check(data):
                    print('Message is not correct')
                    connections[user].close()
                    return False

                for each in connections.values():
                    each.send(data_header + pickle.dumps(data))
            except ConnectionResetError as ex:
                logging.error(ex)
                _close_user_connection(user)
                return False

    def _close_user_connection(user):
        connections[user].close()
        print(f'user with address {user} has been disconnected')
        del connections[user]

    def _receive_data(user):
        data_header = server_socket.receive_bytes_num(HEADER_LENGTH, connections[user])
        if not data_header:
            return False, False
        data_length = int(data_header.decode('utf-8').strip())
        data = pickle.loads(server_socket.receive_bytes_num(data_length, connections[user]))
        return data_header, data

    threading.Thread(target=_connect_users).start()

    while True:
        pass


if __name__ == '__main__':
    main()
