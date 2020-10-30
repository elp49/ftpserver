#!/usr/bin/env python3
# CS472 - Homework #3
# Edward Parrish
# systemhelper.py
#
# This module is the system helper module of the FTP server. It contains a the
# functions needed to communicate with the client system and is used by the
# major module.

import sys

PORT_MIN = 1024
PORT_MAX = 65535


class System:

    @staticmethod
    def args():
        '''args()
        Handles potential errors with the FTP server command line arguments. If
        errors exist then the program exits. Otherwise, returns an array of the
        FTP server arguments in this format: [FILENAME, PORT].'''
        num_args = len(sys.argv)

        # Test if no log filename give.
        if num_args < 2:
            System.exit_('log filename argument is required', True)

        # Test if port is specified.
        elif num_args < 3:
            System.exit_('port number argument is required', True)

        try:
            # Test if port can be casted to int.
            port = int(sys.argv[2])
        except ValueError:
            System.exit_(
                'port number argument must be a positive integer', True)

        # Test if port is out of range.
        if port < PORT_MIN or port > PORT_MAX:
            System.exit_(
                f'port number must be between {PORT_MIN} and {PORT_MAX}')

        return [sys.argv[1], port]

    @staticmethod
    def display(s):
        '''display(s)
        Displays a string s to the console by calling the builtin print function.'''
        print(s)

    @staticmethod
    def display_list(l):
        '''display_list(l)
        Displays a list l to the console by appending each item in the list to
        a string separated by tabs and then calling the builtin print function.'''
        # Test if l is a list.
        if isinstance(l, list):
            mylist = l
        else:
            mylist = [l]

        mylist.sort()

        line = ''
        for s in mylist:
            line += s + '\t\t'

        print(line)

    @staticmethod
    def input(s=None):
        try:
            # Test if s is None.
            if s is None:
                result = input('ftp> ')
            else:
                result = input(s)

        except KeyboardInterrupt:
            System.exit_('KeyboardInterrupt')

        return result.strip()

    @staticmethod
    def input_args(s=None):
        result = []

        # Get raw input args.
        raw = System.input(s).split(' ')

        for a in raw:
            a = a.strip()
            if len(a) > 0:
                result.append(a)

        return result

    @staticmethod
    def exit_(msg, is_arg_err=False):
        '''exit_(msg)
        Prints the error message passed to it by msg to the console and then
        exits. If the optional argument is_arg_err is passed as True then the
        correct usage of the program is also displayed before exiting.'''
        print(f'Error: {msg}')

        if is_arg_err:
            print(f'Usage: {sys.argv[0]} [FILENAME] [PORT]')

        exit('exiting...')
