# CS472 - Homework #4
# Edward Parrish
# logger.py
#
# This module is the logger module of the FTP server. It contains the Logger
# class which is used by the major module.

import datetime


class Logger:
    '''Logger
    The Logger helper class. Used to write logs to a file.'''

    LINE_SEP = '\n'

    def __init__(self, filename):
        self.filename = filename

    def timestamp(self):
        '''timestamp() - > formatted timestamp
        Return a formatted timestamp string of the current datetime.'''

        return datetime.datetime.now().strftime('%x %X.%f')

    def write(self, description):
        '''write(description)
        Write to log file. If the log file's filename has been lost then print
        to the console.'''

        line = f'{self.timestamp()} {description}{self.LINE_SEP}'

        # Test if filename is defined.
        if self.filename:
            try:
                with open(self.filename, 'a') as log_file:
                    # Append the line to log file.
                    log_file.write(line)

            except Exception as err:
                print(f'Error writing to log file {self.filename}: {err}')
                print(line)
        else:
            print(line)
