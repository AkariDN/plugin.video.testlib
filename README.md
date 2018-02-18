# Kodi video plugin for testing media library

This plugin provides demo video content (movies and tv shows).
Use it for test Kodi media library scanning and updating.

Just add video source as:
* plugin://plugin.video.testlib/movies/ - for movies
* plugin://plugin.video.testlib/tvshows/ - for tv shows

Git repo: https://github.com/AkariDN/plugin.video.testlib

***
Plugin reads video information from videodb.xml (Kodi media library single folder export format) located at plugin profile or path (demo version included). For playing videos plugin uses test.mp4 located at plugin profile (not included, you have to copy any video file by your own to test video playback).

You can use different modes of passing parameters to plugin (for testing purposes):
* Options mode: all parameters passed as options string "?key1=value1&key2=value2"
* Folder mode: all parameters passed as path "/param1/param2" (except kodi_action)
* Mixed mode: "mode" passed as path and all other parameters passed as options string

NOTE: If you are using plugin url for video source with options string or in folder mode, you have to set the same scraper for parent url. So using "plugin://plugin.video.testlib/movies/" as video source do not require any additional settings. Currently Kodi uses following rules for parenting plugin urls:
* plugin://plugin.name/folder1/folder2/?options -> plugin://plugin.name/folder1/folder2/
* plugin://plugin.name/folder1/folder2/ -> plugin://plugin.name/
* plugin://plugin.name/?options -> plugin://plugin.name/

Parameters:
* mode: "movies" or "tvshows" - display movies or tvshows from database
* id, sid, eid - movie, tv show or episode id (the same as tag "id" from database)
* noinfo=1 - do not set any information except title and season and episode numbers
* kodi_action=refresh_info - reload item at specified path and return it as directory contents

To strip folder mode and mixed mode different paths are used:
* /mode/ - mixed mode
* /lib/mode/ - folder mode
* /lib_noinfo/mode/ - folder mode with noinfo

If no parameters are gived plugin displays menu with all available modes.

Also plugin calculates MD5 hash for tv shows folders (only path is used, no file size or datetime) and pass it to Kodi as 'hash' ListItem's property.

### Examples:

List movies:
```
plugin://plugin.video.testlib/?mode=movies
plugin://plugin.video.testlib/lib/movies/
plugin://plugin.video.testlib/movies/
```
List tvshows and display only titles (for testing external scraper):
```
plugin://plugin.video.testlib/?mode=tvshows&noinfo=1
plugin://plugin.video.testlib/lib_noinfo/tvshows/
plugin://plugin.video.testlib/tvshows/?noinfo=1
```
List episodes:
```
plugin://plugin.video.testlib/?mode=tvshows&sid=123
plugin://plugin.video.testlib/lib/tvshows/123/
plugin://plugin.video.testlib/tvshows/?sid=123
```
Refresh episode:
```
plugin://plugin.video.testlib/?mode=tvshows&sid=123&eid=456&kodi_action=refresh_info
plugin://plugin.video.testlib/lib/tvshows/123/456?kodi_action=refresh_info
plugin://plugin.video.testlib/tvshows/?sid=123&eid=456&kodi_action=refresh_info
```
Play movie:
```
plugin://plugin.video.testlib/?mode=movies&id=123
plugin://plugin.video.testlib/lib/movies/123
plugin://plugin.video.testlib/movies/?id=123
```
***
_Kodi® (formerly known as XBMC™) is a registered trademark of the XBMC Foundation._
