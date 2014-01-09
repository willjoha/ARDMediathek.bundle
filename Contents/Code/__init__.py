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

CATEGORY = [
  ['Tatort', 'http://www.ardmediathek.de/export/rss/id=602916', 602916],
  ['Mankells Wallander', 'http://www.ardmediathek.de/export/rss/id=10318954', 10318954],
  ['Der Tatortreiniger', 'http://www.ardmediathek.de/export/rss/id=9174954', 9174954],
  ['Lindenstraße', 'http://www.ardmediathek.de/export/rss/id=8078228', 8078228],
  ['tagesschau', '', 4326]
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

    for item in CATEGORY:
        oc.add(DirectoryObject(key=Callback(Sendung, name=item[0].decode(encoding="utf-8", errors="ignore"), documentId=item[2]), title=item[0].decode(encoding="utf-8", errors="ignore")))

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