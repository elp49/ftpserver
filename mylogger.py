# CS472 - Homework #3
# Edward Parrish
# mylogger.py
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
        Uses the datetime library to return a custom formatted string of the
        current datetime."""
        return datetime.datetime.now().strftime('%x %X.%f')

    def write_log(self, description, client_id=None):
        """write_log(client_id, description)
        Logs server activity in the following format: 
        [TIMESTAMP] [CLIENT_ADDR]:[PORT] [ACTIVITY_DESCRIPTION]
        If the filename has been lost then prints to the console."""
        if client_id is not None:
            client_addr, port = client_id
            # Append line separator, datetime, and log string to line.
            line = '{} {}:{} {}{}'.format(self.timestamp(), client_addr, port, description, LINE_SEP)
        else:
            line = self.timestamp() + ' ' + description + LINE_SEP

        # Test if filename is defined.
        if self.filename is not None and len(self.filename) > 0:
            try:
                with open(self.filename, 'a') as log_file:
                    # Append the line to log file.
                    log_file.write(line)

            except Exception as err:
                print('There was an error while writing to the log file {}: {}'.format(
                    self.filename, err))
        else:
            print(line)
