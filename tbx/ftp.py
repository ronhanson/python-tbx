#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2014 - Ronan Delacroix
FTP utils
:author: Ronan Delacroix
"""
try:
    import logging
    import pyftpdlib.servers
    import pyftpdlib.handlers
    from . import text

    try:
        from pyftpdlib.handlers import TLS_FTPHandler as SFTPHandler
    except ImportError:
        from pyftpdlib.handlers import FTPHandler as SFTPHandler  # If that case happens, install pyopenssl


    class FTPEventLogger:

        def on_connect(self):
            self.log("Connection received.")

        def on_disconnect(self):
            self.log("Disconnection.")

        def log(self, msg, logfun=None, error=False):
            raise Exception('Sub classes should override this function.')

        def on_login(self, username):
            self.log("User %s logged in." % username)

        def on_login_failed(self, username, password):
            self.log("Login failed with credentials %s/%s." % (username, password))

        def on_logout(self, username):
            self.log("User %s logged out." % username)

        def on_file_sent(self, filepath):
            filepath = text.convert_to_unicode(filepath)
            self.log(u"File %s has been successfully sent (User %s)." % (filepath, self.username))

        def on_file_received(self, filepath):
            filepath = text.convert_to_unicode(filepath)
            self.log(u"User %s has uploaded a new file : %s" % (self.username, filepath))

        def on_incomplete_file_sent(self, filepath):
            filepath = text.convert_to_unicode(filepath)
            self.log("""File %s has been Incompletely sent by user %s...
            Waiting for the user to resume his download.""" % (filepath, self.username), error=True)

        def on_incomplete_file_received(self, filepath):
            filepath = text.convert_to_unicode(filepath)
            self.log("""A new file %s has been uploaded but is incomplete by user %s...
            Waiting for the user to resume his upload.""" % (filepath, self.username), error=True)


    class FTPHandler(FTPEventLogger, pyftpdlib.handlers.FTPHandler):

        def log(self, msg, logfun=None, error=False):
            if error:
                logging.error("[FTP] %s" % msg)
            else:
                logging.info("[FTP] %s" % msg)


    class SecureFTPHandler(FTPEventLogger, SFTPHandler):

        def log(self, msg, logfun=None, error=False):
            if error:
                logging.error("[FTPS] %s" % msg)
            else:
                logging.info("[FTPS] %s" % msg)


    class DummyDictFTPAuthorizer(pyftpdlib.handlers.DummyAuthorizer):
        """
        Dummy Dict FTP Authorizer class.
        Provide authentication through FTP for users stored in a dict.

        About permissions:

            Read permissions:
             - "e" = change directory (CWD command)
             - "l" = list files (LIST, NLST, STAT, MLSD, MLST, SIZE, MDTM commands)
             - "r" = retrieve file from the server (RETR command)

            Write permissions:
             - "a" = append data to an existing file (APPE command)
             - "d" = delete file or directory (DELE, RMD commands)
             - "f" = rename file or directory (RNFR, RNTO commands)
             - "m" = create directory (MKD command)
             - "w" = store a file to the server (STOR, STOU commands)
        """

        def __init__(self, users):
            """
            Constructor
            """
            super(DummyDictFTPAuthorizer, self).__init__()
            for username, user in users.items():
                self.add_user(username,
                              user['password'],
                              user['homedir'],
                              perm=user.get('perm', self.read_perms),
                              msg_login="Hi %s, you're welcome here." % user.get('name', username),
                              msg_quit="Bye %s, hoping you get back soon!" % user.get('name', username)
                )
            self.custom_users = users


    def create_server(handler, users, listen_to="", port=21, data_port_range='5500-5700', name="Ronan Python FTP Server", masquerade_ip=None, max_connection=500, max_connection_per_ip=10):
        """
        Runs the FTP Server
        """

        try:
            start, stop = data_port_range.split('-')
            start = int(start)
            stop = int(stop)
        except ValueError:
            raise Exception('Invalid value for data ports')
        else:
            data_port_range = range(start, stop + 1)

        handler.authorizer = DummyDictFTPAuthorizer(users=users)

        handler.banner = "%s. (Advice : Please use UTF-8 encoding and always use Binary mode)" % name
        handler.passive_ports = data_port_range

        if masquerade_ip:
            handler.masquerade_address = masquerade_ip

        #logging.getLogger('pyftpdlib').disabled = True
        pyftpdlib.log.logger = logging.getLogger()  # Replace pyftpd logger by default logger

        # Instantiate FTP server class and listen to 0.0.0.0:21 or whatever is written in the config
        address = (listen_to, port)
        server = pyftpdlib.servers.FTPServer(address, handler)

        # set a limit for connections
        server.max_cons = max_connection
        server.max_cons_per_ip = max_connection_per_ip

        return server


    def create_ftp_server(users, listen_to="", port=21, data_port_range='5500-5700',
                          name="FTP Server", masquerade_ip=None, max_connection=500, max_connection_per_ip=10):
        """
            FTP Server implements normal FTP mode.
        """
        handler = FTPHandler
        return create_server(handler, users, listen_to=listen_to, port=port, data_port_range=data_port_range,
                             name=name, masquerade_ip=masquerade_ip, max_connection=max_connection,
                             max_connection_per_ip=max_connection_per_ip)


    def create_secure_ftp_server(users, certificate, listen_to="", port=990, data_port_range='5700-5900',
                                 name="FTP Server", masquerade_ip=None, max_connection=500, max_connection_per_ip=10):
        """
            FTP Server implements FTPS (FTP over TLS/SSL) mode.
              Note: Connect from client using "FTP over TLS/SSL explicit mode".
        """
        handler = SecureFTPHandler
        handler.certfile = certificate
        return create_server(handler, users, listen_to=listen_to, port=port, data_port_range=data_port_range,
                             name=name, masquerade_ip=masquerade_ip, max_connection=max_connection,
                             max_connection_per_ip=max_connection_per_ip)

except ImportError:
    pass

try:
    """
    Following is only for client FTP using FTPUtil library.
    """
    import ftplib


    class FTPSession(ftplib.FTP):
        """
        This class is required to connect to a different port with FTPUtil lib.
        """
        def __init__(self, url, user, password, port=21, passive=None, timeout=None):
            if timeout:
                ftplib.FTP.__init__(self, timeout=timeout)
            else:
                ftplib.FTP.__init__(self)
            self.connect(url, port)
            self.login(user, password)
            if passive is not None:
                self.set_pasv(passive)

        """
        Usage :
            import ftputil
            host = ftputil.FTPHost('my.server.url.or.ip', user='root', password='hello', 2121, session_factory=FTPSession)
            names = host.listdir(host.curdir)
            print(names)
        """

except ImportError:
    pass