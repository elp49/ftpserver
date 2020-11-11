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
PORT_MIN = 1024
PORT_MAX = 65535
IPv4 = '1'
IPv6 = '2'
NET_PRTS = [IPv4, IPv6]


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
        # with socket.create_server(('', self.port), family=fam, dualstack_ipv6=has_ds) as sock:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Bind socket.
            sock.bind(('', port))
            log(f'Binding to address: localhost:{self.port}.')

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
        '''server_params() -> (address family, boolean)
        Determine if the platform supports dualstack IPv6. If it does, then set
        server address family to be AF_INET6; otherwise set it to AF_INET.'''

        has_ds = socket.has_dualstack_ipv6()
        if has_ds:
            addr_fam = socket.AF_INET6
        else:
            addr_fam = socket.AF_INET

        return addr_fam, has_ds

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
                data = client.recvall()

                # Test if user closed connection.
                if not data:
                    log(f'Client closed connection.', client)
                    break

                log(f'Received: {data}', client)

                # Parse client response and update current state.
                command, value = self.parse_response(data)
                client.update(command, value)

        # Remove connection from list of open connections.
        client.close()
        remove_connection(client)

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


LIST = 'LIST'
RETR = 'RETR'
STOR = 'STOR'
DATA_COMMANDS = [LIST, RETR, STOR]


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

    # def recv(self, bufsize=4096):
    #     return util.System.decode(self.conn.recv(bufsize))

    def recvall(self, bufsize=4096):
        '''recvall(bufsize=4096) -> response data
        Receive, decode, and return all response data over control connection.'''

        data = b''
        while True:
            # Receive some data.
            res = self.conn.recv(bufsize)
            data += res

            # Test if end of message.
            if len(res) < bufsize:
                break

        return util.System.decode(data)

    def close(self):
        '''close()
        Send 421 message to client and close connection.'''

        # TODO: can you send the 426 though data conneciton if its not been accepted yet?
        # Test if data connection open.
        if self.data_conn:
            try:
                self.data_conn.close()
                self.state.set_reply(
                    '426', 'Connection closed; transfer aborted.')
                self.sendall()
            except:
                pass

        self.state.set_reply(
            '421', 'Service not available, closing control connection.')
        self.sendall()

        # Remove connection from list of open connections.
        remove_connection(self)

    def update(self, command, value):
        '''update(command, value)
        Performs the client's command.'''

        print(f'update({command}, {value})')
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
            elif command == 'PASV':
                self.pasv()
            elif command == 'EPSV':
                self.epsv(value)
            elif command == 'PORT':
                self.port_cmd(value)
            elif command == 'EPRT':
                self.eprt(value)
            elif command == 'REIN':
                self.initialize()
            elif command == 'QUIT':
                self.close()

            else:
                # Test if command not supported.
                if command not in DATA_COMMANDS:
                    self.state.set_reply('500', 'Unknown command.')

                # Test if data connection was not created.
                elif not self.data_conn:
                    self.state.set_reply('425', 'Use PORT or PASV first.')

                else:
                    # Test if Active Mode.
                    if self.data_conn.is_active_mode:
                        # Connect data connection to client.
                        self.data_conn.connect()

                    # Test if Passive Mode.
                    else:
                        # Wait for client to connect to data connection.
                        self.data_conn.connected.wait()

                    if command == LIST:
                        self.ls(value)
                    elif command == RETR:
                        self.retr(value)
                    elif command == STOR:
                        self.stor(value)

                    # Cleanup data connection.
                    self.data_conn.close()
                    self.data_conn = None

    def login(self, command, value):
        '''login(command, value)
        '''

        # Test if a username has not already been given.
        if not self.user:
            if command == 'USER':
                # Set username.
                self.user = value
                self.state.set_reply('331', 'Please specify the password.')

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

        # Test if a path was given.
        if path:
            # Get realpath (absolute path).
            realpath = util.File.realpath(self._dir, path)
        else:
            realpath = self._dir

        # Test if realpath does not exist or is not readable.
        if not util.File.exists(realpath) or not util.File.isreadable(realpath):
            self.state.set_reply(
                '226', 'Transfer done (but failed to open directory).')

        else:
            self.state.set_reply('150', 'Here comes the directory listing.')
            self.sendall()

            # Send LIST data.
            self.data_conn.ls(realpath)
            self.state.set_reply('226', 'Directory send OK.')

    def stor(self, value):
        '''stor(value)
        Store a file that the client will send over data channel.'''

        # Get the absolute path.
        path = util.File.realpath(self._dir, value)

        # Test if path not accessible.
        if not value or not util.File.can_write_file(path):
            self.state.set_reply('553', 'Could not create file.')

        else:
            # Retrieve file from client and store it in file system.
            self.state.set_reply('150', 'Ok to send data.')
            self.sendall()

            self.data_conn.stor(path)
            self.state.set_reply('226', 'Transfer complete.')

    def retr(self, value):
        '''retr(value)
        Send a file to the client over data channel.'''

        # Get the absolute path.
        path = util.File.realpath(self._dir, value)

        # Test if file does not exists or is not readable.
        if not util.File.isfile(path) or not util.File.isreadable(path):
            self.state.set_reply('550', 'Failed to open file.')

        else:
            # Get file size.
            nbytes = util.File.get_file_size(path)

            # Send file to client.
            self.state.set_reply(
                '150', f'Opening data connection for {value} ({nbytes} bytes).')
            self.sendall()

            self.data_conn.retr(path)
            self.state.set_reply('226', 'Transfer complete.')

    def pasv(self):
        '''pasv()
        Enter Passive Mode.'''

        # Open a data connection and retrieve port number.
        log(f'Opening Passive Mode data connection.', self)
        port = self.open_passive_conn()

        # Convert port number into p1 and p2: port = (p1 * 256) + p2
        p1, p2 = self.convert_port_to_p1p2(port)

        # Convert host address into h1,h2,h3,h4
        h = self.addr.replace('.', ',')

        # Set Passive Mode reply.
        self.state.set_reply('227', f'Entering Passive Mode ({h},{p1},{p2})')

    def epsv(self, net_prt):
        '''epsv(net_prt)
        Enter Extended Passive Mode.'''

        # Test if network protocol is bad.
        if net_prt and net_prt not in NET_PRTS:
            self.state.set_reply('522', 'Bad network protocol.')

        else:
            # Open a data connection and retrieve port number.
            log(f'Opening Extended Passive Mode data connection.', self)
            port = self.open_passive_conn(net_prt)

            # Set Extended Passive Mode reply.
            self.state.set_reply(
                '229', f'Entering Extended Passive Mode (|||{port}|)')

    def port_cmd(self, value):
        '''port_cmd(value)
        Enter Port Mode: Parse'''

        # Test if PORT command is bad.
        try:
            host, port = self.port_ok(value)
        except ValueError:
            return

        self.state.set_reply(
            '200', 'PORT command successful. Consider using PASV.')

        # Initialize a new data connection object.
        self.initialize_data_conn(addr=(host, port), is_active_mode=True)

    def port_ok(self, value):
        '''port_ok(value) -> (host address, port number)
        Parse a PORT command and perform various checks on it to determine if 
        it's OK. If command is OK, then return a tuple of the parsed values;
        otherwise set the reply code and message and raise ValueError.'''

        DELIMETER = ','
        a = value.split(DELIMETER)
        n = len(a)

        # Test if number of delimeters is incorrect.
        if n != 6:
            self.state.set_reply('500', 'Bad PORT command.')
            raise ValueError

        # Test if each PORT command argument is positive integer.
        try:
            for i in range(len(a)):
                pos = self.get_port_position(i)
                if int(a[i]) < 0:
                    raise ValueError
        except ValueError as err:
            self.state.set_reply('500', f'Bad PORT command at position {pos}.')
            raise err

        # Convert PORT command arguments into host and port.
        host = '.'.join(a[:4])
        port = self.convert_p1p2_to_port(a[4], a[5])

        return host, port

    def get_port_position(self, i):
        if i == 0:
            return 'h1'
        elif i == 1:
            return 'h2'
        elif i == 2:
            return 'h3'
        elif i == 3:
            return 'h4'
        elif i == 4:
            return 'p1'
        elif i == 5:
            return 'p2'

    def eprt(self, value):
        '''eptr(value)
        Enter Extended Port Mode.'''

        # Test if EPTR command is bad.
        try:
            net_prt, host, port = self.eptr_ok(value)
        except ValueError:
            return

        self.state.set_reply('200', 'EPRT command successful.')

        # Initialize a new data connection object.
        self.initialize_data_conn(
            addr=(host, port), net_prt=net_prt, is_active_mode=True)

    def eptr_ok(self, value):
        '''eptr_ok(value) -> (network protocol, host address, port number)
        Parse an EPTR command and perform various checks on it to determine if
        it's OK. If command is OK, then return a tuple of the parsed values;
        otherwise set the reply code and message and raise ValueError.'''

        DELIMETER = '|'
        a = value.split(DELIMETER)
        n = len(a)

        # Test if number of delimeters is incorrect.
        if n != 5:
            self.state.set_reply('500', 'Bad EPRT command.')
            raise ValueError

        # Test if network protocol unrecognized.
        net_prt = a[1]
        if net_prt not in NET_PRTS:
            self.state.set_reply('522', 'Bad network protocol.')
            raise ValueError

        # Test if host address not in format: X.X.X.X
        host = a[2]
        if len(host.split('.')) != 4:
            self.state.set_reply(
                '522', 'Bad EPRT command; Bad host address.')
            raise ValueError

        # Test if port number out of bounds.
        try:
            port = int(a[3])
            if port < 1:
                raise ValueError
        except ValueError as err:
            self.state.set_reply(
                '522', 'Bad EPRT command; Port number not positive integer.')
            raise err
        if port < PORT_MIN or port > PORT_MAX:
            self.state.set_reply(
                '522', f'Bad EPRT command; Port number should be in range {PORT_MIN} - {PORT_MAX}.')
            raise ValueError

        return net_prt, host, port

    def determine_addr_fam(self, net_prt=None):
        '''determine_addr_fam(net_prt=None) -> address family
        Determine the address family depending on a given network protcol value
        or the address family user by client connection'''

        # Test if network protocol specified.
        if net_prt:
            # Test if network protocol is IPv6
            if net_prt == IPv6:
                return socket.AF_INET6

            else:
                return socket.AF_INET

        # Return address family used by client connection.
        return self.conn.family

    def convert_port_to_p1p2(self, port):
        '''convert_port_to_p1p2(port) -> (p1, p2)
        Convert a given port number into p1 and p2.'''

        p1 = int(port) // 256
        p2 = int(port) - (p1 * 256)
        return p1, p2

    def convert_p1p2_to_port(self, p1, p2):
        '''convert_p1p2_to_port(p1, p2) -> port
        Convert a given p1 and p2 into a port number.'''

        return (int(p1) * 256) + int(p2)

    def open_passive_conn(self, net_prt=None):
        '''open_passive_conn(net_prt=None) -> port number
        Open a Passive Connection. Find an open port number on this machine,
        create a data connection, and bind it to the port number.'''

        low = 50000
        high = 60000

        self.initialize_data_conn()

        # Loop until found an open port.
        while True:
            # Get random port number within low and high.
            port = util.System.randint(low, high)
            try:
                # Attempt to bind to port.
                self.data_conn.conn.bind(('', port))
                log(f'Binding data connection to: localhost:{port}.', self)
                break
            except:
                pass

        # Create and start new thread to serve the client on data connection.
        t = threading.Thread(target=self.data_conn.listen)
        t.start()

        return port

    def initialize_data_conn(self, conn=None, addr=None, net_prt=None, is_active_mode=False):
        '''initialize_data_conn(addr, conn=None, net_prt=None)
        Initialize a new DataConnection object with given host address.'''

        # Get address family.
        addr_fam = self.determine_addr_fam(net_prt)

        # Test if no connection given.
        if not conn:
            conn = socket.socket(addr_fam, socket.SOCK_STREAM)

        # Create new data connection object.
        self.data_conn = DataConnection(conn, addr, is_active_mode)


class DataConnection:

    def __init__(self, conn=None, addr=None, is_active_mode=False):
        self.conn = conn
        self.addr = addr[0] if addr else None
        self.port = int(addr[1]) if addr else None
        self.connected = threading.Event()
        self.is_active_mode = is_active_mode

    def close(self):
        '''close()
        Close the data connection and remove it from the server's list of open
        connections.'''

        try:
            self.conn.close()
            log('Closed data connection.', self)
        except:
            pass

        # Remove connection from list of open connections.
        remove_connection(self)

    def connect(self):
        '''connect()
        Connect data connection to host, add itself to server's list of open
        connection, and set the "connected" event.'''

        print(f'connecting to {self.addr}:{self.port}')
        self.conn.connect((self.addr, self.port))

        # Add data connection to server's list of open connections.
        add_connection(self)

        # Set "connected" event.
        self.connected.set()

    def listen(self):
        '''listen()
        The data connection listens for a client to connect. This function is to
        be called when a client selects Passive Mode to be used.'''

        self.conn.listen(1)
        try:
            # Accept new client data connection.
            conn, addr = self.conn.accept()

            # Overwrite Data Connection attributes.
            self.conn = conn
            self.addr = addr[0]
            self.port = int(addr[1])

            # Set "connected" event.
            self.connected.set()
            log('Connected to passive data channel.', self)

        except KeyboardInterrupt:
            pass

    def addr_info(self):
        '''addr_info()
        Return the client address information.'''

        return f'{self.addr}:{self.port}'

    def sendall(self, msg):
        '''sendall(msg)
        Send all data to client over data connection.'''

        self.conn.sendall(util.System.encode(msg))

    def recvall(self, bufsize=4096):
        '''recvall(bufsize=4096) -> response data
        Receive, decode, and return all response data over data connection.'''

        data = b''
        while True:
            # Receive some data.
            res = self.conn.recv(bufsize)
            print(f'received {len(res)} bytes')
            data += res

            # Test if end of message.
            if len(res) < bufsize:
                break

        return util.System.decode(data)

    def ls(self, path):
        '''ls(path)
        Send directory list information to client.'''

        # Get list information.
        file_list = util.File.listdir(path)

        # Send to client.
        self.sendall(file_list)
        log(f'Sent LIST data to client.', self)

    def stor(self, path):
        '''stor(path)
        Retrieve file from client and store on file system.'''

        # Receive all file data.
        f_data = self.recvall(8192)

        log(f'Storing file "{path}" from client.', self)
        with open(path, 'w') as f:
            f.write(f_data)

        log(f'Stored file "{path}" from client OK.', self)

    def retr(self, path):
        '''retr(path)
        Send a file to the client over data connection.'''

        # Read the file.
        log(f'Reading file "{path}".', self)
        with open(path, 'r') as f:
            text = f.read()

        log(f'Done reading file "{path}".', self)

        self.sendall(text)
        log(f'Sent file "{path}" to client over data connection.', self)


class State:

    def __init__(self):
        self.code = '220'
        self.message = 'Welcome to FTP Server.'

    def get_reply(self):
        '''get_reply()
        Generates a reply to send to a client based on current state.'''

        return f'{self.code} {self.message}\r\n'

    def set_reply(self, code, message):
        '''set_reply(code, message)
        Sets the reply code and message.'''

        print(f'set_reply({code}, {message})')
        self.code = code
        self.message = message


if __name__ == '__main__':
    # Get command line args.
    filename, port = util.System.args(PORT_MIN, PORT_MAX)

    # Initialize server object and run main processing loop.
    server = Server(port, filename)
    server.start()
