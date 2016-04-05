import logging
from argparse import ArgumentParser
from utils import maintools

logger = logging.getLogger('wwmode_app')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('logs/devdb.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    '%d %B %Y %H:%M:%S.%03d')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

parser = ArgumentParser()
action = parser.add_mutually_exclusive_group(required=True)
action.add_argument('-U', '--update', dest='action', action='store_const',
                    const='update', help='start DB update procedure')
action.add_argument('-S', '--show', dest='action', action='store_const',
                    const='show', help='fetch info about devices & print it')
action.add_argument('-G', '--generate', dest='action', action='store_const',
                    const='generate', help='generate usefull lists from DB')
group_s = parser.add_argument_group('-S', 'show options')
group_s.add_argument('-a', '--show-all', dest='show_all', action='store_true',
                     help='show all devices in compressed fashion')
group_s.add_argument('-d', '--device', dest='show_dev', metavar='DEVICE',
                     help='show full device card chosen by FQDN or IP')
group_s.add_argument('-i', '--inactive', dest='inactive', action='store_true',
                     help='show devices that was not found in last update')
group_s.add_argument('-c', '--chain', dest='uplink_chain',
                     metavar='DEVICE', help='show device uplink chain')
group_s.add_argument('-v', '--vlan-chain', dest='find_vlan', metavar='VLAN',
                     help='show devices chain with VLAN configured')
group_s.add_argument('-f', '--full-search', dest='full_search',
                     metavar='SEARCH',
                     help='show compressed device cards where SEARCH was found')
group_s.add_argument('-m', '--model', dest='model_search', metavar='MODEL',
                     help='show devices wich model name contain MODEL')
group_s.add_argument('-t', '--older-than', dest='older_software',
                     metavar=('MODEL', 'VERSION'), nargs=2,
                     help='''show all switches of MODEL with older VERSION of
                     software''')
group_s.add_argument('-o', '--outdated', dest='outdated', action='store_true',
                     help='show devices with outdated software')
group_g = parser.add_argument_group('-G', 'generate option')
group_g.add_argument('-T', '--tacacs', dest='tacacs', action='store_true',
                     help='generate list of hosts for TACACS+')
group_g.add_argument('-N', '--nagios', dest='nagios', action='store_true',
                     help='generate list of hosts for Nagios')
group_g.add_argument('-D', '--dns', dest='dns', action='store_true',
                     help='generate list of hosts for DNS')
group_g.add_argument('-K', '--kbase', dest='kbase', action='store_true',
                     help='generate list of hosts for Trac knowledge base')
group_g.add_argument('-R', '--rancid', dest='rancid', action='store_true',
                     help='generate list of hosts for RANCID')
args = parser.parse_args()


def update_cmd():
    '''Interlayer function for different update command execution
    based on provided CLI args
    '''
    maintools.update_db_run()


def show_cmd():
    '''Interlayer function for different show command execution
    based on provided CLI args
    '''
    if args.show_all:
        maintools.show_all_records()
    elif args.show_dev:
        maintools.show_single_device(args.show_dev)
    elif args.inactive:
        maintools.show_all_records(inactive=True)
    elif args.uplink_chain:
        maintools.go_high(args.uplink_chain)
    elif args.find_vlan:
        maintools.search_db('vlans', args.find_vlan)
    elif args.model_search:
        maintools.search_db('model', args.model_search)
    elif args.full_search:
        maintools.search_db('full', args.full_search)
    elif args.older_software:
        maintools.software_search(*args.older_software)
    elif args.outdated:
        for model, version in maintools.find_newest_firmware():
            maintools.software_search(model, version)


def generate_cmd():
    '''Interlayer function for different generate command execution
    based on provided CLI args
    '''
    if args.tacacs:
        maintools.generate_tacacs_list()

action_dict = {
    'update': update_cmd,
    'show': show_cmd,
    'generate': generate_cmd
}
action_dict[args.action]()
