#!/usr/bin/env python3
# CS472 - Homework #3
# Edward Parrish
# ftpserver.py
#
# This module is the major module of the FTP server. It contains the main
# processing loop that listens for and accepts new connections. Once a
# connectionand has been accepts its control is handed off to a new thread to
# allow multiple open each accepted connection.

import util
from logger import Logger
import socket
import threading


class Server:

    def __init__(self, host, port, filename):
        self.host = host
        self.port = port
        self.logger = Logger(filename)
        self.open_connections = []

    def log(self, description, client=None):
        # Test if client was passed.
        if client is not None:
            self.logger.write(f'{client.addr_info()} {description}')
        else:
            self.logger.write(description)

    def start(self):
        '''start()
        The main processing loop of the FTP server. Creates a socket to listen
        for incomming connections. When a connection is accepted, starts a new
        thread with target set to serve_client().'''

        # Get Server family and test if it has dualstack IPv6.
        fam, has_ds = self.server_params()

        # Create socket that will listen for client connections.
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with socket.create_server((self.host, self.port), family=fam, dualstack_ipv6=has_ds) as sock:
            # Bind socket.
            # sock.bind((host, port))
            self.log(f'Binding to address: {self.host}:{self.port}.')

            sock.listen()
            while True:
                conn = None
                client = None
                try:
                    # Accept new client connection.
                    conn, addr = sock.accept()
                    if conn:
                        self.handle_connection(conn, addr)

                except KeyboardInterrupt:
                    self.handle_kboard_intr(client, conn)
                    break

    def server_params(self):
        '''server_params() -> (family, has dualstack IPv6)
        Determine if the platform supports dualstack IPv6. If it does then the
        Server family should be AF_INET6, otherwise AF_INET.'''

        if socket.has_dualstack_ipv6():
            family = socket.AF_INET6
            has_ds = True

        else:
            family = socket.AF_INET
            has_ds = False

        return family, has_ds

    def handle_kboard_intr(self, client, conn):
        '''handle_kboard_intr()
        Handle a KeyboardInterrupt that occurs while the server is listening to 
        accept new connections. Close all open connections and remove them from
        list of open connections.'''

        # Test if last connection is open but not in open list.
        if self.connection_not_in_list(conn, client):
            conn.close()
            self.log('Closing connection.', client)

        # Close all open connections.
        for c in self.open_connections:
            c.conn.close()
            self.log('Closing connection.', client)

        self.open_connections.clear()

    def connection_not_in_list(self, conn, client):
        '''connection_not_in_list(self, conn, client) -> boolean
        Test if a client connection is open but has not yet been added the the
        server's list of open client connections.'''

        if conn and client and client not in self.open_connections or conn and not client:
            return True

        return False

    def handle_connection(self, conn, addr):
        '''handle_connection(connection socket object, client address info)
        Handle a new connection accepted by server. Record the connection socket
        object and address information and add it to list of open connections.
        Pass that data off to a new thread and start it.'''

        # Create client and add to list of open connections.
        client = Connection(conn, addr)
        self.open_connections.append(client)

        # Create and start new thread to serve the client.
        t = threading.Thread(target=self.serve_client, args=(client,))
        t.start()

    def serve_client(self, client):
        '''serve_client(client)
        Provides the services of the FTP server to a client. Sends messages to
        the client based on the current state, receives client response, and
        updates the current state.'''

        with client.conn:
            self.log('Connected to new client.', client)
            while True:
                # Get appropriate reply from current state and send to client.
                msg = client.state.get_reply()
                client.conn.sendall(msg.encode())
                self.log(f'Sent: {msg}', client)

                # Receive client response and decode it.
                data = client.conn.recv(1024).decode()

                # Test if user closed connection.
                if not data:
                    self.log(f'Client closed connection.', client)
                    break

                self.log(f'Received: {data}', client)

                # Parse client response and update current state.
                command, value = self.parse_response(data)
                client.update(command, value)

        # Remove connection from list of open connections.
        self.open_connections.remove(client)

    def parse_response(self, response):
        '''parse(response) -> (command, value)
        Parses a client's response and returns the command and value. If the 
        response is only whitespace then command is set to None and value to empty
        string.'''

        command = None
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

        return command, value


class Connection:

    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr[0]
        self.port = addr[1]
        self.initialize()

    def initialize(self):
        '''initialize()
        Initialize attributes to their default values.'''

        self.state = State()
        self.user = ''
        self.is_logged_in = False
        self._dir = ''

    def addr_info(self):
        return f'{self.addr}:{self.port}'

    def update(self, command, value):
        '''update(command, value)
        Performs the client's command.'''

        # Test if user not logged in.
        if not self.is_logged_in:
            self.login(command, value)

        else:
            if command == 'CWD':
                self.cwd(value)

            elif command == 'CDUP':
                self.cdup()

            elif command == 'PWD':
                self.pwd()

            elif command == 'LIST':
                self.ls(value)

            # elif command == 'PASV':

            # elif command == 'PORT':

            # elif command == 'RETR':

            # elif command == 'STOR':

            # elif command == 'QUIT':

            elif command == 'REIN':
                self.initialize()

    def login(self, command, value):
        '''login(command, value)
        '''

        # Test if a username has not already been given.
        if not self.user:
            if command == 'USER':
                # Set username.
                self.user = value
                self.state.set_reply('331', 'Please specify password.')

            elif command == 'PASS':
                self.state.set_reply('503', 'Login with USER first.')

            else:
                self.state.set_reply('530', 'Please login with USER and PASS.')

        else:
            if command == 'PASS':
                # Test if username and password are valid.
                if util.System.credentials_are_correct(self.user, value):
                    # Set login status.
                    self.is_logged_in = True
                    self.state.set_reply('230', 'Login successful.')

                    # Change directory to user home.
                    self._dir = util.File.get_home_dir(self.user)

                else:
                    self.user = ''
                    self.state.set_reply('530', 'Login incorrect.')

            elif command == 'USER':
                self.state.set_reply('331', 'Please specify password.')

            else:
                self.state.set_reply('530', 'Please login with USER and PASS.')

    def cwd(self, path):
        '''cwd(path)
        Change working directory to path.'''

        # Get realpath.
        real = util.File.realpath(self._dir, path)

        # Test if realpath is directory that can be read.
        if util.File.isdir(real) and util.File.isreadable(real):
            self._dir = real
            self.state.set_reply('250', 'Directory successfully changed.')
            
        else:
            self.state.set_reply('550', 'Failed to change directory.')

    def cdup(self):
        '''cdup()
        Change current directory to parent directory.'''
        
        self._dir = util.File.parent(self._dir)
        self.state.set_reply('250', 'Directory successfully changed.')

    def pwd(self):
        '''pwd()
        Print the working directory: send working directory in reply message.'''

        self.state.set_reply('257', f'"{self._dir}" is the current directory.')

    def ls(self, path=None):
        '''ls(path):
        List the files at the provided path or in the current working directory
        if no path.'''

        # Test if PORT of PASV active.
        if PORT or PASV:
            # Test if path provided.
            if path:
                real = util.File.realpath(self._dir, path)

            else:
                real = self._dir
                
            # Test if realpath is directory that can be read.
            if util.File.isdir(real) and util.File.isreadable(real):
                # Get content list of path.
                test()

            else:
                self.state.set_reply()

        else:
            self.state.set_reply('425', 'Use PORT or PASV first.')


class State:

    def __init__(self):
        self.code = '220'
        self.message = 'Welcome to FTP Server.'

    def get_reply(self):
        '''get_reply()
        Generates a reply to send to a client based on current state.'''

        return f'{self.code} {self.message}\r\n'

    def set_reply(self, code, message):
        '''reply(code, message)
        Sets the reply code and message.'''

        self.code = code
        self.message = message


if __name__ == '__main__':
    # Get command line args.
    filename, port = util.System.args()
    host = '0.0.0.0'

    # Initialize server object and run main processing loop.
    server = Server(host, port, filename)
    server.start()
