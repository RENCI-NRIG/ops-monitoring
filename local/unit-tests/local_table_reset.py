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

import sys
import json

common_path = "../../common/"

sys.path.append(common_path)
import table_manager
import opsconfig_loader

def main():

    db_type = "local"
    config_path = "../../config/"
    tbl_mgr = table_manager.TableManager(db_type, config_path)
    tbl_mgr.poll_config_store()

    if not tbl_mgr.drop_all_tables():
        sys.stderr.write("\nCould not drop all tables.\n")
        sys.exit(-1)

    if not tbl_mgr.establish_all_tables():
        sys.stderr.write("\nCould not create all tables.\n")
        sys.exit(-1)

if __name__ == "__main__":
    main()
