#----------------------------------------------------------------------
# Copyright (c) 2014 Raytheon BBN Technologies
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

import sys
import json
import getopt
from pprint import pprint as pprint
local_path = "../"
common_path = "../../common/"

sys.path.append(local_path)
sys.path.append(common_path)
import os
import table_manager
import opsconfig_loader
import info_populator

def usage():
    print('local_restart_config_datastore.py')
    sys.exit(2)

def parse_args(argv):
    base_url = "http://127.0.0.1:5000"

    try:
        opts, args = getopt.getopt(argv,"hb:",["baseurl="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt == '-h':
            usage()
        elif opt in ("-b", "--baseurl"):
            base_url = arg
        elif opt in ("-n", "--nodeid"):
            node_id = arg
        elif opt in ("-i", "--interfaceid"):
            interface_id = arg
        elif opt in ("-r", "--numinserts"):
            num_ins = int(arg)
        elif opt in ("-s", "--sleepperiodsec"):
            per_sec = float(arg)

    return [base_url]

            
def main(argv):

    [base_url] = parse_args(argv)

    os.system("python local_table_reset.py")

    db_type = "local"
    config_path = "../../config/"
    debug = False
    tbl_mgr = table_manager.TableManager(db_type, config_path, debug)

    # info population
    ip = info_populator.InfoPopulator(tbl_mgr, base_url)
    ip.init_config_datastore_info()
    
    tbl_mgr.con.close()

if __name__ == "__main__":
    main(sys.argv[1:])
