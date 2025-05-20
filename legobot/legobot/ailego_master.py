import string
import datetime
from os.path import expanduser
import json
import threading
from contextlib import contextmanager
from getpass import getpass
import paramiko
from .read_config import get_profile


# NOTES:
# This is a cleaned version without 'silent' keyword
# This version does not use a logger to avoid potential errors
# This version has the IDMaker directly in this file
# Removed keeping track of volumes to keep it simple
# Removed "fill_fifth function"


class AiLEGO_master(object):
    """
    A class used to control and the 1D LEGO robot
    The master part of the module
    """

    ALLOWED_COLORS = ['red_t', 'green_t', 'blue_t', 'yellow_t', 'red_u',
                      'yellow_u', 'green_u', 'purple_u']

    def __init__(self, id=None, x_offset=0.0, speak_only=False,
                 local_ssh=True, ssh_profile=None,
                 colors=['red_u', 'green_u', 'blue_t', 'yellow_u']):
        """
        id: str
            The ID given to the instance. Will default to numbers based on
            exact time of initialization
        x_offset: float
            Constant displacement to be applied to x position of cuvettes and
            resevoirs hardcoded in the AiLEGO robot
        speak_only: bool
            If True, initializes a "light" version of the class useable if you
            only want to make to robot speak
        local_ssh: bool
            False: '.eduroam.wireless.dtu.dk' appended to device name and used
                   as ip for ssh connection
            True: manually specify full ip or hostname
        colors: list of strings
            Specify the colors loaded in the color cartridges from left to
            right.
            Possible colors: 'red_t', 'green_t', 'blue_t', 'yellow_t', 'red_u',
                             'yellow_u', 'green_u', 'purple_u'
        """
        if not id:
            self.id = id_maker()
        else:
            self.id = id

        self.x_offset = x_offset

        if not all(elem in self.ALLOWED_COLORS for elem in colors):
            raise ValueError('"colors" can only contain colors in \n' +
                             str(self.ALLOWED_COLORS))
        if len(colors) != 4:
            raise TypeError('"colors" must contain 4 entries')
        self.colors = colors

        self.name = 'robot'
        self.get_ssh_credentials(ssh_profile)
        if local_ssh:
            self.ip = self.device
        else:
            self.ip = self.device + '.eduroam.wireless.dtu.dk'

        self.speak_only = speak_only

        self.color_offset = 1.0

        self.positions = {'1': 2.9,
                          '2': 3.40,
                          '3': 3.9,
                          '4': 4.4,
                          '5': 4.9,
                          '6': 5.4,
                          '7': 5.9,
                          '8': 6.4,
                          '9': 6.9,
                          '10': 7.4,
                          'blue': 8.35,
                          'red': 0.95,
                          'green': 1.9,
                          'yellow': 9.3,
                          'rinse1': 0.,
                          'rinse2': 10.35}

        if speak_only:
            return

        self.home = expanduser("~")
        try:
            with open(self.home + '/47332/data/' + self.id + '.log', 'a') as f:
                print('Colors', 'Cuvette#', 'V_colors', 'rgb', file=f)
        except Exception:
            with open(self.id + '.log', 'a') as f:
                print('Colors', 'Cuvette#', 'V_colors', 'rgb', file=f)

        input("Verify that syringe is at the top positon and the plunger fully"
              " pressed. Then press ENTER")
        input("Verify that color cartridges are filled and cuvettes empty (#5"
              " can be filled). Then press ENTER")

        self.next_cuvette = 1

        # test_positions_input = input('Do you want to test positions? (y/n): ')
        # while True:
        #     if test_positions_input == 'y':
        #         test_positions = True
        #         break
        #     elif test_positions_input == 'n':
        #         test_positions = False
        #         break
        #     else:
        #         test_positions_input = input('Type y or n. Then press ENTER')

        # while test_positions:
        #     self.test_positions(offset=self.x_offset)
        #     pos_ok = input('Are positions okay? (y/n): ')
        #     if pos_ok in ['y', 'Y', 'yes', 'Yes']:
        #         break
        #     else:  # pos_ok == 'n':
        #         self.x_offset = input('Specify offset: ')

    def get_ssh_credentials(self, ssh_profile):
        if ssh_profile is None:
            # No profile was provided
            self.device = str(input("Robot's IP address):"))
            self.password = getpass('Robot password:')
            return
        profile = get_profile(ssh_profile)
        self.device = profile["IP"]
        self.password = profile["PASSWORD"]

    def set_positions(self, pos):
        """ pos is a dict of form
        positions = {'1': 2.9,  # 3.1 before
                         '2': 3.40,
                         '3': 3.9,  # was 4.15 before
                         '4': 4.4,
                         '5': 4.9,
                         '6': 5.4,
                         '7': 5.9,
                         '8': 6.4,
                         '9': 6.9,
                         '10': 7.4,
                         'blue': 8.35,
                         'red': 0.95,
                         'green': 1.9,
                         'yellow': 9.3,
                         'rinse1': 0.,
                         'rinse2': 10.35}
        """
        self.positions = pos

    def set_color_offset(self, offset):
        """
        The program thinks there is a distance of 1.0 between syrringe
        and rgb sensor. If the color reader is not ligning up correctly,
        you can adjust it by specifying the color offset.

        offset: float
            Normally around 1.0
        """
        self.color_offset = offset

    def dict_to_string(self, my_dict):
        return "'" + json.dumps(my_dict) + "'"

    def set_offset(self, offset):
        """
        Specifies an offset to all positions

        offset: float
        """
        self.x_offset = offset
        return

    def get_id(self):
        return self.id

    def read_color(self, cuvette, offset=0.0):
        """
        Read the color of target cuvette

        cuvette: int
            The cuvette you read the color from
        offset: float
            Offset in x positions to ensure syrringe hits targets
            Will use self.x_offset if not specified
        """
        if self.speak_only:
            raise Exception('You have initilized an instance of the '
                            'calculator only for making the robot speak')
        cuvette = int(cuvette)
        max_cuvette = 10
        if cuvette > max_cuvette:
            raise Exception('Cuvette number must be between 1 and 10')
        # print(color_id)
        command = ('python3 read_color.py --ID ' + self.id +
                   ' --xoffset ' + str(offset) +
                   ' --cuvette ' + str(cuvette) +
                   ' --colorx ' + str(self.color_offset) +
                   ' --pos ' + self.dict_to_string(self.positions))

        output_raw = self.ssh_into_robot(command)
        output = output_raw[-1]  # READS LAST LINE

        output_list = output.split(';')

        rgb = eval(output_list[0])

        return rgb

    def normalize_volume(self, color_list, target_volume=3.5):
        """Normalizes the input color list volumes to some total volume sum.
        Outputs list of same length as input list.
        """
        sum_list = sum(color_list)
        return [target_volume / sum_list * i for i in color_list]

    def run_cuvette(self, rough_color_list,
                    cuvette=None,
                    offset=None, read_target=False):
        """
        rough_color_list: list
            Unnormalized list of color ratios in format:
                [red, green, blue, yellow]
        cuvette: int
            The number of the cuvette being mixed in
            Will be self.next_cuvette if not specified
        offset: float
            Offset in x positions to ensure syrringe hits targets
            Will use self.x_offset if not specified
        read_target: bool
            if True, will also read rgb of '5'

        returns:
            (r,g,b) if read_target=False
            (r,g,b), (r5,g5,b5) if read_target=True
        """

        if self.speak_only:
            raise Exception('You have initilized an instance of the '
                            'calculator only for making the robot speak')
        # if read_target:
        #    input('Verify that target color is in '
        #          'cuvette 5. Then press ENTER')

        if cuvette is None:
            cuvette = self.next_cuvette
        else:
            cuvette = int(cuvette)
        # if cuvette == 1:
        #     cuvette = 2  # Skip number 1. Too much noise at edge
        #     self.next_cuvette = 2
        if cuvette == 5:
            cuvette = 6  # Skip number 5. It is the sample
            self.next_cuvette = 6
        if offset is None:
            offset = self.x_offset
        max_cuvette = 10
        if cuvette > max_cuvette:
            raise Exception('Ran out of cuvettes')
        color_list = self.normalize_volume(rough_color_list)
        colors_string = '[' + ','.join([str(col) for col in color_list]) + ']'
        color_id = '[' + ','.join([str(col) for col in self.colors]) + ']'
        # print(color_id)
        command = ('python3 run_robot.py --ID ' + self.id +
                   ' --xoffset ' + str(offset) +
                   ' --cuvette ' + str(cuvette) +
                   ' --incolors ' + color_id +
                   ' --vcolors ' + colors_string +
                   ' --colorx ' + str(self.color_offset) +
                   ' --pos ' + self.dict_to_string(self.positions))

        # print(command)
        # print(read_target)
        if read_target:
            command = (command + ' --read_target')
        # print(command)  # FOR DEBUG

        output_raw = self.ssh_into_robot(command)
        # print(output_raw)
        self.next_cuvette += 1
        output = output_raw[-1]  # READS LAST LINE

        output_list = output.split(';')
        # print(output_list)

        rgb = eval(output_list[0])

        # print into data log here
        try:
            with open(self.home + '/47332/data/' + self.id + '.log', 'a') as f:
                print(self.colors, cuvette, rough_color_list, rgb, file=f)
        except:
            with open(self.id + '.log', 'a') as f:
                print(self.colors, cuvette, rough_color_list, rgb, file=f)

        if read_target:
            return rgb, eval(output_list[1])
        else:
            return rgb

    def set_first_empty_cuvette(self, empty_cuvette):
        """
        first empty cuvette: int
        """
        self.next_cuvette = int(empty_cuvette)

    def get_next_cuvette(self):
        """Returns what the instance thinks is the next empty cuvette"""
        return self.next_cuvette

    def test_positions(self, offset=None):
        """ Used to run test_positions_robot.py script on the robot"""
        with self.manage_process():
            if offset is None:
                offset = self.x_offset
            command = ('python3 test_positions_robot.py --ID ' + self.id
                    + ' --xoffset ' + str(offset) +
                    ' --colorx ' + str(self.color_offset) +
                    ' --pos ' + self.dict_to_string(self.positions))
            self.ssh_into_robot(command)

    def ssh_into_robot(self, command, check_if_busy=True):
        """
        command: str
           The command you wish to send to the robot
           e.g 'python3 run_robot.py --cuvette 8 --colorlist [0.6,0.2,0.1,0.1]'
        """
        cd_command = 'cd 47332-robotscripts/robotscripts; '
        ssh_client = self.get_ssh_client()

        if check_if_busy and self.is_busy(ssh_client=ssh_client):
            raise RuntimeError('The robot is already running a python process')
        stdin, stdout, stderr = ssh_client.exec_command(cd_command + command)
        output = stdout.readlines()
        error = stderr.readlines()
        for line in error:
            print(line)
        # for line in output:
        #    print(line)
        ssh_client.close()
        return output

    def get_ssh_client(self):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=self.ip,
                           username=self.name,
                           password=self.password)
        return ssh_client

    def is_busy(self, ssh_client=None):
        if ssh_client is None:
            ssh_client = self.get_ssh_client()
        stdin0, stdout0, stderr0 = ssh_client.exec_command(
            'pgrep python3 | wc -l')
        output0 = stdout0.readlines()
        if int(output0[0]) >= 1:
            return True
        return False

    def kill_process(self, ssh_client=None, check_busy=True):
        if ssh_client is None:
            ssh_client = self.get_ssh_client()
        if check_busy and not self.is_busy(ssh_client):
            return
        ssh_client.exec_command("pkill python3")
    
    def kill_in_thread(self):
        """Spawn a thread which sends off the pkill command."""
        thread = threading.Thread(target=self.kill_process, kwargs=dict(check_busy=False))
        thread.start()
        

    def make_robot_talk(self, say):
        """Makes the robot say the string you input

        say: str
            Specifies what your robot should say
        """
        command = ('python3 make_robot_speak.py --say "' + str(say) + '"')
        self.ssh_into_robot(command)

    def _git_pull(self):
        command = 'git pull; git reset --hard origin/main'
        self.ssh_into_robot(command, check_if_busy=False)
        
    @contextmanager
    def manage_process(self):
        try:
            yield
        except (Exception, KeyboardInterrupt) as exc:
            print("The process was interrupted. {}".format(str(exc)))
            self.kill_in_thread()
            
        


def id_maker():
    id_raw = datetime.datetime.now()
    id0 = str(id_raw).translate(str.maketrans('', '', string.punctuation))
    return id0.replace(' ', '')
