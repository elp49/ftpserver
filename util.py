#!/usr/bin/env python3
# CS472 - Homework #4
# Edward Parrish
# util.py
#
# This module is the utility module of the FTP server. It provides helper
# functions for the major module.

import sys
import os
import stat
import random
import platform


class System:
    '''System
    This class provides the FTP server with common system helper functions.'''

    @staticmethod
    def args(port_min, port_max):
        '''args() -> (log filename, port number)
        Retrieve the command line arguments for the FTP server. Handles
        potential errors with the FTP server command line arguments. If errors
        exist then the program exits.'''

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
        if port < port_min or port > port_max:
            System.exit(f'port number must be between {port_min} & {port_max}')

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

    DEFAULT_ENCODING = 'ISO-8859-1'

    @staticmethod
    def encode(data, encoding='utf-8'):
        try:
            return data.encode(encoding)
        except UnicodeEncodeError:
            return data.encode(System.DEFAULT_ENCODING)

    @staticmethod
    def decode(data, encoding='utf-8'):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            return data.decode(System.DEFAULT_ENCODING)

    @staticmethod
    def randint(a, b):
        return random.randint(a, b)

    @staticmethod
    def system_info():
        return f'{platform.system()} {platform.release()}'

    @staticmethod
    def config():
        '''config() -> configuration tuple
        Read the config file at the hardcoded path "./home/elp49/ftpserver.conf"
        and return the configuration settings.'''

        config = Config()
        path = './home/elp49/ftpserverd.conf'

        try:
            f = open(path, mode='r')
        except:
            return config

        line = f.readline().strip()
        while line:
            if line[0] != Config.COMMENT:
                a = line.split(Config.OPERATOR)
                if len(a) > 1:
                    attribute = a[0].strip()
                    value = a[1].strip().split(Config.COMMENT)[0].strip()
                    if attribute and value:
                        config.set_attribute(attribute, value)

            line = f.readline().strip()

        f.close()
        return config


class Config:

    COMMENT = '#'
    OPERATOR = '='
    PORT_MODE = 'port_mode'
    PASV_MODE = 'pasv_mode'
    ATTRIBUTES = [PORT_MODE, PASV_MODE]

    YES = 'yes'
    NO = 'no'
    VALUES = [YES, NO]

    def __init__(self, port_mode=True, pasv_mode=True):
        self.port_mode = port_mode
        self.pasv_mode = pasv_mode

    def set_attribute(self, attribute, value):
        a = attribute.lower()
        v = value.lower()
        if a in Config.ATTRIBUTES and v in Config.VALUES:
            if a == Config.PORT_MODE:
                if v == Config.YES:
                    self.port_mode = True
                elif v == Config.NO:
                    self.port_mode = False

            elif a == Config.PASV_MODE:
                if v == Config.YES:
                    self.pasv_mode = True
                elif v == Config.NO:
                    self.pasv_mode = False

    def all_data_conn_types_disabled(self):
        '''all_data_conn_types_disabled() -> boolean
        Test if all data connection types are disabled.'''
        
        if self.port_mode or self.pasv_mode:
            return False

        return True


class File:
    '''File
    This class provides the FTP server with common file system helper functions.'''

    @staticmethod
    def get_home_dir(user):
        '''get_home_dir(user) -> path to user's home directory
        Get the user's home directory. If one does not already exist then create
        it. If a file is in its place, append underscore(s) to filename and
        create directory in its place.'''

        CUR_DIR = os.path.abspath('.')
        HOME = File.realpath(CUR_DIR, './home')

        # Test if home dir does not exist.
        if not os.path.exists(HOME):
            os.mkdir(HOME)

        # Get absolute path to user directory.
        path = File.realpath(HOME, user)

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
    def exists(path):
        '''exists(path) -> boolean
        Determine if the path exists.'''

        return os.path.exists(path)

    @staticmethod
    def isfile(path):
        '''isfile(path) -> boolean
        Determine if the path is a file.'''

        return os.path.isfile(path)

    @staticmethod
    def isdir(path):
        '''isdir(path) -> boolean
        Determine if the path is a directory.'''

        return os.path.isdir(path)

    @staticmethod
    def isreadable(path):
        '''isreadable(path) -> boolean
        Determine if the path is readable.'''

        return os.access(path, os.R_OK)

    @staticmethod
    def iswritable(path):
        '''iswritable(path) -> boolean
        Determine if the path is writable.'''

        return os.access(path, os.W_OK)

    @staticmethod
    def can_write_file(path):
        '''can_write_file(path) -> boolean
        Determine if the user can write a file to a path.'''

        parent = File.parent(path)
        return File.iswritable(parent)

    @staticmethod
    def listdir(path):
        # Open pipe to acces command line stream.
        stream = os.popen(f'ls -Al {path}')

        # Read command lines output.
        listing = stream.readlines()

        # Remove line breaks.
        for i in range(len(listing)):
            listing[i] = listing[i].rstrip()

        return '\n'.join(listing)

    @staticmethod
    def get_file_size(path):
        return os.path.getsize(path)
