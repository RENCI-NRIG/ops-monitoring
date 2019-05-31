#!/usr/bin/python
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

import os


def main():

    # assumes web_server.py (flask) is running, and the local
    # datastore unit test has consistent data

    # Info url
    datastore_info_url = "http://127.0.0.1:5000/info/"
    #datastore_info_url = "http://starkville.bbn.com/info/"

    # Aggregate ID to look up in collector db
    aggregate_id = "gpo-ig"

    # Drops and creates tables at collector
    os.system("python collector_table_reset.py");

    # Performs the info crawling
    os.system("cd ../; python single_local_datastore_info_crawler.py -b " + datastore_info_url + " -a " +  aggregate_id + " -o ni; cd -;")

    # Performs a single fetch for node types at aggregate (node: -o n)
    os.system("cd ../; python single_local_datastore_object_type_fetcher.py -a gpo-ig -o n; cd -;")

    # Performs a single fetch for interface types at aggregate (interface: -o i)
    os.system("cd ../; python single_local_datastore_object_type_fetcher.py -a gpo-ig -o i; cd -;")

   # Performs a single fetch for node types at aggregate (node: -o n)
    os.system("cd ../; python single_local_datastore_object_type_fetcher.py -a gpo-ig -o n; cd -;")

    # Performs a single fetch for interface types at aggregate (interface: -o i)
    os.system("cd ../; python single_local_datastore_object_type_fetcher.py -a gpo-ig -o i; cd -;")


if __name__ == "__main__":
    main()
