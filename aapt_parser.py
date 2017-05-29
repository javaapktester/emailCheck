import smtplib
import subprocess
import argparse


class RespContext(object):
    def __init__(self):
        self.name = ''
        self.min_sdk = ''
        self.target_sdk = ''
        self.permissions = []
        self.app_version = ''
        self.launch_activity = ''
        self.app_label = ''

    # TODO: correct the output
    def __str__(self):
        return '''
        Min SDK: {}
        Target SDK: {}
        Package name: {}
        App version: {}
        Launchable-activity: {}
        Application-label: {}
        Permissions: {}
        '''.format(self.min_sdk, self.target_sdk, self.name, self.app_version,
                   self.launch_activity, self.app_label, self.str_permissions())

    def set_permissions(self, new_permission):
        self.permissions.append(new_permission)

    def str_permissions(self):
        x = ''
        for perm in self.permissions:
            x = x+'    '+perm+'\n'
        return x


class ApkParser(object):
    def __init__(self, username, password, apk, resp_addr, debug=False):
        self.username = username
        self.password = password
        self.apk = apk
        self.resp_addr = resp_addr
        self.debug = debug

    def send_answer(self, text):
        # TODO add subject
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(self.username, self.password)
        if str(self.username).find('@gmail.com') > -1:
            server.sendmail(self.username, self.resp_addr, text)
        else:
            server.sendmail(self.username+'@gmail.com', self.resp_addr, text)

    def pars_sdk(self):
        # run aapt on given path
        try:
            output = subprocess.check_output(["aapt", "dump", "badging", self.apk])
            resp_data = RespContext()
            # parse output
            for line in output.decode("utf-8").splitlines():
                split_line = line.split("'")
                if split_line[0] == "package: name=":
                    resp_data.name = split_line[1]
                    resp_data.app_version = split_line[5]
                    continue
                if split_line[0] == "sdkVersion:":
                    resp_data.min_sdk = split_line[1]
                    continue
                if split_line[0] == "targetSdkVersion:":
                    resp_data.target_sdk = split_line[1]
                    continue
                if split_line[0] == "uses-permission: name=":
                    resp_data.set_permissions(split_line[1])
                    continue
                if split_line[0] == "application-label:":
                    resp_data.app_label = split_line[1]
                    continue
                if split_line[0] == "launchable-activity: name=":
                    resp_data.launch_activity = split_line[1]
                    continue

            # send answer
            self.send_answer(str(resp_data))
            # delete dir
            # TODO: delete the dir
        # catch error
        except subprocess.CalledProcessError as e:
            if self.debug:
                print(e.output)
            self.send_answer("Not valid APK.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='For given e-mail and path to apk file, it will run aapt for given '
                                                 'apk and send parsed report to the given e-mail address.')
    parser_group = parser.add_argument_group('required named arguments')
    parser_group.add_argument("-u", "--username", type=str, help="google account login name", required=True)
    parser_group.add_argument("-p", "--password", type=str, help="google account password", required=True)
    parser_group.add_argument("-a", "--apk", type=str, help="apk file to be parsed.", required=True)
    parser_group.add_argument("-r", "--resp", type=str, help="e-mail address, where to send the parsed information", required=True)
    parser_group.add_argument("-v", "--verbose", action="store_true", help="show debug output")

    args = parser.parse_args()
    a = ApkParser(username=args.username, password=args.password, apk=args.apk, resp_addr=args.resp, debug=args.verbose)
    a.pars_sdk()
