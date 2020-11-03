# FtpServer


## Warning:
    User home areas are stored within the ./home directory. The FTP Server
    assumes that there are only directories and no files in the ./home
    directory. If a file exist in the home directory with the same filename as a
    new user logging in, then the file will be renamed by appending underscores
    to its existing name until that path does not exist.


## Usage:
    python3 ftpserver.py [FILENAME] [PORT]

    FILENAME    path to log file for recording ftp messages and server activity
    PORT        the desired port number to bind the FTP server to


Once the program is running, the server will immedately bind to 0.0.0.0:PORT
where the port number is the one provided on command line. Server activity will
be updated in the log file.


## Issues:
    There are no known issues.
