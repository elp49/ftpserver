#!/usr/bin/env python3
# CS472 - Homework #3
# Edward Parrish
# util.py
#
# This module is the utility module of the FTP server. It provides helper
# classes for the major module.

import sys
import os


class System:
    '''System
    This class provides the FTP server with common system helper functions.'''

    @staticmethod
    def args():
        '''args() -> (filename, port number)
        Retrieve the command line arguments for the FTP server. Handles
        potential errors with the FTP server command line arguments. If errors
        exist then the program exits.'''

        PORT_MIN = 1024
        PORT_MAX = 65535
        num_args = len(sys.argv)

        # Test if no log filename give.
        if num_args < 2:
            System.exit('log filename is required', True)

        # Test if port is specified.
        elif num_args < 3:
            System.exit('port number is required', True)

        try:
            # Test if port can be casted to int.
            port = int(sys.argv[2])
        except ValueError:
            System.exit('port number must be a positive integer', True)

        # Test if port is out of range.
        if port < PORT_MIN or port > PORT_MAX:
            System.exit(f'port number must be between {PORT_MIN} & {PORT_MAX}')

        return (sys.argv[1], port)

    @staticmethod
    def exit(msg, is_arg_err=False):
        '''exit(msg)
        Prints the error message passed to it by msg to the console and then
        exits. If the optional argument is_arg_err is passed as True then the
        correct usage of the program is also displayed before exiting.'''
        print(f'Error: {msg}')

        if is_arg_err:
            print(f'Usage: {sys.argv[0]} [FILENAME] [PORT]')

        exit('exiting...')

    @staticmethod
    def credentials_are_correct(user, pswd):
        '''credentials_correct(user, pswd) -> boolean
        Tests if the given username and password are correct login credentials.'''

        return user == 'cs472' and pswd == 'hw2ftp'


class File:
    '''File
    This class provides the FTP server with common file system helper functions.'''

    @staticmethod
    def get_home_dir(user):
        '''get_home_dir(user) -> path to user's home directory
        Get the user's home directory. If one does not already exist then create
        it. If a file is in its place, append underscore(s) to filename and
        create directory in its place.'''

        # Get absolute path to user directory.
        path = os.path.join(os.path.abspath('.'), 'home', user)

        # Test if does not path exist.
        if not os.path.exists(path):
            os.mkdir(path)

        # Test if path is a file.
        elif os.path.isfile(path):
            new_name = path
            file_renamed = False
            while not file_renamed:
                # Append underscore to new name.
                new_name = f'{new_name}_'
                try:
                    # Rename file to new name and create user home dir.
                    os.rename(path, new_name)
                    os.mkdir(path)
                    file_renamed = True

                except OSError:
                    pass

        return path

    @staticmethod
    def realpath(path1, path2):
        '''realpath(path1, path2) -> file path
        If path2 is an absolute path then return path2. Otherwise, join path1
        and path2 and get the real path from result.'''

        # Test if path2 is absolute path.
        if (os.path.isabs(path2)):
            return path2

        join = os.path.join(path1, path2)
        return os.path.realpath(join)

    @staticmethod
    def parent(path):
        '''parent(path) -> parent directory path'''

        return os.path.split(path)[0]

    @staticmethod
    def isdir(path):
        '''isdir(path) -> boolean
        Determine if the path is a directory.'''

        return os.path.isdir(path)

    @staticmethod
    def isreadable(path):
        '''parent(path) -> boolean
        Determine if the path is readable.'''

        return os.access(path, os.R_OK)

    # def cd(self, path):
    #     '''cd(path) -> error message
    #     Attempt to change the current working directory to path. Return an error
    #     message if unsuccessful.'''

    #     # Test if path is directory.
    #     if os.path.isdir(path):
    #         self._dir = path

    #     # Test if path exists.
    #     elif os.path.exists(path):
    #         return 'Not a directory.'

    #     else:
    #         return 'No such file or directory'