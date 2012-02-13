#!/usr/bin/env python
#
# Author: Harrison Chapman
# This file contains the Album model, and auxiliary functions.
#  An Album object corresponds to a row in the Album table in the datastore

from __future__ import with_statement

# GAE Imports
from google.appengine.ext import db

# Local module imports
from base_models import *
from dj import Dj

# Global python imports
import logging

class Album(CachedModel):
  ENTRY = "album_key%s"

  NEW = "new_albums" # Keep the newest albums cached.
  MIN_NEW = 50 # We want to keep so many new albums in cache, since it's the
               # most typically ever encountered in normal website usage.
  MAX_NEW = 75 # There should be no reason to have more than this many
               # cached new albums, and beyond this is wasteful.

  # GAE Datastore properties
  title = db.StringProperty()
  asin = db.StringProperty()
  lower_title = db.StringProperty()
  artist = db.StringProperty()
  add_date = db.DateTimeProperty()
  isNew = db.BooleanProperty()
  songList = db.ListProperty(db.Key)
  cover_small = blobstore.BlobReferenceProperty()
  cover_large = blobstore.BlobReferenceProperty()

  @property
  def cover_small_key(self):
    return Album.cover_small.get_value_for_datastore(self)

  @property
  def cover_large_key(self):
    return Album.cover_large.get_value_for_datastore(self)

  def to_json(self):
    return {
      'key': str(self.key()),
      'title': self.title,
      'artist': self.artist,
      #'add_date': self.add_date,
      'song_list': [str_or_none(song) for song in self.songList],
      'cover_small_key': str_or_none(self.cover_small_key),
      'cover_large_key': str_or_none(self.cover_large_key),
      }

  # Right now, creating an album creates a bunch of new Songs on the spot
  # so you're probably going to want to put the album right after you make it
  # If you don't, you're a bad person and you hate good things
  def __init__(self, title, artist, tracks, add_date=None, asin=None,
               cover_small=None, cover_large= None, is_new=True,
               key=None, parent=None, key_name=None, **kwds):
    if add_date is None:
      add_date = datetime.datetime.now()
    if key is None:
      proto_key db.Key.from_path("Album", 1)
      batch = db.allocate_ids(proto_key, 1)
      key = db.Key.from_path('Album', batch[0])

    # Instantiate the tracks, put them (Model.put() returns keys)
    tracks = [Song(title=trackname,
                   artist=artist,
                   album=key,).put() for trackname in tracks]
    
    super(Album, self).__init__(parent=parent, key_name=key_name, 
                                key=key, title=title,
                                lower_title=title.lower(),
                                artist=artist,
                                add_date=add_date,
                                isNew=is_new,
                                songList=tracks,
                                **kwds)
    if cover_small is not None:
      self.cover_small = cover_small
    if cover_large is not None:
      self.cover_large = cover_large
    if asin is not None: # Amazon isn't working still as of time of writing
      self.asin = asin

  # TODO: make this a classmethod/instancemethod hybrid??? I wish I knew what
  # to friggin' Google.
  # TODO: generalize this interface (caches some "new" elements)
  @classmethod
  def addToNewCache(cls, key, add_date=None):
    if add_date is None:
      add_date = datetime.datetime.now()
    new_cache = cls.cacheGet(cls.NEW)
    if new_cache is not None:
      # New cache should already be sorted by date.
      next_idx = next(idx for idx, obj in 
                      itertools.izip(xrange(len(new_cache)-1, -1, -1,)
                                     reversed(new_cache)) if 
                      obj.add_date < add_date) # Probably returns wrong order
      #TODO fix this!! make new cache be a buncha tuples (key, date)

  def addToCache(self):
    super(Album, self).addToCache()
    return self

  def purgeFromCache(self):
    super(Album, self).purgeFromCache()
    return self

  @classmethod
  def get(cls, keys=None,
          title=None,
          num=-1, use_datastore=True, one_key=False):
    if keys is not None:
      return super(Album, cls).get(keys, use_datastore=use_datastore, 
                                        one_key=one_key)

    keys = cls.getKey(title=title, order=order, num=num)  
    if keys is not None:
      return cls.get(keys=keys, use_datastore=use_datastore)
    return None

  @classmethod
  def getKey(cls, title=None, artist=None, is_new=None,
             order=None, num=-1):
    query = cls.all(keys_only=True)

    if title is not None:
      query.filter("title =", title)
    if artist is not None:
      query.filter("artist =", artist)
    if is_new is not None:
      query.filter("isNew =", is_new)

    # Usual album orders: 'add_date'
    if order is not None:
      query.order(order)

    if num == -1:
      return query.get()
    return query.fetch(num)

  def put(self, is_new=None):
    if is_new is not None:
      self.p_is_new = is_new

    return super(Album, self).put()

  # Albums are immutable Datastore entries, except for is_new status.
  @property
  def p_title(self):
    return self.title
  @property
  def p_artist(self):
    return self.artist
  @property
  def p_tracklist(self):
    return self.songList
  @property
  def p_add_date(self):
    return self.add_date

  @property
  def p_is_new(self):
    return self.isNew
  @p_is_new.setter
  def p_is_new(self, is_new):
    self.isNew = is_new

  def set_new(self):
    self.isNew = True
  def unset_new(self):
    self.isNew = False

  @classmethod
  def getNew(cls, keys_only=False):
    allcache = cls.getByIndex(cls.ALL, keys_only=keys_only)
    if allcache:
      return allcache

    if keys_only:
      return cls.setAllCache(cls.getKey(order="title", num=1000))
    return cls.get(keys=cls.setAllCache(cls.getKey(order="title", num=1000)))
