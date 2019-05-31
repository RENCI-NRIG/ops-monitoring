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

# This makefile fragment serves as the link between the makefiles
# scattered throughout the tree and the central repository of make
# definitions for this project in the makefile-fragments directory.
# Having this level of indirection allows directories to be moved
# around without needing their associated makefiles to be modified.
#
# This file should serve no other purpose than the one described
# above.  It should remain clean and simple.  If you feel the need to
# put other definitions/rules in this file, you are probably doing
# something wrong.

# Locate the root of the source tree.
# ROOT_MK needs to be preset by the makefile that includes this fragment.
SRCROOT:=$(realpath $(dir $(ROOT_MK)))

# Set MAKEFRAGDIR to where the rest of the makefile definitions reside.
MAKEFRAGDIR:=$(SRCROOT)/cm/build/makefile-fragments

# Pull in a bunch of make definitions to get things rolling.
include $(MAKEFRAGDIR)/prolog.mk
