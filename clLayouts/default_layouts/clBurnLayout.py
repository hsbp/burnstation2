#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Burn Layout - CD/USB burning layout
#

import gtk, os, threading, time
from modules import clWidgets, clThreadedDownload, clEntry, functions, burn, mp3info

class BgJob(threading.Thread):
    def __init__(self,widget,fn):
        threading.Thread.__init__(self)
        self.widget = widget
        self.fn     = fn
        self.result = None

    def run(self):
        self.result=self.fn()
        if self.widget:
            gtk.gdk.threads_enter()
            self.widget.response(0)
            gtk.gdk.threads_leave()

class BurnLayout(gtk.Layout):
    def __init__(self, pyjama):
        self.pyjama = pyjama
        self.burner = burn.Burner()

        gtk.Layout.__init__(self)
        self.set_size(700,300)

        # might be obsolet
        self.pyjama.window.setcolor(self)

        self.pyjama.downloader.priorize_burn(self.pyjama.player.playlist)

    def draw(self, a, b, c, d):
        self.pyjama.window.tvList.clear()
        self.pyjama.window.toolbar.lbMoreAlbumsFromThisArtist2.hide()
        self.pyjama.window.toolbar.lbAppendAlbum.hide()
        self.table = gtk.HBox(True)
        self.table.set_size_request(800, 400)
        self.table.set_border_width(50)
        self.table.set_spacing(100)

        self.put(self.table, 0, 0)

        self.target_usb = gtk.Button()
        self.img_usb = gtk.Image()
        self.target_cd  = gtk.Button()
        self.img_cd = gtk.Image()

        self.img_usb.set_from_file(os.path.join(functions.install_dir(), "images", "burn_usb.png"))
        self.img_cd.set_from_file(os.path.join(functions.install_dir(), "images", "burn_cd.png"))
        self.target_usb.set_size_request(256,256)
        self.target_cd.set_size_request(256,256)
        self.img_usb.set_size_request(256,256)
        self.img_cd.set_size_request(256,256)

        self.target_usb.connect('clicked', self.cb_target_usb_clicked)
        self.target_cd.connect('clicked', self.cb_target_cd_clicked)

        self.target_usb.set_image(self.img_usb)
        self.target_cd.set_image(self.img_cd)

        self.table.pack_start(self.target_usb)
        self.table.pack_end(self.target_cd)

        self.show_all()

    def cb_target_usb_clicked(self, ev):
        self.pyjama.layouts.show_layout("burn_usb", 0, 0)

    def bgJob(self,msg,fn):
        dialog = clWidgets.MyDialog(msg,
                                    self.pyjama.window,
                                    gtk.DIALOG_MODAL,
                                    None,
                                    gtk.STOCK_DIALOG_WARNING,
                                    msg,
                                    sep=False)
        # start job in bg thread
        job=BgJob(dialog, fn)
        job.start()
        dialog.run()
        res=job.result
        dialog.destroy()
        return res

    def cdStatus(self):
        return self.bgJob(_("Checking disc status"),self.burner.cdIsWritable)

    def blankCD(self):
        return self.bgJob(_("Blanking disc"),self.burner.BlankCD)

    def cb_target_cd_clicked(self, ev):
        (isWritable,msg)=self.cdStatus()
        while not isWritable:
            buttons=None
            if msg == "** closed ** CD-RW":
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                         _("Blank CD"), gtk.RESPONSE_APPLY,
                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            else:
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
            msg=_("Please insert a writable CD/DVD!")
            dialog = clWidgets.MyDialog(msg,
                                        self.pyjama.window,
                                        gtk.DIALOG_MODAL,
                                        buttons,
                                        gtk.STOCK_DIALOG_WARNING,
                                        msg)
            response=dialog.run() # gtk.RESPONSE_NONE,
            dialog.destroy()
            if response in [-2,-4]:
                return
            if response == -10:
                self.blankCD()
            (isWritable,msg)=self.cdStatus()
        self.pyjama.mediaSize=msg
        self.pyjama.layouts.show_layout("burn_cd", 0, 0)

    class ToolBar(gtk.HBox):
        def __init__(self, pyjama):
            gtk.HBox.__init__(self)
            self.pyjama = pyjama
            self.layout = self.pyjama.layouts.layouts['top']

class BurnCDLayout(gtk.Layout):
    def __init__(self, pyjama):
        self.pyjama = pyjama

        gtk.Layout.__init__(self)
        self.set_size(700,300)

        # might be obsolete
        self.pyjama.window.setcolor(self)

        self.pyjama.window.liststore.connect('row-changed', self.cb_playlist_changed)
        self.pyjama.window.liststore.connect('row-deleted', self.cb_playlist_changed)
        self.pyjama.window.liststore.connect('row-inserted', self.cb_playlist_changed)

    def getDlStatus(self):
        ready=False
        while not ready:
            dl=self.pyjama.downloader.get_status()
            files=[t[0].local for t in dl if t[0].local]
            if len(files) == len(dl):
                ready=True
            else:
                gtk.gdk.threads_enter()
                self.dlStatus.set_label(_("Downloading %i of %i ..." % (len(dl)-len(files), len(dl))))
                gtk.gdk.threads_leave()
            time.sleep(0.4)

    def waitForDl(self):
        title=(_("Waiting for download to complete"))
        dialog = gtk.Dialog(title,
                            self.pyjama.window,
                            gtk.DIALOG_MODAL)
        dialog.set_has_separator(False)
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
        img.set_size_request(64, 64)
        hbox = gtk.HBox()
        dialog.vbox.pack_start(hbox)
        hbox.pack_start(img,False,False)
        vbox = gtk.VBox(True)
        vbox.set_border_width(8)
        vbox.set_spacing(8)
        hbox.pack_end(vbox)
        vtitle = gtk.Label(title)
        vtitle.set_markup(_("<b>%s</b>" % title))
        vbox.pack_start(vtitle)
        self.dlStatus = gtk.Label("")
        vbox.pack_end(self.dlStatus)
        dialog.show_all()
        # start job in bg thread
        progress=BgJob(dialog, self.getDlStatus)
        progress.start()
        dialog.run()
        dialog.destroy()

    def cb_playlist_changed(self, _tm, _iter, _x=None):
        for track in self.pyjama.player.playlist:
            self.pyjama.downloader.queue_push(track)
        if not 'mediaSize' in dir(self.pyjama): return
        dl=self.pyjama.downloader.get_status()
        files=[t[0].local[7:] for t in dl if t[0].local]
        if not len(files) == len(dl):
            # pop up dialog displaying how many are missing
            # wait until complete, continue
            self.waitForDl()
        size=0
        length=0
        self.tracks=[]
        for track in files:
            size+=os.path.getsize(track)
            file = open(track, "rb")
            mpeg3info = mp3info.MP3Info(file)
            file.close()
            length+= mpeg3info.mpeg.length
            self.tracks.append((track,length,size))
        mediaLength = (self.pyjama.mediaSize*2352*8) / 1411200 # bit/s
        #print mediaLength, length
        #print self.pyjama.mediaSize*2048, size
        if length<mediaLength:
            #print "can write as AUDIO"
            self.bAudio.set_sensitive(True)
            self.lWarning.hide()
        else:
            self.bAudio.set_sensitive(False)
        if size<=self.pyjama.mediaSize*2048:
            # write data
            #print "can write as DATA"
            self.bData.set_sensitive(True)
            self.lWarning.hide()
        else:
            self.bData.set_sensitive(False)
            # remove items from list in order to proceed.
            # and press the refresh button
            #print "music overload"
            self.bAudio.hide(True)
            self.bData.hide(True)
            self.lWarning.show()

    def updateStatus(self):
        while not self.burner.Finished:
            status=self.burner.GetStatus()
            if status:
                gtk.gdk.threads_enter()
                self.status.set_label(status)
                gtk.gdk.threads_leave()
            time.sleep(0.4)

    def burn(self):
        self.burner.BurnCD([x[0] for x in self.tracks], self.format)

    def burnCd(self):
        self.burner = burn.Burner()
        title=(_("Burning %s disc") % self.format)
        dialog = gtk.Dialog(title,
                            self.pyjama.window,
                            gtk.DIALOG_MODAL)
        dialog.set_has_separator(False)
        dialog.set_size_request(600, 60)
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)
        img.set_size_request(64, 64)
        hbox = gtk.HBox()
        dialog.vbox.pack_start(hbox)
        hbox.pack_start(img,False,False)
        vbox = gtk.VBox(True)
        vbox.set_border_width(8)
        vbox.set_spacing(8)
        hbox.pack_end(vbox)
        vtitle = gtk.Label(title)
        vtitle.set_markup(_("<b>%s</b>" % title))
        vbox.pack_start(vtitle)
        self.status = gtk.Label("")
        vbox.pack_end(self.status)
        dialog.show_all()
        # start job in bg thread
        job=BgJob(dialog, self.burn)
        job.start()
        progress=BgJob(None, self.updateStatus)
        progress.start()
        dialog.run()
        dialog.destroy()

        msg=_("Thank you!\n\nIf you like this music, please consider\ngoing to jamendo.com and donating to\nthe Artist, so that you can enjoy their\nmusic also in the future.")
        dialog = clWidgets.MyDialog(msg,
                                    self.pyjama.window,
                                    gtk.DIALOG_MODAL,
                                    (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT),
                                    gtk.STOCK_DIALOG_WARNING,
                                    msg)
        dialog.run() # gtk.RESPONSE_NONE,
        dialog.destroy()
        self.pyjama.layouts.show_layout("burn", 0, 0)

    def on_bData_activated(self, ev):
        #print "Burning data CD"
        self.format='DATA'
        self.burnCd()

    def on_bAudio_activated(self, ev):
        #print "Burning audio CD"
        self.format='AUDIO'
        self.burnCd()

    def draw(self, a, b, c, d):
        self.pyjama.window.tvList.clear()
        self.pyjama.window.toolbar.lbMoreAlbumsFromThisArtist2.hide()
        self.pyjama.window.toolbar.lbAppendAlbum.hide()
        self.table = gtk.HBox(True)
        self.table.set_size_request(800, 400)
        self.table.set_border_width(50)
        self.table.set_spacing(100)

        self.iData = gtk.Image()
        self.iData.set_from_file(os.path.join(functions.install_dir(), "images", "file-mp3-cd.png"))
        #self.iData.set_size_request(256,256)
        self.bData = gtk.Button()
        self.bData.set_image(self.iData)
        #self.bData.set_size_request(256,256)
        self.bData.set_tooltip_text(_("Burn as Data - MP3"))
        self.bData.connect("clicked", self.on_bData_activated)
        self.bData.connect("button_press_event", self.on_bData_activated)
        self.table.pack_start(self.bData)

        self.iAudio = gtk.Image()
        self.iAudio.set_from_file(os.path.join(functions.install_dir(), "images", "file-audio-cd.png"))
        #self.iAudio.set_size_request(256,256)
        self.bAudio  = gtk.Button()
        self.bAudio.set_image(self.iAudio)
        #self.bAudio.set_size_request(256,256)
        self.bAudio.set_tooltip_text(_("Burn as Audio"))
        self.bAudio.connect("clicked", self.on_bAudio_activated)
        self.bAudio.connect("button_press_event", self.on_bAudio_activated)
        self.table.pack_end(self.bAudio)

        self.lWarning = gtk.Label()
        self.lWarning.set_markup(_("<b>Rock'n'Roll overload</b>\nToo many tracks on playlist, please remove some to continue burning."))
        self.table.pack_end(self.lWarning, True, True, 0)

        self.put(self.table, 0, 0)
        self.show_all()

        self.cb_playlist_changed(0,0,0)

    class ToolBar(gtk.HBox):
        def __init__(self, pyjama):
            gtk.HBox.__init__(self)
            self.pyjama = pyjama
            self.layout = self.pyjama.layouts.layouts['top']

class BurnUSBLayout(gtk.Layout):
    def __init__(self, pyjama):
        self.pyjama = pyjama

        gtk.Layout.__init__(self)
        self.set_size(700,300)

        # might be obsolet
        self.pyjama.window.setcolor(self)

    def draw(self, a, b, c, d):
        self.pyjama.window.tvList.clear()
        self.pyjama.window.toolbar.lbMoreAlbumsFromThisArtist2.hide()
        self.pyjama.window.toolbar.lbAppendAlbum.hide()
        # draw the burn-cd dialog
        combo = gtk.ComboBox()
        for usb in functions.list_usb():
            combo.append_text(usb)

        self.put(combo, 0, 0)

        self.show_all()

    class ToolBar(gtk.HBox):
        def __init__(self, pyjama):
            gtk.HBox.__init__(self)
            self.pyjama = pyjama
            self.layout = self.pyjama.layouts.layouts['top']
