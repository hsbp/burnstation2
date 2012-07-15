#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------
# pyjama - python jamendo audioplayer
# Copyright (c) 2008 Daniel Nögel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------

## @package get_imagepack
# This module just holds a function
# to download and extract an image pack

import os
import functions

# Gettext - Übersetzung
functions.translation_gettext()
#def _(string):
#    return string
    

## Download and extrackt images 
# @return: 
# - 0 = ok
# - 1 = download error
# - 2 = extraction error
# 
def download_pack():
    home=functions.preparedirs()
    print ("Downloading imagepack")
    ret = os.system("wget -cO %s xn--ngel-5qa.de/pyjama/release/imagepack.tar.gz" % os.path.join(home, "imagepack.tar.gz"))
    if ret <> 0:
        print ("Error downloading the imagepack")
        return 1
    else:
        print ("Extracting imagepack to '~/.pyjama/images'")
        ret = os.system("tar -C %s -xf %s" % (home, os.path.join(home, "imagepack.tar.gz")))
        if ret <> 0:
            print ("Error extracting the imagepack")
            return 2
        else:
            print ("All done")
            return 0

