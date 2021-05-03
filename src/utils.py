import argparse
import sys
import pickle
import paramiko
from scp import SCPClient, SCPException

#global variables
args = None
debug = False
def print_trace(*params):
   if debug: print (params)

# functions for managing .config file
cfd = {}
def read_from_default_config():
    global cfd
    try:
        configFile = ".config" # config file name in the local dir
        cfh = open (configFile, 'rb')
        cfd = pickle.load(cfh)
        cfh.close()
        return cfd
    except:
        print_trace ('Unable to read config from default file ' + configFile)
        return None

def save_default_config(cfd):
    try:
        configFile = ".config" # config file name in the local dir
        cfh = open (configFile, 'wb')
        pickle.dump(cfd, cfh)
        cfh.close()
    except:
        print ("Unable to write config to default file " + configFile)


#helper functions
def get_name(args):
    global  cfd
    if args and args.name: return args.name
    if "name" in cfd.keys(): return cfd["name"]
    return None

def get_classname(args):
    global  cfd
    if args and args.classname: return args.classname
    if "classname" in cfd.keys(): return cfd["classname"]
    return None

def get_remote(args):
    global  cfd
    if args and args.remote: return args.remote
    if "remote" in cfd.keys(): return cfd["remote"]
    return None

def get_file(args):
    global  cfd
    if args and args.file: return args.file
    if "file" in cfd.keys(): return cfd["file"]
    return None

def get_id(args):
    global cfd
    if args and args.pem:
        idname = pem.name
        args.pem.close()
        return idname
    if "pem" in cfd.keys(): return cfd["pem"]
    return None


# add command line options
parser = argparse.ArgumentParser(description="Utilities file")
parser.add_argument('command', help='which operation to do', type=str)
parser.add_argument('--debug', help='enable debug trace messages', default=False, action='store_true')
parser.add_argument('--name', dest='name', help='your firstname', type=str, default=None)
parser.add_argument('--class', dest='classname', help='your classname', type=str, default=None)
parser.add_argument('--remote', dest='remote', type=str, help='remote computer for projects', default=None)
parser.add_argument('--id', dest='pem', type=argparse.FileType('r', encoding='UTF-8'), help='identity file', default=None)
parser.add_argument('--file', dest='file', type=str, help='file to upload or download', default=None)
args = parser.parse_args(sys.argv[1:])
debug = args.debug

# validate command
validCommands = ['configure', 'upload', 'download', 'list']
if args.command not in validCommands:
    print ("Unrecognized command: ", args.command, ". Valid values are ", repr(validCommands))
    print ("\nSee below for help\n")
    parser.parse_args(['-h'])
    sys.exit(0)

# implement configure command
if args.command == 'configure':

    if not args.name:
        print('Enter your name:')
        cfd["name"] = input()
    if not args.classname:
        print('Enter your class:')
        cfd["classname"] = input()
    if not args.pem:
        while True:
            print('Enter identity file:')
            filename = input()
            try:
                args.pem = open(filename)
            except:
                print("\nFile not found! Please enter a valid pem file name\n")
                continue
            cfd["pem"] = args.pem.name
            args.pem.close()
            break
    if not args.remote:
        print ('Enter remote server name:')
        cfd["remote"]  = input()

    print("Writing ", repr(cfd), " to default config")
    save_default_config(cfd)

#implement list command
if args.command == 'list':
    #read from default config if it exists
    read_from_default_config()

    # get the params
    name = get_name(args)
    classname = get_classname(args)
    remote = get_remote(args)
    pem = get_id(args)
    file = get_file(args)
    if not file: file = ''
    if not name or not remote or not pem or not classname:
        print ("\nRequired arguments not provided. Run \"python", sys.argv[0], "configure first !\"\n")
        print_trace(f'{name} {remote} {pem} {classname} {file}')
        sys.exit(0)

    # execute command
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print_trace (f'Connecting to {remote} as {classname} id={pem} command=ls -a {file}')
        client.connect(remote, username=classname, key_filename=pem)
        i, o, err = client.exec_command('ls -a ' + file)
        for line in o:
            print (line)
        client.close()
    except Exception as e:
        print (f"Got exception {e}")
        sys.exit(1)

#implement upload command
if args.command == 'upload':
    #read from default config if it exists
    read_from_default_config()

    # get the params
    name = get_name(args)
    classname = get_classname(args)
    remote = get_remote(args)
    pem = get_id(args)
    file = get_file(args)
    if not name or not remote or not pem or not classname or not file:
        print ("\nRequired arguments not provided. Run \"python", sys.argv[0], "configure first !\"\n")
        print_trace(f'{name} {remote} {pem} {classname} {file}')
        sys.exit(0)

    project_dir = remote.split('.')[0] + '/src'

    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print_trace (f'Connecting to {remote} as {classname} id={pem} uploading={name}.{file}')
        client.connect(remote, username=classname, key_filename=pem)
        print_trace ('client connected\n')
        scp = SCPClient(client.get_transport())
        print_trace ('scpclient created\n')
        scp.put (file, project_dir + '/' + name + '.' + file)
        print_trace ('scp done\n')
        i, o, err = client.exec_command('ls -al ' + project_dir)
        for line in o:
            print (line)
        scp.close()
        client.close()
    except Exception as e:
        print (f"Got exception {e}")
        sys.exit(1)


print_trace(args)

