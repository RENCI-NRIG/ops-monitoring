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


import subprocess
import ConfigParser
import sys
import getopt
import subprocess
import time

def usage():
    print "pinger --outfile filename --configpath pathWithoutFile"
    sys.exit(0)

def parse_args(argv):
    out_file = ""
    config_path = ""
    source_name = ""
    try:
        opts, args = getopt.getopt(argv,"o:c:s:",["outfile=","configpath=","sourcename="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:

        if opt in ("-o", "--outfile"):
            out_file = arg
        elif opt in ("-c", "--configpath"):
            config_path = arg
        elif opt in ("-s", "--sourcename"):
            source_name = arg
        else:
            usage()

    return [out_file, config_path, source_name]

class Pinger:

    def __init__(self, out_file, config_path, source_name):

        self.file_handle = open(out_file,'w')
        self.srcSite = source_name
        config = ConfigParser.ConfigParser()
        config.read(config_path)
        self.ip_campus = dict(config.items("campus"))
        self.ip_core = dict(config.items("core"))
        ipListFlag=self.srcSite.strip().split('-')
        if len(ipListFlag) == 2:
             self.run_pings(self.ip_campus)
        else:
             self.run_pings(self.ip_core)
        self.file_handle.close()


    def run_pings(self, ipList):
        for dstSite in ipList:
             if self.srcSite != dstSite: # No "self" pinging
                 passFlag = 0
                 dstSiteFlag=dstSite.strip().split('-')
                 if len(dstSiteFlag) ==2:
                     dstString = dstSite + "_campus"
                 else:
                     dstString = dstSite
                     srcSiteFlag=self.srcSite.strip().split('-')
                     if srcSiteFlag[2] != dstSiteFlag[2]:
                         passFlag=1
                         pass # Can't ping between hosts in different networks 
                 if passFlag == 1:
                     pass 
                 else:                      
                     dst_addr = ipList[dstSite]
                     delay_ms = None
                     try:
                         delay_ms = (subprocess.Popen(["ping", "-c 6",  dst_addr], stdout=subprocess.PIPE).stdout.read().split('/')[3])
                         delay_ms = (delay_ms.split("="))[1]
                     except Exception, e:
                         try:
                             delay_ms = (subprocess.Popen(["ping", "-c 6",  dst_addr], stdout=subprocess.PIPE).stdout.read().split('/')[3])
                             delay_ms = (delay_ms.split("="))[1]
                         except Exception, e:
                             delay_ms = -1
                             print "a"
                     ts = str(int(time.time()*1000000))
                     self.file_handle.write("('" + self.srcSite + "_to_" + dstString + "'," + ts + "," + str(delay_ms) + ")" + "\n")

def main(argv):

    [out_file, config_path, source_name] = parse_args(argv)
    pinger = Pinger(out_file, config_path, source_name)

if __name__ == "__main__":
    main(sys.argv[1:])
