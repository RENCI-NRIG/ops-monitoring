#----------------------------------------------------------------------
# Copyright (c) 2014-2015 Raytheon BBN Technologies
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and/or hardware specification (the "Work") to
# deal in the Work without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Work, and to permit persons to whom the Work
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Work.
#
# THE WORK IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE WORK OR THE USE OR OTHER DEALINGS
# IN THE WORK.
#----------------------------------------------------------------------
import logging

# Keeping track if we have loaded the logged configuration yet
global __loaded_config__
__loaded_config__ = False

def load_log_config(config_path):
    """
    Function to load the logging configuration for ops monitoring
    :param config_path: the path to the ops-monitoring configuration folder
    """
    global __loaded_config__
    import logging.config
    fullpath = config_path
    if config_path[len(config_path) - 1] != '/':
        fullpath += '/'
    fullpath += "logging.conf"
    logging.config.fileConfig(fullpath)
    __loaded_config__ = True

def get_logger(config_path="/usr/local/ops-monitoring/config"):
    """
    Function to get the ops-monitoring logger object
    :param config_path: the path to the ops-monitoring configuration folder
    :return: the ops-monitoring logger object, configured according to the logging configuration file.
    """
    global __loaded_config__
    if not __loaded_config__:
        load_log_config(config_path)
    return logging.getLogger("opsmon")

def configure_logger_for_debug_info(config_path):
    """
    Function to change the logging configuration to make sure that logging handlers are at least configure to handle the INFO level.
    """
    opslog = get_logger(config_path)
    for handl in opslog.handlers:
        if logging.INFO < handl.level:
            handl.setLevel(logging.INFO)

