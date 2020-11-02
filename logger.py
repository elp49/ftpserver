# CS472 - Homework #3
# Edward Parrish
# logger.py
#
# This module is the logger module of the FTP server. It contains a Logger class
# that is used by the major module to handle logging.

import datetime

LINE_SEP = '\n'


class Logger:
    """Logger
    The Logger helper class. Used to write logs to a file."""

    def __init__(self, filename):
        self.filename = filename

    def timestamp(self):
        """timestamp()
        Uses the datetime library to return a custom formatted timestamp."""
        return datetime.datetime.now().strftime('%x %X.%f')

    def write_log(self, description):
        """write_log(description)
        Write server activity to log file. If the filename has been lost then
        prints to the console."""
            
        line = f'{self.timestamp()} {description}{LINE_SEP}'

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
