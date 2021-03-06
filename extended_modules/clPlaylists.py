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

import clPlaylistDialog
from modules import clEntry
import gtk
import os
from modules import functions
from modules.clGstreamer010 import Track

class main():
    def __init__(self, pyjama):
        self.pyjama = pyjama

        self.pyjama.Events.connect_event("alldone", self.ev_alldone)
        self.pyjama.Events.connect_event("populate_playlistmenu", self.ev_populate_playlistmenu)
        self.pyjama.Events.connect_event("populate_listmenu", self.ev_populate_listmenu)

    def ev_populate_listmenu(self, rootmenu):
        selection = self.pyjama.window.tvList.get_selection()
        model, tmpIter = selection.get_selected()
        if tmpIter is None: return

        path =  model.get_path(tmpIter)
        ret = self.pyjama.window.tvList.get_item(path)
        track = Track()
        track.id = ret[self.pyjama.window.tvList.COLUMN_TRACKID]
        if track.id < 0: return


        mnu = gtk.ImageMenuItem("Add track to playlist")
        rootmenu.append(mnu)


        try:
            img = gtk.Image()
            pix = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(functions.install_dir(), "images", "playlist.png"), 16, 16)
            img.set_from_pixbuf(pix)
            mnu.set_image(img)
        except:
            print ("Playlist image not found or corrupt")



        submenu = gtk.Menu()
        addnew = gtk.ImageMenuItem("Create new playlist")
        addnew.connect("activate", self.cb_addnew_playlist_activate, track)
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
        addnew.set_image(img)
        addnew.show()
        submenu.append(addnew)
        sep = gtk.SeparatorMenuItem()
        sep.show()
        submenu.append(sep)

#        if self.pyjama.settings.section_exists("Playlists"):
#            playlists = self.pyjama.settings.config.items("Playlists")
        sql = "SELECT option, value FROM settings WHERE section='playlists'"
        playlists = self.pyjama.settingsdb.query(sql)
        if playlists:
            for name, ids in playlists:
                tmp = gtk.ImageMenuItem(name.replace("_", "__"))
                tmp.connect("activate", self.cb_append_to_playlist, name, track)
                submenu.append(tmp)
                tmp.show()

        mnu.set_submenu(submenu)
        submenu.show()
        mnu.show()

    def ev_populate_playlistmenu(self, rootmenu):
        model, tmpIter = self.pyjama.window.tvSelection.get_selected()
        if tmpIter is None: return
        path =  model.get_path(tmpIter)
        track = self.pyjama.player.playlist[path[0]]

        mnu = gtk.ImageMenuItem("Add track to playlist")
        rootmenu.append(mnu)

        try:
            img = gtk.Image()
            pix = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(functions.install_dir(), "images", "playlist.png"), 16, 16)
            img.set_from_pixbuf(pix)
            mnu.set_image(img)
        except:
            print ("Playlist image not found or corrupt")

        submenu = gtk.Menu()
        addnew = gtk.ImageMenuItem("Create new playlist")
        addnew.connect("activate", self.cb_addnew_playlist_activate, track)
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
        addnew.set_image(img)
        addnew.show()
        submenu.append(addnew)
        sep = gtk.SeparatorMenuItem()
        sep.show()
        submenu.append(sep)

#        if self.pyjama.settings.section_exists("Playlists"):
#            playlists = self.pyjama.settings.config.items("Playlists")
        sql = "SELECT option, value FROM settings WHERE section='playlists'"
        playlists = self.pyjama.settingsdb.query(sql)
        if playlists:
            for name, ids in playlists:
                tmp = gtk.ImageMenuItem(name.replace("_", "__"))
                tmp.connect("activate", self.cb_append_to_playlist, name, track)
                submenu.append(tmp)
                tmp.show()

        mnu.set_submenu(submenu)
        submenu.show()
        mnu.show()

    def cb_addnew_playlist_activate(self, activate, track):
        # ask for name
        result = clEntry.input_box(title=_('Playlist'),
            message=_('Please enter a name for your new playlist.\nExisting playlists will be overwritten'),
            default_text="MyPlaylist")
        if result is None:
            return
        name = str(result)

        pl_string = "-SEP-%s" % str(track.id)
        # Append to bookmarks and write to config
        self.pyjama.settingsdb.set_value("playlists", name, pl_string)

        # this part needs to be fixed - the dict submenu
        # is not needed any more, use get_childs instead!
        if not name in self.pyjama.window.menubar.submenus:
            # Append menu entry
            menu = self.pyjama.window.menubar
            playlist = menu.append_entry(menu.get_rootmenu("Playlists"), name, name)
            playlist.connect("activate", self.cb_load_playlist, name)
        

    def cb_append_to_playlist(self, widget,  name, track):
        tracks = self.pyjama.settingsdb.get_value("playlists", name, None)
        if tracks is not None:
            tracks += "-SEP-%s" % str(track.id)
        else:
            tracks = "-SEP-%s" % str(track.id)
        self.pyjama.settingsdb.set_value("playlists", name, tracks)

    def ev_alldone(self):
        # Create Bookmarks menu
        menu = self.pyjama.window.menubar
        playlists = menu.insert_root_before("Extras", _("Playlists"), "Playlists")

        translation_array = [_("Import Playlist"), _("Save playlist"), _("Export Playlist"), _("Import Playlist from Jamendo"), _("Manage Playlists")]

        sub = ["Save playlist", "Import Playlist", "Import Playlist from Jamendo", "Export Playlist", "---", "Manage Playlists", "---"]  
        self.playlists_menu = menu.create_submenu(rootmenu=playlists, submenu=sub)

        save_playlist = menu.get_submenu("Save playlist")
        menu.set_item_image(save_playlist, gtk.STOCK_SAVE )
        save_playlist.connect("activate", self.cb_save_playlist)

        save_playlist_to_disc = menu.get_submenu("Export Playlist")
        menu.set_item_image(save_playlist_to_disc, gtk.STOCK_SAVE_AS )
        save_playlist_to_disc.connect("activate", self.pyjama.window.cb_export_playlist)

        load_playlist_from_disc = menu.get_submenu("Import Playlist")
        menu.set_item_image(load_playlist_from_disc, gtk.STOCK_OPEN )
        load_playlist_from_disc.connect("activate", self.cb_import_playlist)

        import_playlists = menu.get_submenu("Import Playlist from Jamendo")
        menu.set_item_image(import_playlists, gtk.STOCK_NETWORK )
        import_playlists.connect("activate", self.cb_import_playlists)

        manage_playlists = menu.get_submenu("Manage Playlists")
        menu.set_item_image(manage_playlists, gtk.STOCK_EDIT )
        manage_playlists.connect("activate", self.cb_manage_playlists)

#        ret = self.pyjama.settingsdb.create_table("playlists")
#        if ret == "created": print ("Created playlists table")

        # Append menu entrys
        menu = self.pyjama.window.menubar
        root = menu.get_rootmenu("Playlists")
        if self.pyjama.settings.section_exists("Playlists"):
            for name, ids in self.pyjama.settings.config.items("Playlists"):
#                playlist = menu.append_entry(root, name, name)
#                playlist.connect("activate", self.cb_load_playlist, name)
                # move all playlists from configfile to settingsdb
                print ("Playlist '%s' was moved from configfile to database"%name)
                self.pyjama.settingsdb.set_value("playlists", name, ids.replace("+", "-SEP-"))
                # delete the old entries
                self.pyjama.settings.remove_option("Playlists", name)

        sql = "SELECT option, value FROM settings WHERE section='playlists'"
        playlists = self.pyjama.settingsdb.query(sql)
        if playlists:
            for name, ids in playlists:
                playlist = menu.append_entry(root, name, name)
                playlist.connect("activate", self.cb_load_playlist, name)
        

#    def create_table(self):
#        sql = "select count(name) from sqlite_master where name = 'playlists'" 
#        result = self.pyjama.settingsdb.query(sql)
#        if ret[0][0] == 0:
#            sql = """
#            CREATE TABLE playlists (
#              uid INTEGER PRIMARY KEY,
#              name STRING,
#              track INTEGER,
#            )
#            """
#            self.pyjama.settingsdb.query(sql)
#            print ("Created table for playlists")
#            return "created"
#        else:
#            return "existant"

    def cb_import_playlist(self, ev):
        #TO BE IMPROVED:
        #Right now pyjama queries every trackid
        #at the database on its own.

        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,   gtk.RESPONSE_OK)
        dialog = gtk.FileChooserDialog(_("Load Playlist"), None, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=buttons, backend=None)
        filter1 = gtk.FileFilter()
        filter1.set_name("M3U Playlist Format")
        filter1.add_pattern("*.m3u")
        dialog.add_filter(filter1)

        filter2 = gtk.FileFilter()
        filter2.set_name("XSPF Playlist Format")
        filter2.add_pattern("*.xspf")
        dialog.add_filter(filter2)
#        filter2 = gtk.FileFilter()
#        filter2.set_name("XSPF Playlist Format")
#        filter2.add_pattern("*.xspf")
#        dialog.add_filter(filter2)

        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.set_current_folder(os.getenv("HOME"))
#        dialog.set_current_name("pyjama-playlist")

        response = dialog.run()
        dialog.hide()
        if response == gtk.RESPONSE_OK and dialog.get_filename() is not None:
            filename = dialog.get_filename()
            self.open_playlist_from_file(filename)
            dialog.destroy()

    def open_playlist_from_file(self, filename):
        tracks = self.pyjama.read_playlist(filename)
        if tracks is not None:
            ret = self.pyjama.db.get_multiple_trackinfos(tracks)
            if ret is None:
                #~ self.pyjama.info("Playlist Error", "None of the tracks in the playlist were found in the local database")
                return
            if ret == []:
                gtk.gdk.threads_enter()
                self.pyjama.info("Playlist Error", "None of the tracks in the playlist were found in the local database")
                gtk.gdk.threads_leave()
                return
            for track_id in tracks:
                inlist = False
                for track in ret:
                    if int(track.id) == int(track_id):
                        inlist = True
                        self.pyjama.add2playlist(track)
                if not inlist:
                    print ("Track '%i' not in database, yet.")

    def cb_manage_playlists(self, widget):
        dialog = clPlaylistDialog.PlaylistManageDialog(self)

#        if self.pyjama.settings.section_exists("Playlists"):
#            playlists = self.pyjama.settings.config.items("Playlists")
        sql = "SELECT option, value FROM settings WHERE section='playlists'"
        playlists = self.pyjama.settingsdb.query(sql)
        if playlists:
            dialog.populate_list(playlists)
        result = dialog.run()
        model = dialog.treeview.get_model()
        dialog.destroy()
        if result == 1: # delete
            iter = model.get_iter_first()
            menu = self.pyjama.window.menubar
            while iter:
                checked, name = ( model.get(iter, 0, 1) )
                if checked == True:
                    mnu = menu.get_submenu(name).destroy()
                    sql = "DELETE FROM settings WHERE section='playlists' and option = '%s'" % name.replace("'", "''")
                    playlists = self.pyjama.settingsdb.query(sql)

                    # this part needs to be fixed - the dict submenu
                    # is not needed any more, use get_childs instead!
                    del self.pyjama.window.menubar.submenus[name]
                iter = model.iter_next(iter)

    def cb_import_playlists(self, widget):
        dialog = clPlaylistDialog.PlaylistDialog(self)
        result = dialog.run()
        model = dialog.treeview.get_model()
        dialog.destroy()
        if result == 1:
            iter = model.get_iter_first()
            while iter:
                checked, name, id = ( model.get(iter, 0, 1, 2) )
                if checked == True:
                    self.import_playlist(name, id)
                iter = model.iter_next(iter)

    def cb_save_playlist(self, widget):
        dialog = clPlaylistDialog.SaveDialog(self)
        result = dialog.run()
        entry = dialog.entry
        dialog.destroy()
        if result == 1: #save
            name = entry.get_text()
            playlist = self.pyjama.player.playlist
            pl_string = ""
            for track in playlist:
                pl_string += "-SEP-%s" % str(track.id)
                # Append to bookmarks and write to config
                self.pyjama.settingsdb.set_value("playlists", name.replace("'", "''"), pl_string)

                # this part needs to be fixed - the dict submenu
                # is not needed any more, use get_childs instead!
                if not name in self.pyjama.window.menubar.submenus:
                    # Append menu entry
                    menu = self.pyjama.window.menubar
                    playlist = menu.append_entry(menu.get_rootmenu("Playlists"), name, name)
                    playlist.connect("activate", self.cb_load_playlist, name)


    def cb_load_playlist(self, menu, name):
        
        tracks = self.pyjama.settingsdb.get_value("playlists", name, None)
        if tracks is not None:
            tracks = tracks[5:].split("-SEP-")
            tracks = self.pyjama.db.get_multiple_trackinfos(tracks)
            self.pyjama.appendtracks(tracks)


    def import_playlist(self, name, id):
        print "Going to import Playlist '%s' with the id '%i'" % (name, id)
        tracks = self.playlist_tracks(int(id))
        if tracks != []:
            track_string = ""
            for track in tracks:
                track_string += "-SEP-%i" % track

#            name = name.replace(" ", "_").replace("=", "_").replace("#", "_")

            # Append to bookmarks and write to config
            self.pyjama.settingsdb.set_value("playlists", name, track_string)

            # Append menu entry
            menu = self.pyjama.window.menubar
            playlist = menu.append_entry(menu.get_rootmenu("Playlists"), name, name)
            playlist.connect("activate", self.cb_load_playlist, name)


    def user_playlists(self, user):
        ret = self.pyjama.jamendo.query("name+id/playlist/json/?user_idstr=%s&n=all" % (user), self.pyjama.settings.get_value("JAMENDO", "CACHING_TIME_SHORT"))
        return ret

    def playlist_tracks(self, playlist_id):
        ret = self.pyjama.jamendo.query("track_id/playlist/json/?id=%i" % playlist_id)
        return ret
