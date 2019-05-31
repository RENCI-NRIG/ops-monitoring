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
import json
import ConfigParser

class WhitelistLoader:

    def __init__(self, config_path):
        self.config_path = config_path
        self._whitelist_set = set()
        self.load_whitelist()

    def load_whitelist(self):
        config = ConfigParser.ConfigParser()
        config.read(self.config_path + "/whitelist.conf")
        wl_list = json.loads(config.get("main", "whitelist"))

        for i in wl_list:
            self._whitelist_set.add(i)

    def is_in_whitelist(self,req_urn):
        return req_urn in self._whitelist_set


# short unit test
def main():
    wl = WhitelistLoader("../config")
    assert wl.is_in_whitelist("sdfsd") == False
    assert wl.is_in_whitelist("URI:urn:publicid:IDN+ch.geni.net+tool+collector-gpo") == True
    print "Successful unit test"

if __name__=="__main__":
    main()
