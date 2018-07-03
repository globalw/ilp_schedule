import socket
import time
from termcolor import colored


def client_program():
    host = socket.gethostname()  # as both code is running on same pc
    port = 5000  # socket server port number

    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    message = input(colored(" -> ",'red'))  # take input

    while message.lower().strip() != 'exit':
        try:
            client_socket.send(message.encode())  # send message
            data = client_socket.recv(1024).decode()  # receive response
            if data != '':
                print('airfraight server : ' + colored(data,'green'))  # show in terminal
                message = input(colored(" -> ",'yellow')) # enter message for server
            else:
                print('airfraight server does not answer...')
                print('reconnecting...')

                # reconnect to port
                # close broken socket
                client_socket.close()
                # initialize new socket
                client_socket = socket.socket()  # instantiate
                # connect new socket
                client_socket.connect((host, port))  # connect to the server
                time.sleep(1)

        except BrokenPipeError:
            print('reconnecting...')

            # reconnect to port
            # close broken socket
            client_socket.close()
            # initialize new socket
            client_socket = socket.socket()  # instantiate
            # connect new socket
            client_socket.connect((host, port))  # connect to the server
            time.sleep(1)
        except ConnectionRefusedError:
            print('Connection was refused. try again')

    client_socket.close()  # close the connection


if __name__ == '__main__':
    client_program()
