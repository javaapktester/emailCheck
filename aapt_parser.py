import smtplib
import subprocess
import shutil
import os
import argparse


class RespContext(object):
    """Object of response context, with parsed properties of .apk

        Instantiate with: RespContext(), it will init all values to empty string.

        Parameters are set by direct calling.

            name - Package name
            min_sdk - Minimal SDK
            target_sdk - Target SDK
            permissions - list of permissions, to add permission, use set_permissions() object method.
            app_version - App version
            launch_activity - Launchable-activity
            app_label - Application-label
            file_name - filename of .apk file

    """
    def __init__(self):
        self.name = ''
        self.min_sdk = ''
        self.target_sdk = ''
        self.permissions = []
        self.app_version = ''
        self.launch_activity = ''
        self.app_label = ''
        self.file_name = ''

    # human readable string output of instance
    def __str__(self):
        return ''' 
        Filename: {}
        Min SDK: {}
        Target SDK: {}
        Package name: {}
        App version: {}
        Launchable-activity: {}
        Application-label: {}
        Permissions: {}
        '''.format(self.file_name, self.min_sdk, self.target_sdk, self.name, self.app_version,
                   self.launch_activity, self.app_label, self.str_permissions())

    def set_permissions(self, new_permission):
        """ append given permission to the instance list.

        :param new_permission: string representation of parsed permission from .apk
        """
        self.permissions.append(new_permission)

    # human readable string output of permission list
    def str_permissions(self):
        x = ''
        for perm in self.permissions:
            x = x+'    '+perm+'\n'
        return x


class ApkParser(object):
    """Parser of .apk files, parsing output of aapt dump badging

        Instantiate with: RespContext(username, password, apk, resp_addr, debug=False)


            username - gmail account username
            password - gmail account password
            apk - apk file with absolute path e.g. /tmp/test.apk
            resp_addr - e-mail address of the apk file sender
            debug - verbosity of the instance, True for high, False(default) for low.

        """
    def __init__(self, username, password, apk, resp_addr, debug=False):
        self.username = username
        self.password = password
        self.apk = apk
        self.resp_addr = resp_addr
        self.debug = debug

    def send_answer(self, text, subject):
        """Universal method for sending e-mail answer, using instance variable

        :param text: text part of the response
        :param subject: subject of the e-mail response
        """
        # change the host:port for other mail-server if needed.
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(self.username, self.password)
        # create string representation of e-mail body with subject
        message = 'To: {}\nSubject: {}\n\n{}'.format(self.resp_addr, subject, text)
        if str(self.username).find('@gmail.com') > -1:
            server.sendmail(self.username, self.resp_addr, message)
        else:
            # if using other then gmail account, change appropriately
            server.sendmail(self.username+'@gmail.com', self.resp_addr, message)

    def pars_sdk(self):
        """ run aapt on given path and create the RespContext instance, with parsed information

        this method:
            run and parse .apk file (from instance variable)
            send the outcome information
            delete apk from the server
        """
        try:
            output = subprocess.check_output(["aapt", "dump", "badging", self.apk])
            resp_data = RespContext()
            # parse output, if the output of aapt would change in newer version, appropriated changes are needed
            for line in output.decode("utf-8").splitlines():
                split_line = line.split("'")
                # get package name and app version
                if split_line[0] == "package: name=":
                    resp_data.name = split_line[1]
                    resp_data.app_version = split_line[5]
                    continue
                # get min sdk version
                if split_line[0] == "sdkVersion:":
                    resp_data.min_sdk = split_line[1]
                    continue
                # get targeted sdk version
                if split_line[0] == "targetSdkVersion:":
                    resp_data.target_sdk = split_line[1]
                    continue
                # get permission
                if split_line[0] == "uses-permission: name=":
                    resp_data.set_permissions(split_line[1])
                    continue
                # get Application-label
                if split_line[0] == "application-label:":
                    resp_data.app_label = split_line[1]
                    continue
                # get Launchable-activity
                if split_line[0] == "launchable-activity: name=":
                    resp_data.launch_activity = split_line[1]
                    continue

            # get file name of the parsed apk
            resp_data.file_name = os.path.basename(self.apk)
            # send answer
            self.send_answer(str(resp_data), 'Re:APK')
        # catch error, if apk is not valid or damaged it will inform the sender about the situation.
        except subprocess.CalledProcessError as e:
            if self.debug:
                print(e.output)
            self.send_answer("Not valid APK.")

        # remove directory with .apk file
        shutil.rmtree(os.path.dirname(self.apk))

if __name__ == "__main__":
    # prepare for help and parsing arguments from terminal
    parser = argparse.ArgumentParser(description='For given e-mail and path to apk file, it will run aapt for given '
                                                 'apk and send parsed report to the given e-mail address.')
    # to modify output if -h is used to mark arguments as required
    parser_group = parser.add_argument_group('required named arguments')

    parser_group.add_argument("-u", "--username", type=str, help="google account login name", required=True)
    parser_group.add_argument("-p", "--password", type=str, help="google account password", required=True)
    parser_group.add_argument("-a", "--apk", type=str, help="apk file to be parsed.", required=True)
    parser_group.add_argument("-r", "--resp", type=str, help="e-mail address, where to send the parsed information", required=True)
    parser_group.add_argument("-v", "--verbose", action="store_true", help="show debug output")

    args = parser.parse_args()
    # create instance of the parser with all needed inputs
    a = ApkParser(username=args.username, password=args.password, apk=args.apk, resp_addr=args.resp, debug=args.verbose)
    # run & parse & send & delete
    a.pars_sdk()
