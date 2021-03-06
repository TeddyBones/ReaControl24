"""Control24 common functions and default settings"""

import binascii
import datetime
import logging
import optparse
import os
import time

import netifaces

'''
    This file is part of ReaControl24. Control Surface Middleware.
    Copyright (C) 2018  PhaseWalker

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

DEFAULTS = {
    'ip':'0.0.0.0',
    'daemon':9123,
    'control24osc':9124,
    'oscDaw':9125,
    'auth':'be_in-control',
    'loglevel':logging.INFO,
    'interface':'en0',
    'scribble':'/track/c24scribstrip/name',
    'logdir':'./logs',
    'logformat':'%(asctime)s\t%(name)s\t%(levelname)s\t' +
                '%(threadName)s\t%(funcName)s\t%(lineno)d\t%(message)s'
}

CHANNELS = 24
FADER_RANGE = 2**10
FADER_STEP = 1 / float(FADER_RANGE)


def tick():
    """Wrapper for a common definition of execution seconds"""
    return time.time()

def fix_ownership(path):
    """Change the owner of the file to SUDO_UID"""

    uid = os.environ.get('SUDO_UID')
    gid = os.environ.get('SUDO_GID')
    if uid is not None:
        os.chown(path, int(uid), int(gid))

def start_logging(name, logdir, debug=False):
    """Configure logging for the program"""
    # Set logging
    logformat = DEFAULTS.get('logformat')
    loghead = ''.join(c for c in logformat if c not in '$()%')
    # Get the root logger and set up outputs for stderr
    # and a log file in the CWD
    if not os.path.exists(logdir):
        try:
            original_umask = os.umask(0)
            os.makedirs(logdir, 0o666)
            fix_ownership(logdir)
        finally:
            os.umask(original_umask)

    root_logger = logging.getLogger(name)
    if debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(DEFAULTS.get('loglevel'))
    log_f = logging.FileHandler('{}/{}.log.{:%d_%m.%H_%M}.csv'.format(
        logdir,
        name,
        datetime.datetime.now()))
    root_logger.addHandler(log_f)
    # First line be the header
    root_logger.info(loghead)
    # Subsequent lines get formatted
    log_formatter = logging.Formatter(logformat)
    log_f.setFormatter(log_formatter)
    log_s = logging.StreamHandler()
    # if this inherits root logger level then remove else put back: log_s.setLevel()
    root_logger.addHandler(log_s)
    return root_logger


def opts_common(desc):
    """Set up an opts object with options we use everywhere"""
    fulldesc = desc + """
        part of ReaControl24  Copyright (c)2018 Phase Walker 
        This program comes with ABSOLUTELY NO WARRANTY;
        This is free software, and you are welcome to redistribute it
        under certain conditions; see COPYING.md for details."""
    oprs = optparse.OptionParser(description=fulldesc)
    oprs.add_option(
        "-d",
        "--debug",
        dest="debug",
        action="store_true",
        help="logger should use debug level. default = off / INFO level")
    logdir = DEFAULTS.get('logdir')
    oprs.add_option(
        "-o",
        "--logdir",
        dest="logdir",
        help="logger should create dir and files here. default = %s" % logdir)
    oprs.set_defaults(debug=False, logdir=logdir)
    return oprs


def format_ip(ipaddr, port):
    """from ip and port provide a string with ip:port"""
    return '{}:{}'.format(ipaddr, port)


def ipv4(interface_name=None):
    """ Get an IPv4 address plausible default. """
    # to not take into account loopback addresses (no interest here)
    ifaces = netifaces.interfaces()
    default_interface = DEFAULTS.get('interface')
    default_address = DEFAULTS.get('ip')
    found = False
    if not interface_name is None and not interface_name in ifaces:
        raise KeyError('%s is not a valid interface name' % interface_name)
    for interface in ifaces:
        if interface_name is None or unicode(interface_name) == interface:
            config = netifaces.ifaddresses(interface)
            # AF_INET is not always present
            if netifaces.AF_INET in config.keys():
                for link in config[netifaces.AF_INET]:
                    # loopback holds a 'peer' instead of a 'broadcast' address
                    if 'addr' in link.keys() and 'peer' not in link.keys():
                        default_interface = interface
                        default_address = link['addr']
                        found = True
                        break

    if not interface_name is None and not found:
        raise LookupError(
            '%s interface has no ipv4 addresses' % interface_name)

    return default_interface, default_address

def hexl(inp):
    """Convert to hex string using binascii but
    then pretty it up by spacing the groups"""
    shex = binascii.hexlify(inp)
    return ' '.join([shex[i:i+2] for i in range(0, len(shex), 2)])
