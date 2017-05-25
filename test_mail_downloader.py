#!/usr/bin/python3

import poplib
import email
import os


class GmailTest(object):
    def __init__(self):
        self.savedir="./"

    def test_save_attach(self):
        self.connection = poplib.POP3_SSL('pop.gmail.com', 995)
        #self.connection.set_debuglevel(1)
        self.connection.user("javaapktester")
        self.connection.pass_("Avast2017!")

        emails, total_bytes = self.connection.stat()
        print("{0} emails in the inbox, {1} bytes total".format(emails, total_bytes))
        # return in format: (response, ['mesg_num octets', ...], octets)
        msg_list = self.connection.list()
        #print(msg_list)

        # messages processing
        for i in range(emails):

            # return in format: (response, ['line', ...], octets)
            response = self.connection.retr(i+1)
            raw_message = response[1]

            str_message = email.message_from_bytes(b'\n'.join(raw_message))

            # save attach
            for part in str_message.walk():
                p = email.parser.FeedParser()
                p.feed(str(part))
                header = p.close()
                if 'Subject' in header.keys():
                  print(header['Subject'])
                if 'Return-Path' in header.keys():
                  print(header['Return-Path'])
                #print(part)
                #print('*****************')
                '''
                print(part.get_content_type())

                if part.get_content_maintype() == 'multipart':
                    continue

                if part.get('Content-Disposition') is None:
                    print("no content dispo")
                    continue

                filename = part.get_filename()
                if not(filename): filename = "test.txt"
                print(filename)

                fp = open(os.path.join(self.savedir, filename), 'wb')
                fp.write(part.get_payload(decode=1))
                fp.close()
'''
            print('#####################################')
        #I  exit here instead of pop3lib quit to make sure the message doesn't get removed in gmail
#        import sys
#        sys.exit(0)

d=GmailTest()
d.test_save_attach()