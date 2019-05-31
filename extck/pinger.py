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


import subprocess
import ConfigParser
import sys
import getopt
import time
import multiprocessing.pool
import exceptions

def usage():
    print "pinger options"
    print "   -o filename"
    print "   --outfile=filename"
    print "     location of the output file containing the ping rtt results"
    print "   -c configurationFile"
    print "   --configpath=configurationFile"
    print "     location of the configuration file containing the ping destination site names and IP addresses"
    print "   -s pingSource"
    print "   --sourcename=pingSource"
    print "     site name of the source (a.k.a nickname of the site running the pings)"
    print "   -t pingType"
    print "   --type=pingType"
    print "     type of pings (campus or core), which is also the section to look up in the configuration file."
    print "   -p size"
    print "   --poolsize=size"
    print "     size of the process pool that will be used (if the host support python multiprocessing module)"
    print "   -i initialPingCount"
    print "   --inipingcount=initialPingCount"
    print "     ping count to use when \"priming\" the openFlow flows)"
    print "   -m measurePingCount"
    print "   --measpingcount=measurePingCount"
    print "     ping count to use when measuring the ping rtt)"
    sys.exit(0)

def parse_args(argv):
    out_file = ""
    config_path = ""
    source_name = ""
    try:
        opts, _args = getopt.getopt(argv, "o:c:s:t:p:i:m:",
                                    ["outfile=", "configpath=", "sourcename=", "type=", "poolsize=", "inipingcount=", "measpingcount="])
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:

        if opt in ("-o", "--outfile"):
            out_file = arg
        elif opt in ("-c", "--configpath"):
            config_path = arg
        elif opt in ("-s", "--sourcename"):
            source_name = arg
        elif opt in ("-t", "--type"):
            ping_type = arg
        elif opt in ("-p", "--poolsize"):
            pool_size = int(arg)
        elif opt in ("-i", "--inipingcount"):
            ini_ping_count = int(arg)
        elif opt in ("-m", "--measpingcount"):
            meas_ping_count = int(arg)
        else:
            usage()

    return [out_file, config_path, source_name, ping_type, pool_size, ini_ping_count, meas_ping_count]


def ping(dst_addr, count):
    """
    """
    wrote_output = False
    try:
        output = (subprocess.Popen(["ping", "-c", str(count), dst_addr], stdout=subprocess.PIPE).stdout.read().split('/')[3])
        delay_ms = (output.split("="))[1]
    except Exception, _e:
        try:
            output = (subprocess.Popen(["ping", "-c", str(count), dst_addr], stdout=subprocess.PIPE).stdout.read().split('/')[3])
            delay_ms = (output.split("="))[1]
        except Exception, _e:
            delay_ms = -1
            sys.stdout.write("a")
            wrote_output = True
    return delay_ms, wrote_output

def run_ping_in_process((dst_addr, experiment_id, ini_ping, meas_ping)):
    output = False
    (_, tmp_output) = ping(dst_addr, ini_ping)
    if tmp_output: output = True
    # Running a second set of pings so that we eliminate the possible
    # delays seen when the first set of pings is affected by the flows
    # being set up on the OpenFlow switches.
    (delay_ms, tmp_output) = ping(dst_addr, meas_ping)
    if tmp_output: output = True
    ts = str(int(time.time() * 1000000))
    # Assembling the result string for this ping set
    strres = "('" + experiment_id + "'," + ts + "," + str(delay_ms) + ")" + "\n"
    return output, strres

class Pinger:

    def __init__(self, out_file, config_path, source_name, ping_type, pool_size, ini_ping_count, meas_ping_count):

        self.out_file = out_file
        self.srcSite = source_name
        self.ping_type = ping_type
        self.pool_size = pool_size
        self.ini_ping_count = ini_ping_count
        self.meas_ping_count = meas_ping_count
        config = ConfigParser.ConfigParser()
        config.read(config_path)
        self.ip_list = dict(config.items(ping_type))
        self.run_pings(self.ip_list)


    def run_pings(self, ipList):
        output = False
        argListArray = []
        for dstSite in ipList:
            if self.srcSite == dstSite:
                # No "self" pinging
                continue

            experiment_id = self.srcSite + "_to_" + dstSite
            if self.ping_type == 'campus':
                experiment_id = experiment_id + "_campus"
            else:
                dstSiteFlag = dstSite.strip().split('-')
                srcSiteFlag = self.srcSite.strip().split('-')
                if srcSiteFlag[2] != dstSiteFlag[2]:
                    # Can't ping between hosts in different networks
                    continue

            dst_addr = ipList[dstSite]
            # build argument list for process pool
            argList = [dst_addr, experiment_id, self.ini_ping_count, self.meas_ping_count]
            argListArray.append(argList)


        # create process pool - use the map() method with the argument list built above
        try :
            pool = multiprocessing.pool.ThreadPool(processes=self.pool_size)
            parallel = True
        except exceptions.OSError:
            parallel = False
        if parallel:
            resArray = pool.map(run_ping_in_process, argListArray)
        else:
            # We'll run sequentially then...
            resArray = []
            for argList in argListArray:
                tuple_result = run_ping_in_process(tuple(argList))
                resArray.append(tuple_result)

        file_handle = open(self.out_file, 'w')
        for (thread_output, res_str) in resArray:
            if thread_output:
                output = True
            file_handle.write(res_str)

        file_handle.close()
        if output:
            print

def main(argv):
#     multiprocessing.util.log_to_stderr(multiprocessing.util.DEBUG)
    [out_file, config_path, source_name, ping_type, pool_size, ini_ping_count, meas_ping_count] = parse_args(argv)
    _pinger = Pinger(out_file, config_path, source_name, ping_type, pool_size, ini_ping_count, meas_ping_count)


if __name__ == "__main__":
    main(sys.argv[1:])
