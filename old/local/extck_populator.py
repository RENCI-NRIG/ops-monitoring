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
import sys
import time
import json
import ConfigParser
import subprocess

from pprint import pprint as pprint

common_path = "../common/"
# input file with short-names and Urls aggregates 
inputFile=open('/home/amcanary/src/gcf/agg_nick_cache.base')
# dic to store short name and corresponding url 
# Format: shortname [fqdn]=[aggShortName,amtype, state, timestamp]
# where state is 0 for up and 1 for down
shortName={}
sys.path.append(common_path)
import table_manager

class InfoPopulator():
    def __init__(self, tbl_mgr, url_base):

        self.tbl_mgr = tbl_mgr 
        self.url_base = url_base
        # steal config path from table_manager
        self.config_path = tbl_mgr.config_path

    def insert_agg_is_avail_datapoint(self,aggRow):
        # Insert into ops_externalcheck 
        agg_id = aggRow[0] # agg_id
        ts = aggRow[3]#str(int(time.time()*1000000))
        v = aggRow[2] 
        datapoint = [agg_id, ts, v]
        db_insert(self.tbl_mgr, "ops_aggregate_is_available", datapoint)  
        db_purge(self.tbl_mgr,"ops_aggregate_is_available")
            
def db_purge(tbl_mgr, table_str):
    old_ts = int((time.time()-.25*60*60)*1000000) # Purge data older than 12 hours
    tbl_mgr.purge_old_tsdata(table_str, old_ts)    


def db_insert(tbl_mgr, table_str, row_arr):
    val_str = "('"

    for val in row_arr:        
        val_str += val + "','" # join won't do this
    val_str = val_str[:-2] + ")" # remove last 2 of 3 chars: ',' and add )
    tbl_mgr.insert_stmt(table_str, val_str)
    
def getShortName():
    i=1
    for line in inputFile: # Read in line
        if line[0]!='#' and line[0]!='[' and line[0]!='\n': # Don't read comments/junk
            cols = line.strip().split('=')
            aggShortName=cols[0] # Grab shortname
            if aggShortName == "plcv3" or aggShortName == "plc3": # Only grab fqdn for aggShortName=plc
               continue
            cols1=cols[1].strip().split(',')
            cols2=cols1[1].strip().split('/')
            cols3=cols2[2].strip().split(':')
            fqdn=cols3[0] # Grab fqdn

            if aggShortName == "plc" or aggShortName=="ion":
                amtype="myplc"
            else: 
                amtype=cols2[3] # Grab amtype

            if is_empty(shortName) == "True": # If dic is empty
                shortName[fqdn]= [aggShortName,amtype]
            else:
                if shortName.has_key(fqdn): # If we have the shortName move to next line
                   continue 
                else:
                    shortName[fqdn]=[aggShortName,amtype]
    return shortName

def is_empty(any_structure): # Determine if "any_structure" is empty
    if any_structure:
       # print('Structure is not empty.')
        return False
    else:
       # print('Structure is empty.')
        return True
def getAMState(output):
    cols=output.strip().split(':')
    if cols[2] == " Timed out after 60 seconds": # Occurs if subprocess hangs 
        result =0
    elif cols[3]==" 0": # check for "returned: 0" output
        result="1" # Good result
    else:
        result="0" # Bad result   
    return result

def main():

   
    db_name = "local"
    config_path = "../config/"
    debug = False
    tbl_mgr = table_manager.TableManager(db_name, config_path, debug)
    tbl_mgr.poll_config_store()
    ip = InfoPopulator(tbl_mgr,"")

    # read list of urls (or short-names)
    shortName=getShortName()
    for fqdn in shortName:
        amtype = shortName[fqdn][1]
        p=subprocess.Popen(["/usr/local/bin/wrap_am_api_test", "genich",fqdn,amtype,"GetVersion"], stdout=subprocess.PIPE)            
        output, err = p.communicate()
        state=getAMState(output)
        shortName[fqdn].append(state)
        shortName[fqdn].append(str(int(time.time()*1000000)))
        ip.insert_agg_is_avail_datapoint(shortName[fqdn])
    tbl_mgr.close_con();
    
if __name__ == "__main__":
    main()
