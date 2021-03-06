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

## @package Jamendo
# The class Jamendo on this module manages communication
# with jamendo

#JSon parser
import simplejson as json

import os
import hashlib
import time

# URL Handling
from urllib2 import urlopen, URLError
from urllib import urlencode as _urlencode

try:
    import socket # for setting timeout
    timeout = 10
    socket.setdefaulttimeout(timeout)
except:
    print("Error setting timeout")

#own classes
import functions

# Gettext - Übersetzung
functions.translation_gettext()
#def _(string):
#    return string

###################################################################
#
# several urls for jamendo - should be moved to documentation
#
### ari = Artistinfo
### tri = Trackinfo
### ali = albuminfo
# ===> http://developer.jamendo.com/de/wiki/MusiclistApi_draft
# info_min or info_common or full.

### ALLE MÖGLICHEN ALBEN INFOS:
    #http://www.jamendo.com/get/album/id/album/data/json/33?ali=info_common+archives+tracker+lengths&ari=info_min&aenc=ogg3

### Alle Tracks eines Albums:
    # http://www.jamendo.com/get/track/id/album/data/json/33?ali=full&ari=full+object&tri=full&item_o=track_no_asc&showhidden=1&shownotmod=1
    
### Alle Infos zum Track:
    # http://www.jamendo.com/get/track/id/track/data/json/4707?ali=full&ari=full+object&tri=full&item_o=track_no_asc&showhidden=1&shownotmod=1

### 50 populäre alben von rock
   # http://api.jamendo.com/get2/id+name+url+image+artist_name/album/jsonpretty/?tag_idstr=rock&n=50&order=rating_desc

### Torrent, redirect
    # http://api.jamendo.com/get2/bittorrent/file/redirect/?album_id=919&type=archive&class=ogg3

### 20 artists alphabetically #0-9
    # http://www.jamendo.com/get2/name/artist/plain?order=alpha_asc&hasalbums=1&firstletter=a

#### Arists has albums
    # http://www.jamendo.com/get2/name/artist/plain?order=alpha_asc&firstletter=0-9&hasalbums=1&n=40

#### Soundslike
    # http://api.jamendo.com/get2/id+name/album/jsonpretty/album_album2_soundslike/?album2_id=116

#### Radio
    # Find radio by name
    # http://api.jamendo.com/get2/id+name+idstr/radio/jsonpretty/?radio_idstr=Alchimie
    # Get radio tracks
    # http://www.jamendo.com/get2/track_id/track/jsonpretty/radio_track_inradioplaylist/?order=numradio_asc&radio_id=17

## @cond skip
## This class isn't used at all.
# I was just wondering how to make
# this whole query thing more
# relyable for the developer.
class Query(object):
    def __init__(self, query=None, caching_time=None, raise_event=True, ignore_cache=False):
        self.query = query
        self.caching_time = caching_time
        self.raise_event = raise_event
        self.ignore_cache = ignore_cache

    def send(self):
        pass
## @endcond
        

## Module for interaction with jamendo
class Jamendo:
    ## Constructor
    def __init__(self, parent):
        self.__parent = parent
        self.__home = functions.preparedirs()
        ## The directory in which pyjama stores cached queries
        self.cachedir = os.path.join(self.__home, "cache")
        ## Counter for queries from cache
        self.cache_counter = 0
        ## Counter for queries from jamendo
        self.jamendo_counter = 0

        self.__last_query = None

        self.__ignore_cache = None

        self.__parent.Events.add_event("jamendo-query")
        
        # Somehow simplejsons behaviour
        # changed some times so i had to
        # do it this way. 
        # If this new behaviour won't change
        # again, the strict-statement is
        # obsolete
        try:
            self.json = json.JSONDecoder(strict=False)
        except:
            self.json = json.JSONDecoder()

    ## Get cover image for a given album
    # This function will download a image
    # if it's not on disc, yet.
    # Else it will return the local uri
    # @param self OP
    # @param album_id Id of the album 
    # @param size Size of the cover to get (default: 100)
    def get_album_image(self, album_id, size=100):
        image = "http://api.jamendo.com/get2/image/album/redirect/?id=%i&imagesize=%i" % (int(album_id), int(size))
        md5hash = hashlib.md5(image).hexdigest()
        fh = os.path.join(self.main.home, "images", md5hash)
        if not os.path.exists(fh):
            try:
                urllib.urlretrieve(image, fh)
                return fh
            except IOError:
                print ("Could not load image")
                return None
        else:
            return fh

    ## Let the next query no be loaded from cache
    # @param self Object Pointer
    # @param value Boolean
    # If True is set, the next query will be ignored
    def set_ignore_cache(self, value):
        self.__ignore_cache = value

    ## Will the next query be cached?
    # @return bool
    def get_ignore_cache(self):
        return self.__ignore_cache

    ## Is a given jamendo-query-result usable?
    # @return bool
    # @todo Tidy up return values
    def check(self, query):
        if query is None:
            return False
        if isinstance(query, list) and query == []:
            return False
        if isinstance(query, int) and query < 0:
            return False
        if isinstance(query, str) and query == "":
            return False
        return True

    ## Decode a json encoded string
    # @param self Object Pointer
    # @param string The string to decode
    # @return 
    # - None if an error occured
    # - The decoded string if successful
    def json_decode(self, string):
        try:
#            return simplejson.loads(string.decode('utf-8'))
#            x= json.read(string)

            return self.json.decode(string) 
        except Exception, inst:
            desc = "An error occured while parsing Jamendos server-response\n"
            desc += "Most probably this is a json issue coming up with new\n"
            desc += "versions of debian.\n"
            desc += "<b>Get the newest version of pyjama to deal with it!</b>"
            self.__parent.Events.raise_event("error", inst, desc)
            return None

    ## Do a jamendo query
    # This function is obsolete, run query() instead
    # @param self Object Pointer
    # @param field The fields to get (think of SELECT)
    # @param unit The table(s) from which you want to get (think of FROM)
    # @param params Additional params (think of WHERE)
    # @param format Which output format would you like to get?
    # Use json or jsonpretty
    # @return json string
    def get(self, field, unit, params, format="json"):
        print ("Requesting database on jamendo.com")
        query = "http://api.jamendo.com/get2/" + field + "/" + unit + "/" + format  + "/" + params
        if self.__parent.debug:
            print query
        source = urlopen(query)
        print ("Requesting database - done")
        return self.json_decode(source.read())

    ## Tests if a specific query can be found in cache and if it is up to date
    # This methode is called by query() function for that you should not call this
    # methode directly.
    # @param query The jamendo query you want to make
    # @param CACHING_TIME Must be CACHING_TIME_LONG or CACHING_TIME_SHORT from pyjama.cfg
    # This param decides where is looked for the cached query
    # @return
    # - False if query not in cache or to old
    # - The cached itself when its cached
    def cache(self, query, CACHING_TIME = None):
        if CACHING_TIME == None or CACHING_TIME == self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_LONG"):
            CACHING_TIME = self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_LONG")
            subdir = "long"
        else:
            subdir = "short"
        if self.__ignore_cache is True: 
            print "Ignoring Cache"
            CACHING_TIME = 0
        md5hash = hashlib.md5(query).hexdigest()
        datei = os.path.join(self.cachedir, subdir, md5hash)
        if os.path.exists(datei):
            file_time = os.stat(datei).st_mtime
            if file_time + CACHING_TIME > time.time():
                datei = open(datei,'r')
                content = datei.read()
                datei.close()
                remaining = CACHING_TIME - (time.time() - file_time)
                m = 60
                h = 60*m
                d = h*24
                #w = d*7
                days = remaining // d
                hours = (remaining - d*days) // h
                mins = ((remaining - d*days) - h*hours) // m
                secs = (((remaining - d*days) - h*hours) - m*mins)
                if self.__parent.verbose:
                    print ("This Query was loaded from Cache. New Data will be loaded from Jamendo  in %i days, %i hourse, %i minutes and %i seconds.") % (days, hours, mins, secs)
                    if CACHING_TIME == self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_LONG"):
                        print ("Don't mind this might be to long. This specific data- set won't change!")
#                self.__parent.window.sbStatus.set_text("Info", _("Aus dem Cache. Gültig noch %iT, %i:%i:%i") % (days, hours, mins, secs))
                self.__parent.window.sbStatus.set_text("Info", _("From Cache. Reload in %iD, %i:%i:%i") % (days, hours, mins, secs))
                self.cache_counter += 1
                return content
            print ("Cache too old, Loading Data from Jamendo")
            self.__parent.window.sbStatus.set_text("Info", _("Refreshing Cache"))
            return False
        print ("No Data cached, yet. Caching Query now")
        self.__parent.window.sbStatus.set_text("Info", _("Cached from Jamendo"))
        self.jamendo_counter += 1
        return False

    def __write2cache(self, query, result, caching_time = None):
        if caching_time == None or caching_time == self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_LONG"):
            subdir = "long"
        else:
            subdir = "short"
        if self.__parent.debug:
            print subdir
        md5hash = hashlib.md5(query).hexdigest()
        datei = os.path.join(self.cachedir, subdir, md5hash)
        fh = file(datei,'w')
        fh.write(result)
        fh.close()

    ## Query Jamendo via GET2 API
    # Allways use this function to query jamendo - it will automatically do the
    # caching and all the other stuff!
    # @param query The Jamendo query - strip of 'http://api.jamendo.com/get2/' (!)
    # @param caching_time Must be CACHING_TIME_LONG or CACHING_TIME_SHORT from pyjama.cfg
    # @return 
    # - None if this query came to fast after another
    # - -1 if jamendo could not be accesed
    # - Dictionary if succesfull
    def query(self, query, caching_time = None, raise_query_event=True):
        if raise_query_event:
            self.__parent.Events.raise_event("jamendo-query", "start")
        query = "http://api.jamendo.com/get2/" + query
        ret = self.cache(query, caching_time)
        if  ret != False: ##wenn cache daten vorliegen
            if raise_query_event:
                self.__parent.Events.raise_event("jamendo-query", "end")
            return self.json_decode(ret)
        if self.__last_query == None:
            self.__last_query = time.time()
        elif self.__last_query + 1 > time.time():
            print "To fast"
            print (query)
            if raise_query_event:
                self.__parent.Events.raise_event("jamendo-query", "end")
            return None
        else:
            self.__last_query = time.time()
        if self.__parent.verbose:
            print ("Requesting database on jamendo.com")
        if self.__parent.debug:
            print query
        try:
            source = urlopen(query)
        except URLError, inst:
            desc = "Could not query Data from jamendo. Perhaps Jamendo is maintening the servers or your connection is broken."
            self.__parent.Events.raise_event("error", inst, desc)
            print ("couldn't load from jamendo")
            if raise_query_event:
                self.__parent.Events.raise_event("jamendo-query", "end")
            return -1
        ret = source.read()
        self.__write2cache(query, ret, caching_time)
        if self.__parent.verbose:
            print ("Requesting database - done, wrote cache")
        if raise_query_event:
            self.__parent.Events.raise_event("jamendo-query", "end")
        return self.json_decode(ret)

    ## This hack prevents the jamendo class from aborting the query
    # with a "to fast" message - there should be a better solution
    def last_query_hack(self):
        self.__last_query=0

    ## Query Jamendo via REST API
    # This function handles queries for jamendo's old rest api.
    # Please try not to use this api.
    # @param query The Jamendo query - strip of 'http://api.jamendo.com/get2/' (!)
    # @param caching_time Must be CACHING_TIME_LONG or CACHING_TIME_SHORT from pyjama.cfg
    # @return 
    # - None if this query came to fast after another
    # - -1 if jamendo could not be accesed
    # - Dictionary if succesfull
    def queryold(self, query, caching_time = None, raise_query_event=True): 
        if raise_query_event:
            self.__parent.Events.raise_event("jamendo-query", "start")
        query = "http://www.jamendo.com/get/" + query
        ret = self.cache(query, caching_time)
        if  ret != False: ##wenn cache daten vorliegen
            if raise_query_event:
                self.__parent.Events.raise_event("jamendo-query", "end")
            return self.json_decode(ret)
        if self.__last_query == None:
            self.__last_query = time.time()
        elif self.__last_query + 1 > time.time():
            print ("To fast")
            print (query)
            if raise_query_event:
                self.__parent.Events.raise_event("jamendo-query", "end")
            return None
        else:
            self.__last_query = time.time()   
        print ("Requesting database on jamendo.com")
        if self.__parent.debug:
            print query
        try:
            source = urlopen(query)
        except URLError, inst:
            desc = "Could not query Data from jamendo. Perhaps Jamendo is maintening the servers or your connection is broken."
            self.__parent.Events.raise_event("error", inst, desc)
            print ("couldn't load from jamendo")
            if raise_query_event:
                self.__parent.Events.raise_event("jamendo-query", "end")
            return -1
        ret = source.read()
        self.__write2cache(query, ret, caching_time)
        print ("Requesting database - done, wrote cache")
        if raise_query_event:
            self.__parent.Events.raise_event("jamendo-query", "end")
        return self.json_decode(ret)

    ## Get albums similar to the given one
    # @param album_id The album to search similar albums for
    # @return results from query()
    def get_similar_albums(self, album_id, num=5):
        if self.__parent.debug: 
            print ("jamendo: getting similar albums")
        if num <= 0: return None
        ret = self.query("id/album/jsonpretty/album_album2_soundslike/?album2_id=%i&n=%i" % (album_id, num) )
        return ret

    ## Get albums from Jamendo
    # @param num Number of albums to fetch
    # @param order How the result are ordered (ratingweek, download ...)
    # @param page Which page should be fetched?
    # @param tag Only fetch albums with a particular tag
    # @return results from query()
    def top(self, num = 10, order = "tag", page=1, tag="all"):
        if self.__parent.debug: 
            print ("jamendo: getting top albums")
        if tag == "all": 
            if self.__parent.verbose:
                print ("Getting top %i ordered by '%s'") % (num, order)
            ret = self.query("artist_name+artist_idstr+artist_id+album_name+album_id+album_image+album_genre/album/json/?order=%s_desc&n=%i&pn=%s" % (order, num, page), self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_SHORT"))
        else:
            if self.__parent.verbose:
                print ("Getting %i albums tagged '%s' ordered by '%s'") % (num, tag, order)
            ret = self.query("artist_name+artist_idstr+artist_id+album_name+album_id+album_image+album_genre/album/json/?tag_idstr=%s&n=%i&pn=%s&order=%s_desc" % (tag, num, page, order), self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_SHORT"))
        return ret

    ## Get stream URL for a track
    # @param id The track-id
    # @return results from query()
    def stream(self, id):
        if self.__parent.debug: 
            print ("jamendo: getting stream")
        if self.__parent.verbose:
            print ("Getting stream informations")
        ret = self.query("stream/track/json/?id=%i&streamencoding=ogg2" % id, self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_LONG"))
        if ret == None:
            return None
        return ret[0]
                                #track/id/album/data/json/15395?ali=common_info+archives+artist&ari=full+object&tri=full&item_o=track_no_asc&showhidden=1&shownotmod=1

    ## Get infos for a track
    # Loads a plenty of track infos from jamendo
    # @param id The track id you want to query
    # @return results from query()
    def trackinfos(self, id):
        if self.__parent.debug: 
            print ("jamendo: getting track infos")
        if self.__parent.verbose:
            print ("Getting track informations")
        ret = self.queryold("track/id/track/data/json/%s?ali=full&ari=full+object+stream&tri=full&item_o=track_no_asc&showhidden=1&streamencoding=ogg2&shownotmod=1" % str(id), self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_LONG"))
        return ret

        #!!!! ret = self.queryold("track/id/album/data/json/%s?ali=full&ari=full+object&tri=full&item_o=track_no_asc&showhidden=1&shownotmod=1" % id) 

    ###################################################################
    #
    # old
    # RETURNS: dictionary
    #
    def albuminfos_altundmaechtig(self, id):
        if self.__parent.debug: 
            print ("jamendo: getting a lot of album infos")
        strQuery = "track/id/album/data/json/ID?ali=full&ari=full+object&tri=full&item_o=track_no_asc&showhidden=1&shownotmod=1"
        strQuery = strQuery.replace("ID", str(id))
        ret = self.queryold(strQuery, self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_LONG"))
        return ret

    ###################################################################
    #
    # get infos for a album
    # RETURNS: dictionary
    #
    def albuminfos(self, id):
        if self.__parent.debug: 
            print ("jamendo: getting album infos")
        if self.__parent.verbose:
            print ("Getting album informations")
        strQuery = "album/id/album/data/prettyjson/ID?ali=full&ari=full+object&item_o=track_no_asc&showhidden=1&shownotmod=1"
        strQuery = strQuery.replace("ID", str(id))
        ret = self.queryold(strQuery, self.__parent.settings.get_value("JAMENDO", "CACHING_TIME_LONG"))
        if ret == None:
            return None
        return ret[0]




#http://api.jamendo.com/get2/track_name+track_duration+track_url+license_url+album_id+album_name+artist_id+artist_idstr+artist_name/track/jsonpretty/album_artist/

    ###################################################################
    #
    # get an album's tracks
    # RETURNS: dictionary
    #
    def albumtracks(self, id): 
        if self.__parent.debug: 
            print ("jamendo: getting album's tracks")		
        ret = self.get("track_id+track_name+track_stream+track_duration+album_name", "track", "album_track/?album_id=" + str(id)+"&streamencoding=ogg2") 		
        return ret
        
    ###################################################################
    #
    # get an artist's album 
    # RETURNS: dictionary
    # 
    def artistalbums(self, idstr):
        if self.__parent.debug: 
            print ("jamendo: getting artist's albums")
        ret = self.get("album_id+album_name+album_playlist", "artist", "?idstr=" + idstr + "&ali=full")
        print ret
        return ret

    ###################################################################
    #
    # get a list of artists
    # RETURNS: dictionary
    #
    def artistlist(self):
        if self.__parent.debug: 
            print ("jamendo: getting artist list")
        ret =  self.get("id+idstr+name", "artist", "?artist_hasalbums&n=50")
        return ret
