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


def main(host, port):
    '''main()
    The main processing loop of the FTP server.'''
    # Test if platform supports IPv4/v6 dual connections.
    # if socket.has_dualstack_ipv6():
    #     sock = socket.create_server(
    #         myaddr, family=socket.AF_INET6, dualstack_ipv6=True)
    # else:
    #     sock = socket.create_server(myaddr)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        logger.write_log('Server binding to address {}:{}.'.format(host, port))
        sock.bind((host, port))

        logger.write_log('Server listening on port {}.'.format(port))
        sock.listen()

        conn, addr = sock.accept()
        with conn:
            logger.write_log('Connected to new client.', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                logger.write_log('Got: ' + data.decode(), addr)
                conn.sendall(data)
                logger.write_log('Sent: ' + data.decode(), addr)


if __name__ == '__main__':
    # Get command line args
    filename, port = System.get_ftp_args()
    if port < PORT_MIN or port > PORT_MAX:
        System.exit_('port number must be between {} and {}'.format(
            PORT_MIN, PORT_MAX))
    logger = Logger(filename)
    main('', port)
