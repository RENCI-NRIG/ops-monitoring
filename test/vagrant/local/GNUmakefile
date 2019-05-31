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
#------------------------------------------------------------------------------

# Put the following two lines of boilerplate at the top of every Makefile.
ROOT_MK := $(firstword $(realpath root.mk ../root.mk ../../root.mk ../../../root.mk ../../../../root.mk ../../../../../root.mk ../../../../../../root.mk))
include $(ROOT_MK)

UNITTEST_REPORTDIR = test-reports
UNITTEST_PY = UT_local_response.py
COLLECTOR_KEY = col-gpo.pem
COPY_KEY = col-gpo.pem

.PHONY: start_vm 
unittests:: start_vm $(COPY_KEY)
	@- $(foreach UTPY, $(UNITTEST_PY), \
	echo "running $(UTPY)"; \
	vagrant ssh -- /usr/local/ops-monitoring/local/unit-tests/$(UTPY) -c /vagrant/$(COPY_KEY) --xml /vagrant/$(UNITTEST_REPORTDIR); \
	)
	vagrant suspend
	 

start_vm: $(UNITTEST_REPORTDIR)
	../start-vagrant-vm.sh
	
$(COPY_KEY): $(COLLECTOR_KEY)
	cp -v $(COLLECTOR_KEY) $(COPY_KEY)

ifneq "$(COPY_KEY)" "$(COLLECTOR_KEY)"
clean::
	rm -f $(COPY_KEY)
endif

# Put the following line of boilerplate at the end of every Makefile.
include $(MAKEFRAGDIR)/epilog.mk
