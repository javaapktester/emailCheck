#!/usr/bin/python3

import poplib
import email
import os
import jenkins
import argparse


class GmailTest(object):
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

        self.savedir = "./"
        self.jenAddr = 'http://localhost:8080'

    def set_jenkins_server(self, address):
        self.jenAddr = address

    def create_jenkins_job(self, email_addr, path):
        """
        creating jenkins job for aapt and cleanup job

        inspiration: https://python-jenkins.readthedocs.io/en/latest/examples.html

        :param email_addr: e-mail address of return address in the e-mail
        :param path: path to apk file
        """
        server = jenkins.Jenkins(self.jenAddr, username=self.jenUser, password=self.jenPass)
        # TODO: change 'api-test'
        # TODO: deal with priorities
        server.build_job('api-test', {'email': email_addr, 'pathToApk': path})

    def test_save_attach(self):
        # TODO: check for subject and return address only in first part of the mail.
        # TODO: add downloading attachment from gdrive

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

            for part in str_message.walk():
                part_num += 1
                if part_num == 1:
                    p = email.parser.FeedParser()
                    p.feed(str(part))
                    header = p.close()
                    if 'Subject' in header.keys():
                        print(header['Subject'])
                        if header['Subject'].upper() == 'APK':
                            if 'Return-Path' in header.keys():
                                return_path = header['Return-Path']
                                print(header['Return-Path'])
                            elif 'From:' in header.keys():
                                print('Unable to get, using from value instead')
                                return_path = header['From']
                                print(header['From'])
                            else:
                                print('Unable to parse return address.')
                                print(part)
                                break
                if return_path != '':
                    if self.debug:
                        print(part.get_content_type())
                    if part.get_content_maintype() == 'multipart':
                        continue

                    if part.get('Content-Disposition') is None:
                        if self.debug:
                            print("no content dispo")
                        continue

                    filename = part.get_filename()
                    if not (filename): filename = "test.txt"
                    print(filename)

                    fp = open(os.path.join(self.savedir, filename), 'wb')
                    fp.write(part.get_payload(decode=1))
                    fp.close()

        print('#####################################')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test if for given gmail acc, there is any unprocessed e-mails, '
                                                 'with specified subject, if so download the attachment and create '
                                                 'the jenkins job.')
    parser.add_argument("-u", "--username", type=str, help="google account login name")
    parser.add_argument("-p", "--password", type=str, help="google account password")
    parser.add_argument("-U", "--jenusername", type=str, default=None,
                        help="jenkins account login name [default same as for google]")
    parser.add_argument("-P", "--jenpassword", type=str, default=None,
                        help="jenkins account password [default same as for google]")
    parser.add_argument("-s", "--jenserver", type=str, default=None,
                        help="address of jenkins server [default localhost:8080]")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug output")
    args = parser.parse_args()

    d = GmailTest(g_username=args.username, g_password=args.password, j_username=args.jenusername,
                  j_password=args.jenpassword, debug=args.verbose)



    d.test_save_attach()
