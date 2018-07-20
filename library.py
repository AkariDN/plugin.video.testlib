# -*- coding: utf-8 -*-
# Kodi video plugin for testing media library.
# Copyright (C) 2018 AkariDN
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import hashlib
import xml.etree.ElementTree as ET
try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON = xbmcaddon.Addon()

# tag, type (0: string, 1: int, 2: float, 3: stringlist)
tag_types = {
    'genre':            3,
    'country':          3,
    'year':             1,
    'episode':          1,
    'season':           1,
    'sortepisode':      1,
    'sortseason':       1,
    'top250':           1,
    'director':         3,
    'mpaa':             0,
    'plot':             0,
    'plotoutline':      0,
    'title':            0,
    'originaltitle':    0,
    'duration':         1,
    'studio':           3,
    'tagline':          0,
    'tvshowtitle':      0,
    'premiered':        0,
    'status':           0,
    'tag':              0,
    'code':             0,
    'aired':            0,
    'credits':          3,
    'trailer':          0,
    'dateadded':        0
}

tag_mappings = {
    'plotoutline':      'outline',
    'tvshowtitle':      'showtitle',
    'duration':         'runtime',
    'sortseason':       'displayseason',
    'sortepisode':      'displayepisode'
}

def log(msg, lvl=xbmc.LOGNOTICE):
    xbmc.log('[plugin.video.testlib]: {0}'.format(msg), lvl)

def enc(s):
    try:
        return s.encode('utf-8') if isinstance(s, unicode) else str(s)
    except NameError:
        return str(s)

def iteritems(d):
    try:
        return d.iteritems()
    except AttributeError:
        return d.items()

def tag_text(xml, tag, tag_type=0):
    s = xml.find(tag)
    if s == None:
        return None
    s = s.text
    if s == None:
        return None
    if tag_type == 0:
        return enc(s)
    elif tag_type == 1:
        return int(s)
    elif tag_type == 2:
        return float(s)
    else:
        return s

def load_tags(xml):
    ret = {}
    for k,v in iteritems(tag_types):
        if v == 3:
            data = [enc(e.text) for e in xml.iterfind(tag_mappings.get(k, k)) if e.text]
            if data:
                ret[k] = data
        else:
            s = tag_text(xml, tag_mappings.get(k, k), v)
            if s != None and (v != 1 or s != -1):
                ret[k] = s if k != 'duration' else s*60
    ret = {'info': ret}
    data = xml.find('id')
    if data != None:
        ret['id'] = enc(data.text)
    data = {int(e.get('number')): enc(e.text) for e in xml.iterfind('namedseason')}
    if data:
        ret['seasons'] = data
    section = xml.find('ratings')
    if section != None:
        ret['ratings'] = [(e.get('name'), tag_text(e, 'value', 2), tag_text(e, 'votes', 1), e.get('default') == 'true') for e in section.iterfind('rating')]
    data = [(e.text, e.get('aspect'), int(e.get('season', -1))) for e in xml.iterfind('thumb')]
    if data:
        ret['thumbs'] = data
    section = xml.find('fanart')
    if section != None:
        url = section.get('url', '')
        ret['fanart'] = [{k: v for k,v in iteritems({'image': url+e.text, 'preview': url+e.get('preview')}) if v} for e in section.iterfind('thumb')]
    data = {}
    default = ''
    for e in xml.iterfind('uniqueid'):
        t = e.get('type')
        if not t:
            continue
        data[t] = e.text
        if e.get('default') == 'true':
            default = t
    if data:
        ret['uniqueids'] = (data, default)
    data = [{k: v for k,v in iteritems({'name': tag_text(e, 'name'), 'role': tag_text(e, 'role'), 'thumbnail': tag_text(e, 'thumb'), 'order': tag_text(e, 'order', 1)}) if v != None} for e in xml.iterfind('actor')]
    if data:
        ret['actors'] = data
    section = xml.find('art')
    if section != None:
        ret['art'] = {e.tag: e.text for e in section if e.tag != 'season'}
        data = ret.get('thumbs', [])
        for e in section.iterfind('season'):
            season = int(e.get('num'))
            for i in e:
                thumb = (i.text, i.tag, season)
                if not thumb in data:
                    data.append(thumb)
        if data and not 'thumbs' in ret:
            ret['thumbs'] = data
    return ret

def load_tvshow(xml):
    ret = load_tags(xml)
    ret['episodes'] = [load_tags(e) for e in xml.iterfind('episodedetails')]
    return ret

def get_path(pathtype, fn):
    path = xbmc.translatePath(ADDON.getAddonInfo(pathtype))
    try:
        return os.path.join(path.decode('utf-8'), fn.decode('utf-8'))
    except AttributeError:
        return os.path.join(path, fn)

def get_database_path():
    path = get_path('profile', 'videodb.xml')
    if os.path.exists(path):
        return path;
    return get_path('path', 'videodb.xml')

def load_database(mode):
    xml = ET.ElementTree(file=get_database_path()).getroot()
    if mode == 'movies':
        return [load_tags(e) for e in xml.iterfind('movie')]
    elif mode == 'tvshows':
        return [load_tvshow(e) for e in xml.iterfind('tvshow')]
    else:
        return None

def mkitem(data, mediatype, url, noinfo):
    info = data['info']
    title = info['title']
    if noinfo:
        new_info = {'title': title}
        if mediatype == 'episode' and 'season' in info and 'episode' in info:
            new_info['season'] = info['season']
            new_info['episode'] = info['episode']
        info = new_info
    li = xbmcgui.ListItem(title)
    if mediatype != 'tvshow':
        path = url.split('?', 1)
        info['path'] = path[0] if len(path) > 1 else 'plugin://plugin.video.testlib/'
        info['filenameandpath'] = url
        li.setMimeType('application/mp4')
        li.setContentLookup(False)
        li.setProperty('IsPlayable', 'true')
    else:
        info['path'] = url
        li.setMimeType('x-directory/normal')
    info['mediatype'] = mediatype
    li.setInfo('video', info)
    if noinfo:
        return li
    for k,v in iteritems(data.get('seasons', {})):
        li.addSeason(k, v)
    for i in data.get('ratings', []):
        li.setRating(i[0], i[1], i[2], i[3])
    for i in data.get('thumbs', []):
        li.addAvailableArtwork(i[0], i[1], season=i[2])
    if 'fanart' in data:
        li.setAvailableFanart(data['fanart'])
    if 'uniqueids' in data:
        d = data['uniqueids']
        li.setUniqueIDs(d[0], d[1])
    if 'actors' in data:
        li.setCast(data['actors'])
    if 'art' in data:
        li.setArt(data['art'])
    return li

def list_videos(handle, data, mediatype, url, noinfo, hash_url=None):
    xbmcplugin.setContent(handle, mediatype+'s')
    isfolder = mediatype == 'tvshow'
    for d in data:
        if not 'id' in d:
            continue
        vid = quote_plus(d['id'])
        path = url.format(vid)
        li = mkitem(d, mediatype, path, noinfo)
        if hash_url and 'episodes' in d:
            found = False
            m = hashlib.md5()
            for e in d['episodes']:
                if 'id' in e:
                    m.update(hash_url.format(vid, quote_plus(e['id'])).encode('utf-8'))
                    found = True
            li.setProperty('hash', m.hexdigest().upper() if found else '')
        xbmcplugin.addDirectoryItem(handle, path, li, isfolder)
    xbmcplugin.endOfDirectory(handle)

def play_video(handle, data, mediatype, url, noinfo):
    if not data:
        return
    xbmcplugin.setContent(handle, mediatype+'s')
    li = mkitem(data, mediatype, url, noinfo)
    li.setPath(get_path('profile', 'test.mp4'))
    li.setProperty('original_listitem_url', url)
    li.setProperty('get_stream_details_from_player', 'true')
    xbmcplugin.setResolvedUrl(handle, True, li)

def reply(handle, ret):
    xbmcplugin.setResolvedUrl(handle, ret, xbmcgui.ListItem())

def check_exists(handle, data):
    reply(handle, data != None)

def quote(arg):
    return arg if arg[:1] == '{' and arg[-1:] == '}' and arg[1:-1].isdigit() else quote_plus(arg)

def mkurl(urltype, mode, id1, id2, noinfo):
    url = 'plugin://plugin.video.testlib/'
    opt = []
    if urltype == 1:
        url += ('lib_noinfo' if noinfo else 'lib') + '/'
    if urltype:
        url += mode + '/'
    else:
        opt.append(('mode', mode))
    if urltype == 1:
        url += quote(id1)
        if mode == 'tvshows':
            url += '/'
        if id2:
            url += quote(id2)
    else:
        opt.append(('sid' if mode == 'tvshows' else 'id', quote(id1)))
        if id2:
            opt.append(('eid', quote(id2)))
        if noinfo:
            opt.append(('noinfo', '1'))
    if opt:
        url += '?'
        for i in opt:
            url += i[0] + '=' + i[1] + '&'
        url = url[:-1]
    return url

def get_subdata(data, vid):
    try:
        return next(i for i in iter(data) if i.get('id') == vid)
    except StopIteration:
        log('ID {0} not found'.format(vid), xbmc.LOGERROR)
        return None

def get_subdatalist(data, i):
    ret = get_subdata(data, i)
    return [ret] if ret != None else []


def main(urltype, mode, id1, id2, refresh, check, noinfo, handle):
    data = load_database(mode)
    if not data:
        reply(handle, False)
        return
    if mode == 'movies':
        if id1:
            url = mkurl(urltype, mode, id1, None, noinfo)
            if refresh:
                log('Refresh movie {0}'.format(id1))
                list_videos(handle, get_subdatalist(data, id1), 'movie', url, noinfo)
            elif check:
                log('Check movie {0}'.format(id1))
                check_exists(handle, get_subdata(data, id1))
            else:
                log('Play movie {0}'.format(id1))
                play_video(handle, get_subdata(data, id1), 'movie', url, noinfo)
        else:
            if check:
                log('Check movies')
                reply(handle, True)
            else:
                log('List movies')
                list_videos(handle, data, 'movie', mkurl(urltype, mode, '{0}', None, noinfo), noinfo)
    elif mode == 'tvshows':
        if id1:
            if id2:
                data = get_subdata(data, id1)
                if not data or not 'episodes' in data:
                    reply(handle, False)
                    return
                data = data['episodes']
                url = mkurl(urltype, mode, id1, id2, noinfo)
                if refresh:
                    log('Refresh tvshow {0} episode {1}'.format(id1, id2))
                    list_videos(handle, get_subdatalist(data, id2), 'episode', url, noinfo)
                elif check:
                    log('Check tvshow {0} episode {1}'.format(id1, id2))
                    check_exists(handle, get_subdata(data, id2))
                else:
                    log('Play tvshow {0} episode {1}'.format(id1, id2))
                    play_video(handle, get_subdata(data, id2), 'episode', url, noinfo)
            else:
                if refresh:
                    log('Refresh tvshow {0}'.format(id1))
                    list_videos(handle, get_subdatalist(data, id1), 'tvshow', mkurl(urltype, mode, id1, None, noinfo), noinfo)
                elif check:
                    log('Check tvshow {0}'.format(id1))
                    check_exists(handle, get_subdata(data, id1))
                else:
                    data = get_subdata(data, id1)
                    if data and 'episodes' in data:
                        log('List tvshow {0} episodes'.format(id1))
                        list_videos(handle, data['episodes'], 'episode', mkurl(urltype, mode, id1, '{0}', noinfo), noinfo)
                    else:
                        reply(handle, False)
        else:
            if check:
                log('Check tvshows')
                reply(handle, True)
            else:
                log('List tvshows')
                list_videos(handle, data, 'tvshow', mkurl(urltype, mode, '{0}', None, noinfo), noinfo, mkurl(urltype, mode, '{0}', '{1}', noinfo))

