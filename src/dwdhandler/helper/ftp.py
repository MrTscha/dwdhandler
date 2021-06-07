# -*- coding: utf-8 -*-
"""
Created on Sat Jun 06 17:32:40 2021

@author: Tobias Schad
@email: tobias.schad@googlemail.com
@description: Simple FTP handling """

# import library
from ftplib import FTP

class cftp():
    def __init__(self,url,user=None,passw=None):
        """ Class to handle ftp connections
            url: Destination to open connection
            user: If user credential is needed, default None
            passw: if password credential is needed, default None
        """

        self.url   = url
        if(user is None):
            self.user = 'anonymous'
        else:
            self.user  = user
        if(passw is None):
            self.passw = ''
        else:
            self.passw = passw

    def open_ftp(self):
        """ Opens ftp connection via given url
        """

        self.ftp = FTP(self.url)
        self.ftp.set_pasv(True)
        self.ftp.login(user=self.user,passwd=self.passw)

    def cwd_ftp(self,location):
        """ Change location on ftp connection """
        self.ftp.cwd(location)

    def retr_files_ftp(self):
        """ retrieves files from current dir of ftp connection """
        return self.ftp.nlst()

    def save_file(self,remote,local):

        fil_save = open(local,'wb')

        self.ftp.retrbinary('RETR {}'.format(remote),fil_save.write)

        fil_save.close()

    def close_ftp(self):
        """ Close existing ftp connection """
        self.ftp.close()