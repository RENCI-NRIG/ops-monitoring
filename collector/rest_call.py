#!/usr/bin/env python
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

'''
This program exercises the monitoring REST/JSON API by making REST
call local datastores and validating the JSON reponses it receives
against the monitoring schema.  The URLs specifying the REST calls are
supplied on the command line.  A disk filename can be given instead of
a URL to verify test data.  See the commmand line options (invoke with
--help) for more information about the program's capabilities.

This requires the python requests and validictory packages.
'''

import json
import sys
import requests
import re
import os
from optparse import OptionParser
import datetime

# XXX this program must be run with the current directory set to
# collector/ (the directory containing this file) OR with said
# directory added to the PYTHONPATH environment variable so that it
# can find the response_validatory module.
import response_validator


def visit_url(url, cert_path, http_headers):
    """
    Make a monitoring REST call and collect the response.

    :param url: URL of the monitoring REST call for which to fetch the
      response.  If this doesn't start with http(s)://, interpret it as
      a filename.
    :param cert_path: path to tool certificate file for SSL access.
    :param http_headers: a dictionary of HTTP header names/values to use with
      the HTTP request.
    :return: a 2-tuple.  The first item of the tuple is a dictionary
      containing the JSON response to url, or None if an error occurred.
      The second item of the tuple is a status string.  If url was
      really a url, the status string will be the HTTP status code
      and description, or "No Response" if the web server did not respond.
      If url was a filename, it will be "File OK" or an errno value and
      description.
    """
    json_dict = None
    status_string = "No Response"

    if re.match("https?://", url):
        # interpret url as an actual URL
        resp = None
        try:
            resp = requests.get(url, verify=False, cert=cert_path,
                                headers=http_headers)
            status_string = str(resp.status_code) + " " + resp.reason
        except Exception as e:
            print "No response from local datastore for URL %s\s%s" % (url,
                                                                       str(e))
        if resp is not None:
            try:
                json_dict = json.loads(resp.content)
            except Exception as e:
                print "Could not parse JSON from URL %s, %s\n%s" % (url, resp.content,
                                                                    str(e))
        else:
            print "resp object is None from", url
    else:
        # interpret url as a file on the local disk
        try:
            json_dict = json.load(open(url))
            status_string = "File OK"
        except IOError as ioe:
            print "Could not open file: %s\n%s" % (url, str(ioe))
            status_string = str(ioe.errno) + " " + os.strerror(ioe.errno)
        except ValueError as ve:
            print "Could not parse JSON from file: %s\n%s" % (url, str(ve))
            status_string = str(ve)

    return (json_dict, status_string)


def find_embedded_urls(json_dict):
    """
    Examine a JSON response to find other URLs that could be visited.
    Fields named "href" or "selfRef" are assumed to be URLs.

    :param json_dict: dictionary containing a JSON response to examine.
    :return: a list, possibly empty, of embedded urls found.
    """
    embedded_urls = []

    if isinstance(json_dict, dict):
        for urlKey in ["href", "selfRef"]:
            if urlKey in json_dict:
                embedded_urls.append(json_dict[urlKey])

        for (_key, dval) in json_dict.items():
            if isinstance(dval, dict):
                embedded_urls.extend(find_embedded_urls(dval))
            elif isinstance(dval, list):
                for lval in dval:
                    if isinstance(lval, dict):
                        embedded_urls.extend(find_embedded_urls(lval))
    return embedded_urls


def validate_response(json_dict, options, schema_stats=None):
    """
    Check a JSON response against its schema.

    :param json_dict: dictionary containing a JSON response to validate..
    :param options: command line options object
    :param schema_stats: dictionary of per-URL schema stats
    :return: True if json_dict was valid, else False
    """
    if not json_dict:
        return False

    try:
        schema_url = json_dict["$schema"]
    except KeyError:
        print "No $schema specified in response"
        return False

    schema = response_validator.parse_schema(schema_url,
                                             options.schema_path)
    if not schema:
        return False

    if schema_stats is not None:
        try:
            schema_stats[schema_url]["seen"] += 1
        except KeyError:
            schema_stats[schema_url] = {"seen": 1, "valid": 0}

    if options.print_schema:
        print "Schema used for validation:\n%s" % (json.dumps(schema, indent=4,
                                                              sort_keys=True))
    valid = response_validator.validate(json_dict, schema,
                                        options.validictory_path,
                                        options.schema_base)
    if valid and schema_stats:
        schema_stats[schema_url]["valid"] += 1

    return valid


def choose_url_to_visit(unvisited_urls, num_visited_urls, interactive):
    """
    Decide which URL to visit next.

    :param unvisited_urls: candidate URLs that could be visited next.
    :param num_visited_urls: number of URLs already visited.
    :param interactive: boolean, are we in interactive mode?
    :return: URL (string) to visit next, or None
    """
    if interactive:
        # If there is only one possible URL, and this is the first time
        # visiting anything, just go there without asking.
        if len(unvisited_urls) == 1 and num_visited_urls == 0:
            return unvisited_urls[0]

        print 79 * "="  # line of === for visual separation
        for idx in range(len(unvisited_urls)):
            print str(idx) + ": " + unvisited_urls[idx]
        user_input = raw_input(
            "Which URL to go to? (enter number from above, or anything else to exit)\n")
        try:
            choice = int(user_input)
        except ValueError:
            # If non-numeric input was received, pretend we got an
            # invalid choice.
            choice = -1

        # If it's an invalid choice...
        if (choice < 0) or (choice >= len(unvisited_urls)):
            return None
        else:
            return unvisited_urls[choice]
    else:
        # non-interactive: always return the first URL in the list
        return unvisited_urls[0]


def get_max_keylen(d):
    """
    Find the longest key length in a given dictionary.

    :param d: dictionary for which to compute longest key length
    """
    max_len = 0
    for k in d:
        k_len = len(k)
        if max_len < k_len:
            max_len = k_len
    return max_len


def print_schema_stats(schema_stats_dict):
    """
    Print per-URL schema statistics.

    :param schema_stats: dictionary of per-URL schema stats
    """

    # Find the length of the longest URL to format the output nicely.

    max_url_len = get_max_keylen(schema_stats_dict)

    print "Schema counts:"
    for url, stats in sorted(schema_stats_dict.items()):
        print "%-*s seen %d times, valid %d times" % (
            max_url_len, url, stats["seen"], stats["valid"])


def main(argv):

    # Set up command-line options

    parser = OptionParser(usage="usage: %prog [options] <list-of-datastore-urls>",
                          description="Make a monitoring REST call, and "
                          "validate and display the JSON response. "
                          "If any of the URLs in <list-of-datastore-urls> "
                          "does not start with \"http(s)://\", then it is "
                          "interpreted as a file containing a JSON response.")
    parser.add_option("-c", "--cert-path", dest="cert_path",
                      help="path to tool certificate file")
    parser.add_option("-v", "--validictory-path", dest="validictory_path",
                      help="path to validictory python module")
    parser.add_option("-s", "--schema-path", dest="schema_path",
                      help="path to directory of schema files to use for validation")
    parser.add_option("-b", "--schema-base", dest="schema_base",
                      help="expected $schema string in JSON responses")
    parser.add_option("-f", "--follow-urls", dest="follow_urls",
                      default=False, action="store_true",
                      help="follow URLs in JSON responses to find other "
                           "objects, i.e., crawl the datastore")
    parser.add_option("-i", "--interactive", dest="interactive",
                      default=False, action="store_true",
                      help="allow user to choose which URLs to follow "
                           "(implies -f)")
    parser.add_option("--skip-validation", dest="skip_validation",
                      default=False, action="store_true",
                      help="don't do JSON validation of responses")
    parser.add_option("--print-schema", dest="print_schema",
                      default=False, action="store_true",
                      help="print the schema used to validate each response")
    parser.add_option("--schema-stats", dest="schema_stats",
                      default=False, action="store_true",
                      help="print statistics on schema usage")
    parser.add_option("--connection-close", dest="connection_close",
                      default=False, action="store_true",
                      help="use 'Connection: close' header on HTTP requests")
    (options, url_args) = parser.parse_args()

    # Do some more checking on the options provided

    if options.cert_path and not os.path.isfile(options.cert_path):
        print "cert-path %s is not a file" % (options.cert_path)
        return 1

    if options.validictory_path and not os.path.isdir(
            options.validictory_path):
        print "validictory-path %s is not a directory" % (options.validictory_path)
        return 1

    if options.schema_path and not os.path.isdir(options.schema_path):
        print "schema-path %s is not a directory" % (options.schema_path)
        return 1

    # If in interactive mode, enable follow_urls so that the user has choices
    if options.interactive:
        options.follow_urls = True

    # Initialize http headers
    if options.connection_close:
        http_headers = {'Connection':'close'}
    else:
        http_headers = {}  # empty dictionary

    # Options look good.  Let's get to work.

    # URLs that haven't been fetched yet
    unvisited_urls = list(url_args)  # make a copy of url_args

    # URLs for which we have attempted to fetch a response
    visited_urls = set()  # empty set to begin

    # Number of URLs visited that returned valid JSON according to their schema
    num_valid_urls = 0

    # Dictionary to track stats about schema URLs that we've seen.
    # The key into this dictionary is the schema URL.
    # The value is another dictionary with keys "seen" and "valid".
    # The value for "seen" is the number of times this schema URL was
    # encountered.
    # The value for "valid" is the number of times the response was
    # valid according to this schema.
    if options.schema_stats:
        schema_stats_dict = dict()
    else:
        schema_stats_dict = None

    http_status_dict = dict()

    # main loop

    while unvisited_urls:
        url = choose_url_to_visit(unvisited_urls, len(visited_urls),
                                  options.interactive)
        if not url:  # chose to exit
            break

        print 79 * "-", "\n%s Visiting %s returns:" % (
            str(datetime.datetime.now()), url)

        json_dict, status_string = visit_url(url, options.cert_path,
                                             http_headers)

        # now that we've visited it, move this url from unvisited to visited
        unvisited_urls.remove(url)
        visited_urls.add(url)

        # print the response

        print str(datetime.datetime.now()) + " " + status_string
        print json.dumps(json_dict, indent=4, sort_keys=True)

        # keep track of how many times this status was seen

        try:
            http_status_dict[status_string] += 1
        except KeyError:
            http_status_dict[status_string] = 1

        # maybe validate the response

        if not options.skip_validation:
            valid = validate_response(json_dict, options, schema_stats_dict)
            print "Response from %s is" % (url),
            if valid:
                print "valid"
                num_valid_urls += 1
            else:
                print "NOT valid"

        # maybe "crawl"; harvest other URLs from the response

        if options.follow_urls:
            # Find the URLs embedded in this response.  Any that we
            # have not already visited go into unvisited_urls if not
            # already there.
            embedded_urls = find_embedded_urls(json_dict)
            for embedded_url in embedded_urls:
                if (not (embedded_url in visited_urls) and
                        not (embedded_url in unvisited_urls)):
                    unvisited_urls.append(embedded_url)

    # print a summary of this run

    print "%d URLs visited" % (len(visited_urls)),
    if not options.skip_validation:
        print ", %d valid" % (num_valid_urls)

    print "HTTP or errno status codes:"
    max_status_len = get_max_keylen(http_status_dict)
    for status_string, count in sorted(http_status_dict.items()):
        print "%-*s seen %d times" % (max_status_len, status_string, count)

    # print schema stats if requested

    if options.schema_stats:
        print_schema_stats(schema_stats_dict)

if __name__ == "__main__":
    main(sys.argv[1:])
