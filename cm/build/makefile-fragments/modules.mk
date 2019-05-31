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

# This file provides a set of make variables that define the locations
# of various things, mostly libraries (a.k.a. modules), that may
# need to be referenced from other parts of the tree.  By using the
# symbolic names here, we avoid hardcoding paths into the makefiles,
# making tree reorganization less painful.


# $(call declare-module,name,dir)
# Generate make variable declarations for a module.
#
# Arguments:
# $1 : name of the module as it will appear in other makefiles
# $2 : directory containing the module's sources
#
# For example, if name ($1) is FOO, this function will provide
# the following make variables that can be used in other
# makefiles to refer to this module:
#
# FOO_DIR, directory containing the module's sources

define declare-module
MODULE_NAMES += $1
$1_DIR := $2
endef

#------------------------------------------------------------------------------

#
# Module declarations
#

$(eval $(call declare-module,SCHEMA,$(SRCROOT)/schema))
$(eval $(call declare-module,CONFIG,$(SRCROOT)/config))
$(eval $(call declare-module,BUILD,$(SRCROOT)/cm/build))
