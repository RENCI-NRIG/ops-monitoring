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

# This file is included at the end of our makefiles.  It mostly defines
# make targets based on the definitions given in the body of the makefile.

# Let make know that these are not real files.
.PHONY: all clean unittests

# Handle SUBDIRS definition from the makefile body.
# This is a list of subdirectories (of the directory
# containing the makefile) in which make should be run.
ifdef SUBDIRS

all:: $(SUBDIRS)

clean:: $(SUBDIRS)

unittests:: $(SUBDIRS)

# Here is where the recursive make happens.  $@ is one of the subdirs,
# and MAKECMDGOALS is the make target(s) that the user gave to the
# make command, e.g., all, clean.  So this one rule works for any
# make target that needs to be recursive just by listing $(SUBDIRS) as
# a prerequisite for the target.

.PHONY: $(SUBDIRS)
$(SUBDIRS):
	$(MAKE) -C $@ $(MAKECMDGOALS)
endif # SUBDIRS

#------------------------------------------------------------------------------

# Handle JWC_FILES definition from the makefile body. JWC_FILES must
# be a list of JSON files, usually schemas, that have comments.  (JWC
# stands for JSON With Comments.)  Since JSON doesn't support
# comments, we must produce a version with the comments stripped out.
# Our convention is that these files have the extension .jwc, and
# comment lines in these files begin with // like C++/Java.  For a JWC
# file xyz.jwc, the uncommented version generated will be called xyz;
# we just drop the .jwc suffix.
ifdef JWC_FILES

# $(call remove-jwc-suffix,filename)
# Remove .jwc from the end of a filename
# Arguments:
# $1 : filename to remove .jwc from
# returns: filename without .jwc
define remove-jwc-suffix
    $(patsubst %.jwc,%,$1)
endef

# $(call remove-comments-from-json-file,src,dest)
# Generate file with comments stripped out
# Arguments:
# $1 : filename to strip comments from
# $2 : filename to write uncommented results to
define remove-comments-from-json-file
$2: $1
	$(BUILD_DIR)/strip_comments.py < $1 > $2

endef

# Get a list of files to generate
JSON_FILES += $(foreach file,$(JWC_FILES),$(call remove-jwc-suffix,$(file)))

all:: $(JSON_FILES)

$(eval $(foreach file,$(JWC_FILES),\
                 $(call remove-comments-from-json-file,$(file),\
                        $(call remove-jwc-suffix,$(file)))))
unittests:: $(JSON_FILES)

clean::
	$(RM) $(JSON_FILES)

endif # JWC_FILES

ifdef UNITTEST_REPORTDIR

unittests:: $(UNITTEST_REPORTDIR)

$(UNITTEST_REPORTDIR):
	@mkdir -p $(UNITTEST_REPORTDIR)

clean::
	$(RM) -rf $(UNITTEST_REPORTDIR)



endif # UNITTEST_PY
