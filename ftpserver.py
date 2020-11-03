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

global server
HOST = '0.0.0.0'
PORT_MIN = 1024
PORT_MAX = 65535


def log(description, client=None):
    # Test if client was passed.
    if client:
        server.logger.write(f'{client.addr_info()} {description}')
    else:
        server.logger.write(description)


def add_connection(client):
    if client not in server.open_connections:
        # Append client to list of open connections.
        server.open_connections.append(client)


def remove_connection(client):
    if client in server.open_connections:
        # Remove client from list of open connections.
        server.open_connections.remove(client)


class Server:

    def __init__(self, port, filename):
        self.port = port
        self.logger = Logger(filename)
        self.open_connections = []

    def start(self):
        '''start()
        The main processing loop of the FTP server. Creates a socket to listen
        for incomming connections. When a connection is accepted, starts a new
        thread with target set to serve_client().'''

        # Get Server family and test if it has dualstack IPv6.
        # fam, has_ds = self.server_params()

        # Create socket that will listen for client connections.
        # with socket.create_server((HOST, self.port), family=fam, dualstack_ipv6=has_ds) as sock:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Bind socket.
            sock.bind((HOST, port))
            log(f'Binding to address: {HOST}:{self.port}.')

            sock.listen()
            while True:
                conn = None
                client = None
                try:
                    # Accept new client connection.
                    conn, addr = sock.accept()
                    if conn:
                        # Create client and add to list of open connections.
                        client = Connection(conn, addr)
                        self.open_connections.append(client)
                        log('Connected to new client.', client)

                        # Create and start new thread to serve the client.
                        t = threading.Thread(
                            target=self.serve_client, args=(client,))
                        t.start()

                except KeyboardInterrupt:
                    self.close_all(client, conn, addr)
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

    def close_all(self, client, conn, addr):
        '''close_all(client, conn)
        Terminate the server. Close all open control and data connections and
        remove them from list of open connections.'''

        # Test if last connection is open but not in open list.
        if self.connection_not_in_list(conn, client):
            # Instantiate a new client and append to open list.
            self.open_connections.append(Connection(conn, addr))

        # Close all open connections.
        for c in self.open_connections:
            if c.data_conn:
                try:
                    c.data_conn.close()
                    log('Closing data connection', c.data_conn)
                except:
                    pass
            try:
                c.close()
                log('Closing connection.', c)
            except:
                pass

        self.open_connections.clear()

    def connection_not_in_list(self, conn, client):
        '''connection_not_in_list(self, conn, client) -> boolean
        Test if a client connection is open but has not yet been added the the
        server's list of open client connections.'''

        if (conn and client and client not in self.open_connections) or (conn and not client):
            return True

        return False

    def serve_client(self, client):
        '''serve_client(client)
        Provides the services of the FTP server to a client. Sends messages to
        the client based on the current state, receives client response, and
        updates the current state.'''

        with client.conn:
            while True:
                # Send current state reply to client.
                client.sendall()

                # Receive decoded client response.
                data = client.recv()

                # Test if user closed connection.
                if not data:
                    log(f'Client closed connection.', client)
                    break

                log(f'Received: {data}', client)

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

    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr[0]
        self.port = addr[1]
        self.data_conn = None
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

    def sendall(self, msg=None):
        if not msg:
            msg = self.state.get_reply()

        self.conn.sendall(util.System.encode(msg))
        log(f'Sent: {msg}', self)

    def recv(self, bufsize=4096):
        return util.System.decode(self.conn.recv(bufsize))

    def close(self):
        '''close()
        Send 421 message to client and close connection.'''

        # TODO: can you send the 426 though data conneciton if its not been accepted yet?
        # Test if data connection open.
        if self.data_conn:
            self.data_conn.close()
            self.state.set_reply('426', 'Connection closed; transfer aborted.')
            self.sendall()

        self.state.set_reply(
            '421', 'Service not available, closing control connection.')
        self.sendall()

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

            elif command == 'PASV':
                self.pasv()

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
        if self.data_conn:
            # Wait for client to connect to data connection.
            while not self.data_conn.connected:
                continue

            #TODO: move file logic to file class.
            # Test if a path was given.
            if path:
                # Get realpath (absolute path).
                real = util.File.realpath(self._dir, path)

                # Test if realpath is not readable.
                if util.File.isdir(real) and not util.File.isreadable(real):
                    self.state.set_reply(
                        '550', 'Directory read access restricted.')
                    return

            else:
                real = self._dir
                
            self.state.set_reply('150', 'Here comes the directory listing.')
            self.sendall()

            # Send LIST data.
            self.data_conn.ls(real)
            self.state.set_reply('226', 'Directory send OK.')

            # Clear data connection.
            self.data_conn = None


        else:
            self.state.set_reply('425', 'Use PORT or PASV first.')

    def pasv(self):
        '''pasv()
        Enter passive mode.'''

        # Open a data connection and retrieve port number.
        log(f'Opening Passive Mode data connection.', self)
        port = self.open_data_conn()

        # Convert port number into p1 and p2: port = (p1 * 256) + p2
        p1, p2 = self.convert_port_to_p1p2(port)

        # Convert host address into h1,h2,h3,h4
        h = self.addr.replace('.', ',')

        # Set Passive Mode reply.
        self.state.set_reply('227', f'Entering Passive Mode ({h},{p1},{p2})')

    def convert_port_to_p1p2(self, port):
        '''convert_port_to_p1p2(port) -> (p1, p2)
        Convert a given port number into p1 and p2.'''

        p1 = port // 256
        p2 = port - (p1 * 256)
        return p1, p2

    def open_data_conn(self):
        '''open_data_conn() -> port number
        Find an open port number on this machine, create a data connection, and
        bind it to the port number.'''

        low = 50000
        high = 60000

        # Initialize data connection.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Loop until found an open port.
        port_open = False
        while not port_open:
            # Get random port number within low and high.
            port = util.System.randint(low, high)
            try:
                # Attempt to bind to port.
                s.bind((HOST, port))
                port_open = True
                log(f'Binding data connection to: {HOST}:{port}.', self)
            except:
                pass

        # Create and start new thread to serve the client on data connection.
        t = threading.Thread(target=self.serve_data_conn, args=(s,))
        t.start()

        return port

    def serve_data_conn(self, sock):
        '''serve_data_conn(sock)
        '''

        sock.listen()
        # TODO: can I remove this while loop since only accepting single data conn?
        while True:
            try:
                # Accept new client data connection.
                conn, addr = sock.accept()
                if conn:
                    # Create new data connection object.
                    self.data_conn = DataConnection(conn, addr)
                    add_connection(self.data_conn)
                    self.data_conn.connected = True
                    log('Connected to client on data channel.', self.data_conn)
                    break

            except KeyboardInterrupt:
                break


class DataConnection:

    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr[0]
        self.port = addr[1]
        self.connected = False
        self.data_sent = False

    def addr_info(self):
        return f'{self.addr}:{self.port}'

    def sendall(self, msg):
        self.conn.sendall(util.System.encode(msg))

    def ls(self, path):
        # Get list information.
        file_list = util.File.listdir(path)

        # Send to client.
        self.sendall(file_list)
        self.data_sent = True
        log(f'Sent LIST data to client', self)

        # Remove connection from list of open connections.
        remove_connection(self)
        self.close()

    def close(self):
        try:
            self.conn.close()
            log('Closed data connection.', self)
        except:
            pass

    # def listen(self):
    #     '''listen()
    #     Listen for client to connect to this data connection.'''

    #     self.conn.listen()
    #     while True:
    #         conn = None
    #         try:
    #             # Accept new client data connection.
    #             conn, addr = self.conn.accept()
    #             if conn:
    #                 # Add self to list of open connections.
    #                 add_connection(self)
    #                 self.connected = True
    #                 log('Connected to client on data channel.', self)

    #         except KeyboardInterrupt:
    #             break


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
    filename, port = util.System.args(PORT_MIN, PORT_MAX)

    # Initialize server object and run main processing loop.
    server = Server(port, filename)
    server.start()
