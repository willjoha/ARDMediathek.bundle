import re
from collections import OrderedDict

# +++++ ARD Mediathek Plugin for Plex +++++
#
# Version 0.1
#
# Artwork (folder 'Resources'): (c) ARD
#
# TODO
# - Sendungen A-Z
# 

####################################################################################################

SENDUNGENAZURL = 'http://www.ardmediathek.de/ard/servlet/ajax-cache/3551682/view=module/index.html'
MOSTVIEWEDURL = 'http://www.ardmediathek.de/ard/servlet/ajax-cache/3516192/view=list/show=%s/index.html'

RE_SENDUNGVERPASSTLISTE = Regex('var sendungVerpasstListe = (\[[^\]]+\]);')
RE_DOCUMENTID = Regex('\?documentId=([0-9]+)$')

SENDUNGENAZ = OrderedDict()
SENDUNGENAZ['ABC']  = Regex('^[A-Ca-c]')
SENDUNGENAZ['DEF']  = Regex('^[D-Fd-f]')
SENDUNGENAZ['GHI']  = Regex('^[G-Ig-i]')
SENDUNGENAZ['JKL']  = Regex('^[J-Lj-l]')
SENDUNGENAZ['MNO']  = Regex('^[M-Om-o]')
SENDUNGENAZ['PQRS'] = Regex('^[P-Sp-s]')
SENDUNGENAZ['TUV']  = Regex('^[T-Vt-v]')
SENDUNGENAZ['WXYZ'] = Regex('^[W-Zw-z]')
SENDUNGENAZ['0-9']  = Regex('^[^A-Za-z]')

CATEGORY = [
#  ['Tatort', 'http://www.ardmediathek.de/export/rss/id=602916', 602916],
#  ['Mankells Wallander', 'http://www.ardmediathek.de/export/rss/id=10318954', 10318954],
#  ['Der Tatortreiniger', 'http://www.ardmediathek.de/export/rss/id=9174954', 9174954],
#  ['Lindenstraße', 'http://www.ardmediathek.de/export/rss/id=8078228', 8078228],
#  ['tagesschau', '', 4326]
]

NAME = 'ARD Mediathek'

ART = 'art-default.jpg'
ICON = 'icon-default.png'

BASE_URL = "http://www.ardmediathek.de"


####################################################################################################

def Start():
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)

    HTTP.CacheTime = CACHE_1HOUR

@handler('/video/ardmediathek', NAME, allow_sync=True)
def MainMenu():
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(SendungenAZ, name="Sendungen A-Z"), title="Sendungen A-Z"))
    oc.add(DirectoryObject(key=Callback(MostViewed, name="Meistabgerufene Clips - Heute", type='recent'), title="Meistabgerufene Clips - Heute"))
    oc.add(DirectoryObject(key=Callback(MostViewed, name="Meistabgerufene Clips - Gesamt", type='all'), title="Meistabgerufene Clips - Gesamt"))

    for item in CATEGORY:
        oc.add(DirectoryObject(key=Callback(Sendung, name=item[0].decode(encoding="utf-8", errors="ignore"), documentId=item[2]), title=item[0].decode(encoding="utf-8", errors="ignore")))

    return oc

@route('/video/ardmediathek/sendungenaz')
def SendungenAZ(name):
    oc = ObjectContainer(title2=name, view_group="List")
    
    # A to Z
    for page in SENDUNGENAZ:
        oc.add(DirectoryObject(key=Callback(SendungenAZList, char=page), title=page))
    
    return oc

@route('/video/ardmediathek/sendungenaz/{char}')
def SendungenAZList(char):
    oc = ObjectContainer(title2=char)
    data = HTTP.Request(SENDUNGENAZURL, cacheTime=CACHE_1HOUR).content
    list = RE_SENDUNGVERPASSTLISTE.findall(data, re.DOTALL)
    jsondata = JSON.ObjectFromString(list[0], 'utf-8')
    for sendung in jsondata:
        if(SENDUNGENAZ[char].match(sendung['titel']) == None):
            continue
        Log(sendung)
        title = html_decode(sendung['titel'])
        documentId = RE_DOCUMENTID.findall(sendung['link'])[0]
        oc.add(DirectoryObject(key=Callback(Sendung, name=title, documentId=documentId), title=title))
    return oc

@route('/video/ardmediathek/mostviewed/{type}')
def MostViewed(name, type):
    oc = ObjectContainer(title2=name)
    content = HTML.ElementFromURL(MOSTVIEWEDURL % type).xpath('//div[@class="mt-media_item"]')
    for item in content:
        link  = item.xpath('./h3[@class="mt-title"]/a')[0]
        title = link.text
        url   = BASE_URL + link.get('href')
        summary = item.xpath('./p[@class="mt-source mt-tile-view_hide"]')[0].text
        Log(summary)
        thumb = BASE_URL + item.xpath('./div[@class="mt-image"]/img/@src')[0]
        oc.add(VideoClipObject(
            url = url,
            title = title,
            summary = summary,
            thumb = thumb
        ))
    return oc


@route('/video/ardmediathek/sendung/{name}/{documentId}')
def Sendung(name, documentId):
    oc = ObjectContainer(title2=name)

    for item in XML.ElementFromURL('http://www.ardmediathek.de/export/rss/id=%s' % documentId).xpath('//item'):
        url = item.xpath('./link/text()')[0]
        title = item.xpath('./title/text()')[0]
        summary = item.xpath('./description/text()')[0]
        originally_available_at = Datetime.ParseDate(item.xpath('./pubDate/text()')[0])

        oc.add(VideoClipObject(
            url = url,
            title = title,
            summary = summary,
            originally_available_at = originally_available_at
        ))

    return oc

def html_decode(s):
    s = s.replace('&#039;', "'")
    s = s.replace('&quot;', '"')
    s = s.replace('&gt;', ">")
    s = s.replace('&lt;', "<")
    s = s.replace('&amp;', "&")
    return s