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

import sys

try:
    from urlparse import parse_qs
    from urllib import unquote_plus
except ImportError:
    from urllib.parse import parse_qs, unquote_plus

import xbmc
import xbmcgui
import xbmcplugin

PLUGIN_ROOT = 'plugin://plugin.video.testlib/'

def get_mode(arg):
    if not arg in ('movies', 'tvshows'):
        raise ValueError('Invalid mode')
    return arg

def get_id(name, arg, mode):
    if arg == None:
        return None
    if name == 'id':
        if mode != 'movies':
            raise ValueError('Invalid ID')
    elif name in ('sid', 'eid'):
        if mode != 'tvshows':
            raise ValueError('Invalid ID')
    else:
        raise ValueError('Invalid ID')
    return arg

def get_arg(args, need_backslash, urlend_check=None):
    if not args:
        return None
    arg = args.pop(0)
    urlend = True if urlend_check != None and arg in urlend_check else not need_backslash
    if (need_backslash and not args) or (urlend and ((need_backslash and args[0]) or (not need_backslash and args))):
        raise ValueError('Invalid URL')
    if len(args) == 1 and not args[0]:
        del args[0]
    return arg

def set_arg(ret, name, arg):
    if name in ret:
        raise ValueError('Invalid URL')
    if arg != None:
        ret[name] = arg

def parse_args():
    ret = {}
    path = sys.argv[0][len(PLUGIN_ROOT):]
    if path:
        args = list(map(unquote_plus, path.split('/')))
        arg = get_arg(args, True, ('movies', 'tvshows'))
        if arg in ('lib', 'lib_noinfo'):
            ret['urltype'] = 1
            ret['noinfo'] = arg == 'lib_noinfo'
            arg = get_arg(args, True)
        else:
            ret['urltype'] = 2
        set_arg(ret, 'mode', get_mode(arg))
        if ret['urltype'] == 1:
            set_arg(ret, 'id1', get_arg(args, ret['mode'] == 'tvshows'))
            set_arg(ret, 'id2', get_arg(args, False))
    else:
        ret['urltype'] = 0
    args = parse_qs(sys.argv[2][1:])
    if 'mode' in args:
        set_arg(ret, 'mode', get_mode(unquote_plus(args['mode'][0])))
    for k,v in args.items():
        v = unquote_plus(v[0])
        if k in ('id', 'sid'):
            set_arg(ret, 'id1', get_id(k, v, ret.get('mode')))
        elif k == 'eid':
            set_arg(ret, 'id2', get_id(k, v, ret.get('mode')))
        elif k == 'noinfo':
            set_arg(ret, 'noinfo', True)
        elif k == 'kodi_action' and v == 'refresh_info':
            ret['refresh'] = True
    if 'id2' in ret and not 'id1' in ret:
        raise ValueError('Invalid URL')
    return ret if 'mode' in ret else {}

def show_menu():
    handle = int(sys.argv[1])
    xbmcplugin.setContent(handle, 'video')
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'?mode=movies', xbmcgui.ListItem('Movies (options mode)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'?mode=tvshows', xbmcgui.ListItem('TV Shows (options mode)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'lib/movies/', xbmcgui.ListItem('Movies (folder mode)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'lib/tvshows/', xbmcgui.ListItem('TV Shows (folder mode)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'movies/', xbmcgui.ListItem('Movies (mixed mode)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'tvshows/', xbmcgui.ListItem('TV Shows (mixed mode)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'?mode=movies&noinfo=1', xbmcgui.ListItem('Movies (options mode, only titles)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'?mode=tvshows&noinfo=1', xbmcgui.ListItem('TV Shows (options mode, only titles)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'lib_noinfo/movies/', xbmcgui.ListItem('Movies (folder mode, only titles)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'lib_noinfo/tvshows/', xbmcgui.ListItem('TV Shows (folder mode, only titles)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'movies/?noinfo=1', xbmcgui.ListItem('Movies (mixed mode, only titles)'), True)
    xbmcplugin.addDirectoryItem(handle, PLUGIN_ROOT+'tvshows/?noinfo=1', xbmcgui.ListItem('TV Shows (mixed mode, only titles)'), True)
    xbmcplugin.endOfDirectory(handle)

def plugin_main():
    try:
        args = parse_args()
    except ValueError as e:
        xbmc.log('[plugin.video.testlib]: {0}'.format(e), xbmc.LOGERROR)
        return

    if args:
        from library import main
        main(args.get('urltype', 0), args['mode'], args.get('id1'), args.get('id2'), args.get('refresh', False), args.get('noinfo', False))
    else:
        show_menu()


if __name__ == "__main__":
    plugin_main()
