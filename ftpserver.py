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
        while True:
            data = conn.recv(1024)
            if not data:
                break
            logger.write_log(f'Got: {data.decode()}', addr)
            conn.sendall(data)
            logger.write_log(f'Sent: {data.decode()}', addr)

    # Remove connection from list of open connections.
    open_connections.remove(conn)


if __name__ == '__main__':
    # Get command line args.
    filename, port = System.args()
    host = '0.0.0.0'

    # Initialize logger with log filename and run main processing loop.
    logger = Logger(filename)
    main(host, port)
