#!/usr/bin/env python3
# CS472 - Homework #3
# Edward Parrish
# ftpserver.py
#
# This module is the major module of the FTP server, with the main processing loop.

from systemhelper import System
from mylogger import Logger
import socket
import threading

global logger
open_connections = []


def main(host, port):
    '''main(host, port)
    The main processing loop of the FTP server.'''
    # Test if platform supports dualstack IPv4/6.
    if socket.has_dualstack_ipv6():
        family = socket.AF_INET6
        dualstack = True

    else:
        family = socket.AF_INET
        dualstack = False

    # Create socket that will listen for client connections.
    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    with socket.create_server((host, port), family=family, dualstack_ipv6=dualstack) as sock:
        # Bind socket.
        # sock.bind((host, port))
        logger.write_log(f'Binding to address: {host}:{port}.')

        sock.listen()
        while True:
            conn = None
            try:
                # Accept new client connection.
                conn, addr = sock.accept()
                if conn:
                    # Append connection to list of open connections.
                    open_connections.append(conn)

                    # Create and start new thread for connection with target run.
                    t = threading.Thread(target=run, args=(conn, addr,))
                    t.start()

            except KeyboardInterrupt:
                # Test if most recent connection is open but not yet add to
                # list of open connections.
                if conn and conn not in open_connections:
                    conn.close()

                # Close all connections.
                for c in open_connections:
                    c.close()

                break


def run(conn, addr):
    with conn:
        logger.write_log('Connected to new client.', addr)
        state = State()
        while True:
            # Get appropriate message from state and send to client.
            msg = state.message()
            conn.sendall(msg.encode())
            logger.write_log(f'Sent: {msg}', addr)

            # Receive client response and decode it.
            data = conn.recv(1024).decode()

            # Test if user closed connection.
            if not data:
                logger.write_log(f'Client closed connection.', addr)
                break

            logger.write_log(f'Received: {data}', addr)

            # Update state based on client response.
            state.update(data)

    # Remove connection from list of open connections.
    open_connections.remove(conn)


class State:

    def __init__(self):
        self.initialize()

    def initialize(self):
        '''initialize()
        Initializes the state to be ready for new user with default values.'''
        self.code = '220'
        self.res = 'Welcome to FTP Server.'
        self.is_logged_in = False
        self.user = ''

    def reply(self, code, message):
        '''reply(code, message)
        Sets the reply code and message.'''
        self.code = code
        self.message = message

    def message(self):
        '''message()
        Generates a message to send to a client based on current state.'''
        return f'{self.code} {self.res}\r\n'

    def update(self, response):
        '''update(response)
        Updates the current state based on a client's response.'''
        # Parse the client's response.
        command, value = self.parse(response)

        # Test if user not logged in.
        if not self.is_logged_in:
            self.login(command, value)

    def login(self, command, value):
        '''login(command, value)
        Prompts client to send USER and PASS based on current state.'''
        # Test if a username has not already been given.
        if not self.user:
            if command == 'USER':
                self.user = value
                self.reply('331', 'Please specify password.')

            elif command == 'PASS':
                self.reply('503', 'Login with USER first.')

            else:
                self.reply('530', 'Please login with USER and PASS.')
                
        else:
            if command == 'PASS':
                # Test if user and pass are correct.
                if self.credentials_correct(self.user, value):
                    self.reply('230', 'Login successful.')

                else:
                    self.user = ''
                    self.reply('530', 'Login incorrect.')

            elif command == 'USER':
                self.reply('331', 'Please specify password.')

            else:
                self.reply('530', 'Please login with USER and PASS.')

    def credentials_correct(self, user, pswd):
        '''credentials_correct(user, pswd)
        Tests if the given username and password are correct login credentials.'''
        return user == 'cs472' and pswd == 'hw2ftp'

    def parse(self, response):
        '''parse(response)
        Parses a client's response and returns the command and value. If the
        response is only whitespace then command is set to None and value to
        empty string.'''
        value = ''

        # Strip whitespace from response.
        res = response.strip()

        # Test if response is not only whitespace.
        if len(res) > 0:
            # Find index of first space in order to locate command.
            space_i = res.find(' ')

            # Test if a space was found.
            if space_i > -1:
                command = res[:space_i]

                # Test if values exist after space.
                if len(res) > space_i:
                    value = res[space_i+1:]

            else:
                command = res

        else:
            command = None

        return command, value


if __name__ == '__main__':
    # Get command line args.
    filename, port = System.args()
    host = '0.0.0.0'

    # Initialize logger with log filename and run main processing loop.
    logger = Logger(filename)
    main(host, port)
