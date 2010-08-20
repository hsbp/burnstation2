#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------
# pyjama - python jamendo audioplayer
# Copyright (c) 2009 Daniel Nögel
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

import gtk

from modules.clWidgets import StockButton
from modules import functions

class main():
    def __init__(self, pyjama):
        self.pyjama = pyjama

        self.pyjama.Events.connect_event("alldone", self.ev_alldone)

    ######################################################################
    #                                                                    #
    #                                Events                              #
    #                                                                    #
    ######################################################################

    def ev_alldone(self):
        # Register layout
        self.pyjama.layouts.register_layout("search", SearchLayout(self.pyjama))

        #
        # Add Search Button to Toolbar
        #
        # add button to toolbar
        toolbar = self.pyjama.window.toolbar
        self.bSearch = gtk.ToolButton(_("Search"))
        self.bSearch.set_label(_("Search"))
        self.bSearch.set_stock_id(gtk.STOCK_FIND)
        self.bSearch.set_tooltip_text(_("Search"))
        self.bSearch.connect("clicked", self.on_bSearch_clicked)
#        try:
#            pos = toolbar.get_item_index(toolbar.space_fs)
#        except:
#            pos = -2
#        toolbar.insert(self.bSearch, pos+1)
        toolbar.insert(self.bSearch, -1)
        self.bSearch.show()


        #
        # Menu
        #
        menu = self.pyjama.window.menubar
        browse = menu.get_rootmenu("Browse")

        search = gtk.ImageMenuItem(_("Search"))
        menu.set_item_image(search, gtk.STOCK_FIND)
        search.show()
        browse.get_submenu().insert(search, 0)
        search.connect("activate", self.on_bSearch_clicked)

        sep = gtk.SeparatorMenuItem()
        sep.show()
        browse.get_submenu().insert(sep,1)
        


        #
        # Accelerators
        #
        self.accel_group = gtk.AccelGroup()
        search.add_accelerator("activate", self.accel_group, ord("f"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        self.pyjama.window.add_accel_group(self.accel_group)

    def on_bSearch_clicked(self, ev):
        self.pyjama.layouts.show_layout("search", who_called = "on_bSearch_clicked")

######################################################################    
#
# Search Layout - searches albums, artists, tracks
#
class SearchLayout(gtk.Layout):
    def __init__(self, pyjama):
        self.pyjama = pyjama
        gtk.Layout.__init__(self)
        self.set_size(350,100)   

        # Labels for Search- Window
        self.SearchLabels={}

        #
        # Search Layout
        #
        self.SearchLabels['desc'] = gtk.Label("")
        self.SearchLabels['desc'].set_single_line_mode(False)
        self.put(self.SearchLabels['desc'], 10, 10)
        if self.pyjama.nocolor:
            self.SearchLabels['desc'].set_markup(_("<span><b>Here you can search for artist, albums and tracks.\nEnter your search term in the text field\n\nAt most 100 results will be shown.</b></span>") )
        else:
            self.SearchLabels['desc'].set_markup(_("<span foreground=\"white\"><b>Here you can search for artist, albums and tracks.\nEnter your search term in the text field\n\nAt most 100 results will be shown.</b></span>"))
        self.SearchLabels['desc'].show()
            
        # Entry
        self.hbSearch = gtk.HBox()
        self.put(self.hbSearch, 10, 80)
        self.eSearch = gtk.Entry()
        self.eSearch.connect("activate", self.prepare_search)
        self.hbSearch.pack_start(self.eSearch, True, True)
        
        # Button
        self.bSearch2 = StockButton(gtk.STOCK_FIND, gtk.ICON_SIZE_SMALL_TOOLBAR )
        self.hbSearch.pack_start(self.bSearch2, True, True)
        self.bSearch2.connect("clicked", self.prepare_search)

        self.SearchLabels['hits'] = gtk.Label("")
        self.SearchLabels['hits'].set_single_line_mode(False)
        self.put(self.SearchLabels['hits'], 250,90)
        #self.hbSearch.pack_end(self.SearchLabels['hits'], True, True)
        self.hbSearch.show_all()

        # Setting Color
        self.pyjama.window.setcolor(self)
        self.show_all()


    def draw(self, data1, data2, data3, data4):
        if data4 == None:
#            markup = self.pyjama.window.markuplbCaption.replace("TEXT", _("Search for artists, albums and tracks"))
            txt = _("Search for artists, albums and tracks")
        else:
#            markup = self.pyjama.window.markuplbCaption.replace("TEXT", _("You searched for '%s'") % data4)
            srch = "<b>%s</b>" % data4
            txt = _("You searched for '%s'") % srch
#        self.pyjama.window.lbCaption.set_markup(markup)
        self.pyjama.window.LayoutInfo.set_text(txt)
        self.pyjama.window.LayoutInfo.set_image(gtk.STOCK_FIND)
        self.search_window(data1, data2, data3, data4)

    ######################################################################
    #                                                                    #
    #                            Functions                               #
    #                                                                    #
    ######################################################################

    # This Function was installed to pass search results
    # through "clear_layout" function, which supplies
    # history functionality!
    def prepare_search(self, ev):
        if len(self.eSearch.get_text())<3:
            self.pyjama.layouts.show_layout("search", -1)
            return None
        ret1 =  self.pyjama.db.search_artist(self.eSearch.get_text())
        ret2 =  self.pyjama.db.search_album(self.eSearch.get_text())
        ret3 =  self.pyjama.db.search_track(self.eSearch.get_text())
        self.pyjama.layouts.show_layout("search", ret1, ret2, ret3, self.eSearch.get_text(), who_called = "prepare_search")

    def search_window(self, search=None, search2=None, search3=None, keyword=None):
        if search == None and search2 == None and search3 == None:
            self.SearchLabels['hits'].hide()
        else:
            self.SearchLabels['hits'].show()
        if search == -1:
            print ("Minimum length of 3 letters")
            return None

        if keyword:
            self.eSearch.set_text(keyword)
        self.pyjama.window.set_focus(self.eSearch)

        hits_artists, hits_albums, hits_tracks = 0,0,0

        
        ### Results into Treeview
        # in order to fast that up, i should
        # disconnect listview from treeview
        # temporary

        if keyword is None:
            self.pyjama.window.TVListFrame.get_label_widget().set_markup("")
        else:
            self.pyjama.window.TVListFrame.get_label_widget().set_markup(_("Artists, Albums and Tracks containing '<b>%s</b>'" % keyword))

        self.pyjama.window.tvList.clear()
        if search != None and len(search) > 0:
            for hit in search:
                results = [search[hit]['artist_name'], "", "", "", "", search[hit]['artist_id'], -1, -1]
                self.pyjama.window.tvList.add_item(results)
            hits_artists = len(search)
                
        if search2 != None and len(search2) > 0:
            for hit in search2:
                results = [search2[hit]['artist_name'], search2[hit]['album_name'], "", "", "", search2[hit]['artist_id'], search2[hit]['album_id'], -1]
                self.pyjama.window.tvList.add_item(results)
            hits_albums = len(search2)
            
        if search3 != None and len(search3) > 0:
            for track in search3:
                results = [track.artist_name, track.album_name, track.numalbum, track.name, track.license, track.artist_id, track.album_id, track.id]
                self.pyjama.window.tvList.add_item(results)
            hits_tracks = len(search3)

        if search or search2 or search3:
            hit_message = _("<u>%i hits</u>\n\n%i artists\n%i albums\n%i tracks") % (hits_artists + hits_albums + hits_tracks, hits_artists, hits_albums, hits_tracks)

            if self.pyjama.nocolor:
                self.SearchLabels['hits'].set_markup("<span><b>%s</b></span>" % hit_message)
            else:
                self.SearchLabels['hits'].set_markup("<span foreground=\"white\"><b>%s</b></span>" % hit_message)

    class ToolBar(gtk.HBox):
        def __init__(self, pyjama):
            self.pyjama = pyjama
            gtk.HBox.__init__(self)
            
