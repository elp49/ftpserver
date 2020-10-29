#!/usr/bin/env python3
# CS472 - Homework #3
# Edward Parrish
# ftpserver.py
#
# This module is the major module of the FTP server, with the main processing loop.

from systemhelper import System
from mylogger import Logger
import socket

global logger
PORT_MIN = 1024
PORT_MAX = 65535


def main(port):
    '''main()
    The main processing loop of the FTP server.'''
    # Test if platform supports IPv4/v6 dual connections.
    if socket.has_dualstack_ipv6():
        sock = socket.create_server(
            ('', port), family=socket.AF_INET6, dualstack_ipv6=True)
    else:
        sock = socket.create_server(('', port))

    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.bind((socket.gethostname(), port))

    logger.write_log('', 'Server listening on port {}.'.format(port))
    sock.listen()
    conn, addr = sock.accept()

    logger.write_log(addr, 'Connected to new client.')
    while True:
        data = conn.recv(1024)
        if not data:
            break
        logger.write_log(addr, 'Got: ' + data.decode())
        conn.sendall(data)
        logger.write_log(addr, 'Sent: ' + data.decode())


if __name__ == '__main__':
    # Get command line args
    filename, port = System.get_ftp_args()
    if port < PORT_MIN or port > PORT_MAX:
        System.exit_('port number must be between {} and {}'.format(
            PORT_MIN, PORT_MAX))
    logger = Logger(filename)
    main(port)
