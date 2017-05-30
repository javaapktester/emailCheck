#!/usr/bin/python3

import poplib
import email
import os
import jenkins
import time
import argparse


class GmailTest(object):
    """Attachment parser for emails with specified subject and attachment extension.

    This class checks new e-mail in inbox of specified e-mail(gmail) account, using poplib
    and sends build command for Jenkins job with obtained information.

    Instantiate with: GmailTest(g_username, g_password, j_username=None, j_password=None, debug=False)

               g_username - username of google account
               g_password - google account password
               j_username - jenkins username, by default same as for google account
               j_password - jenkins password, by default same as for google account
               debug - verbosity of printable output

        See the methods of the class for more documentation.
    """
    def __init__(self, g_username, g_password, j_username=None, j_password=None, debug=False):
        self.debug = debug
        self.username = g_username
        self.password = g_password
        # if the jenkins login username is the same as for gmail
        if j_username is None:
            self.jenUser = g_username
        else:
            self.jenUser = j_username

        # if the jenkins login password is the same as for gmail
        if j_password is None:
            self.jenPass = g_password
        else:
            self.jenPass = j_password

        # Change following string to change path, where to store e-mails, remember the access rights
        self.savedir = "/home/user/javaapktester/emailCheck"
        # Default Jenkins address and port, can by changed by set_jenkins_server method
        self.jenAddr = 'http://localhost:8080'

    def set_jenkins_server(self, address):
        """
        enable to specify other then default Jenkins' address and port, e.g. in case of remote Jenkins

        :param address: the IP address and port on which Jenkins server is listening in format: XXX.XXX.XXX.XXX:PORT
        """
        self.jenAddr = address

    def create_jenkins_job(self, email_addr, path):
        """
        sending command for build of jenkins job for aapt and cleanup job

        :param email_addr: e-mail address of return address in the e-mail
        :param path: path to apk file
        """
        server = jenkins.Jenkins(self.jenAddr, username=self.jenUser, password=self.jenPass)
        server.build_job('apk_parser', {'email': email_addr[1:-1], 'apkPath': path})

    def save_attach(self):
        """
        Parse new e-mails in the inbox of GmailTest.g_username account.
        Search for apk subject and download the attachment if it is of .apk extension.

        Used parameter are from object instance, specified during __init__ or by set_jenkins_server() method.
        """
        # TODO: add downloading attachment from gdrive

        # To use other mail-server then gmail, just replace the host and port
        self.connection = poplib.POP3_SSL('pop.gmail.com', 995)
        if self.debug:
            self.connection.set_debuglevel(1)

        # login information
        self.connection.user(self.username)
        self.connection.pass_(self.password)

        emails, total_bytes = self.connection.stat()
        print("{0} emails in the inbox, {1} bytes total".format(emails, total_bytes))
        # return in format: (response, ['mesg_num octets', ...], octets)

        if self.debug:
            msg_list = self.connection.list()
            print(msg_list)

        # messages processing
        for i in range(emails):

            # return in format: (response, ['line', ...], octets)
            response = self.connection.retr(i + 1)
            raw_message = response[1]

            str_message = email.message_from_bytes(b'\n'.join(raw_message))

            # save attach and parse data

            part_num = 0
            return_path = ''

            # in the following loop, there is safety feature in case, wrong e-mail format will be obtained,
            # it is not likely, but to be sure, if in the first part there is not Subject it will skip that part and try
            # the next-one, etc. For this need there is part_num if its val is 1 program will be looking for subject.

            for part in str_message.walk():
                part_num += 1
                if part_num == 1:
                    if part.get('Subject', '') == '':
                        if self.debug:
                            print("Haven't found the Subject, searching next part.")
                        part_num -= 1
                        continue

                    # accepted Subject values are (a||A)&&(p||P)&&(k||K)
                    if part.get('Subject').upper() == 'APK':
                        # find Return-Path information in the mail header
                        if part.get('Return-Path', '') != '':
                            return_path = part.get('Return-Path')
                            print(return_path)
                        else:
                            if self.debug:
                                print('Unable to get return-path, using from value instead')
                            # if Return-Path is missing, use From address from, mail header
                            if part.get('From', '') == '':
                                if self.debug:
                                    print('Unable to parse return address.')
                                    print(part)
                                break
                            else:
                                return_path = part.get('From')
                                print(return_path)

                # when we know where to send response, start searching for .apk
                if return_path != '':
                    if self.debug:
                        print(part.get_content_type())

                    # if true, then its parts will be walk in following iterations.
                    if part.get_content_maintype() == 'multipart':
                        continue

                    if part.get('Content-Disposition') is None:
                        if self.debug:
                            print("no content dispo")
                            print(part.get_payload())
                        continue

                    # Parsing original filename
                    filename = part.get_filename()
                    # check if it is .apk
                    if os.path.splitext(filename)[-1] == '.apk':
                        print("Filename: " + str(filename))
                    else:
                        if self.debug:
                            print('Attached file is not .apk')
                        continue

                    # create directory where to store the attached .apk, dirname will be actual timestamp, without dot.
                    dir_path = os.path.join(self.savedir, str(time.time()).replace(".", ""))
                    os.mkdir(dir_path)

                    # concat the path to file with normalized filename
                    # normalized means: if filename contained whitespace, replace it with underscore
                    path = os.path.join(dir_path, filename.replace(' ', '_'))

                    # write attachment do file specified in path variable.
                    fp = open(path, 'wb')
                    fp.write(part.get_payload(decode=1))
                    fp.close()

                    # send command to Jenkins server, to build a second job with given return address and apk file.
                    self.create_jenkins_job(return_path, path)
            # remove processed e-mail, for sanity of the mailbox, I suggest to uncomment next line, but it is not needed
            #self.connection.dele(i + 1)

            if self.debug:
                print('#####################################')

        # close the connection to gmail pop server, if commented out, the e-mails won't be marked as parsed.
        self.connection.quit()


if __name__ == '__main__':
    # prepare for help and parsing arguments from terminal
    parser = argparse.ArgumentParser(description='Test if for given gmail acc, there is any unprocessed e-mails, '
                                                 'with specified subject, if so download the attachment and create '
                                                 'the jenkins job.')
    parser.add_argument("-u", "--username", type=str, help="google account login name", required=True)
    parser.add_argument("-p", "--password", type=str, help="google account password", required=True)
    parser.add_argument("-U", "--jenusername", type=str, default=None,
                        help="jenkins account login name [default same as for google]")
    parser.add_argument("-P", "--jenpassword", type=str, default=None,
                        help="jenkins account password [default same as for google]")
    parser.add_argument("-s", "--jenserver", type=str, default=None,
                        help="address of jenkins server [default localhost:8080]")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug output")
    args = parser.parse_args()

    # create instance of GmailTest and set all needed parameters
    d = GmailTest(g_username=args.username, g_password=args.password, j_username=args.jenusername,
                  j_password=args.jenpassword, debug=args.verbose)
    # if needed uncomment and modify following line
    # d.set_jenkins_server('192.168.1.1:8400')

    # start parsing && saving attachments
    d.save_attach()
