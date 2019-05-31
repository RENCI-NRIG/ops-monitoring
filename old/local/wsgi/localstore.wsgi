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
import traceback
import os
#import OpenSSL

sys.path.insert( 0, '/usr/local/ops-monitoring/local' )
from web_server import LocalDatastoreServer
server = LocalDatastoreServer('/usr/local/ops-monitoring')
def application(environ, start_response):
    return server.app(environ, start_response)

#try:
#  sys.path.insert(0, '/usr/local/ops-monitoring/local')
#  from web_server import LocalDatastoreServer
#
#  server = LocalDatastoreServer('/usr/local/ops-monitoring')
#  _application = server.app
#except Exception, e:
#  sys.stderr.write("WSGI threw an exception: %s: %s\n" % (
#    str(e), str(traceback.format_exc())))
#
#def authorized_certificate(cert_string):
#    """
#    Given a cient's PEM certificate in cert_string, return True if we
#    allow the client access or False if we deny access.
#
#    The allow/deny decision is based on comparing the certificate's
#    Subject Alternative Name to a configured whitelist of allowed names.
#    """
#
##    # parse the certificate data
##    try:
##        cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM,
##    	                                       cert_string)
##    except Exception, e:
##        print "Failed to parse certificate: %s" % (str(e))
##        return False
##
##    # Find the subject alternative name in the certificate.
##    # To begin, we have no subject alternative name.
##    alt_name = None
##
##    # loop over extensions, checking each to see if it is the subject
##    # alternative name
##    for x in range(cert.get_extension_count()):
##	ext = cert.get_extension(x)
##	short_name = ext.get_short_name()
##	if short_name == 'subjectAltName':
##	    alt_name = ext
##	    break
##
##    # If no subject alternative name, we're done.  Client is not authorized.
##    if not alt_name:
##        print "No subject alternative name found in cert"
##	return False
##
##    # At this point, alt_name should be a string that looks like this:
##    # email:dwiggins@bbn.com, URI:urn:publicid:IDN+ch.geni.net+tool+collector-gpo, URI:urn:uuid:be47098f-ff0c-4961-b1b1-bdfb3814a5fd
##    # Convert subject alt name value to string, split on comma to produce
##    # a list, and strip whitespace before & after on each element.
##    names = [s.strip() for s in str(alt_name).split(',')]
##
##    # find the URN by matching the prefix
##    sys.path.insert(0, '/usr/local/ops-monitoring/common')
##    import whitelist_loader
##    wl = whitelist_loader.WhitelistLoader('/usr/local/ops-monitoring/config')
##  
##    urn_prefix = 'URI:urn:publicid:IDN'
##    for name in names:
##        if name.startswith(urn_prefix):
##
##	    #if 'tool+collector-' in name: # maybe also include this
##	    if wl.is_in_whitelist(name):
##                return True
##            else:
##                print "%s not authorized" % (name)
##                return False
##
##    print "No %s found in certificate's subject alternative name" % (urn_prefix)
##    return False
#    return True
#
#def application(environ, start_response):
#    response_headers = [('Content-Type', 'text/plain')]
#
#    # Get the SSL client certificate supplied by the upper layers.
#    # Apache must be configured with SSLOptions +ExportCertData
#    # for SSL_CLIENT_CERT to be available here.
##    try:
##        cert = environ['SSL_CLIENT_CERT']
##    except KeyError:
##        print "SSL_CLIENT_CERT not found in WSGI environment"
##        start_response('500 Internal Server Error', response_headers)
##        return [""]
##
##    if authorized_certificate(cert):
##        return _application(environ, start_response)
##    else:
##        start_response('403 Forbidden', response_headers)
##        return ["Client certificate not authorized\n"]
#    return _application(environ, start_response)