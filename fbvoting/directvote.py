""" Contains the description of a direct vote. """

from flask import Markup

import fbvoting.conf
import fbvoting.apis.lastfm
import fbvoting.apis.musicbrainz

class DirectVote(object):
    description = None
    input_id = None
    db_id = None
    visible = True
    
    def __init__(self, ):
        assert all([type(x) in (unicode, str)
                for x in (self.description, self.input_id, self.db_id)])
    

class Author(DirectVote):
    description = "Author name"
    input_id = "dv-author"
    db_id = "author"
    
class Song(DirectVote):
    description = "Title"
    input_id = "dv-song"
    db_id = "song"


class YoutubeId(object):
    description = "Youtube Video"
    input_id = "dv-youtube-id"
    db_id = "video"
    visible = False



DIRECT_VOTE = (Author(), Song(), YoutubeId())

def validate(dbdoc):
    return fbvoting.apis.musicbrainz.check_existence_of(
        dbdoc[Author.db_id], dbdoc[Song.db_id]
    )[0]


def dbdocs2str(docs):
    assert type(docs) is list
    strings = ['%s - "%s"' % ( doc[Author.db_id], doc[Song.db_id] ) for doc in docs]
    if len(strings) == 0:
        return ''
    elif len(strings) == 1:
        return strings[0]
    else:
        return ", ".join(strings[:-1]) + " and " + strings[-1]

def dbdoc2comparable(doc):
    return (
        (Author.db_id,  doc[Author.db_id].lower()),
        (Song.db_id,    doc[Song.db_id].lower())
    )

def attach_cover_to_dbdoc(doc):
    assert type(doc) is dict
    doc['cover'] = fbvoting.apis.lastfm.get_cover(doc[Author.db_id], doc[Song.db_id])
    return doc

def _dbdoc2html(doc, category=None):
    if doc is None:
        return None
    assert type(doc) is dict
    
    author_html, song_html, edit_html, play_html = '', '', '', ''
    
    if Author.db_id in doc:
        author_html = "<td><strong>" + doc[Author.db_id] + "</strong></td>"
    
    if Song.db_id in doc:
        song_html = "<td>" + doc[Song.db_id] + "</td>"
    
    if YoutubeId.db_id in doc:
        play_html = """ <a href="https://www.youtube.com/v/%s" target="_blank">
                            <img src="static/images/play-small.png" title="play" alt="play" width="14" height="15" />
                        </a>""" % doc[YoutubeId.db_id]
    
    edit_html = """ <a href="votes/%s">
                            <img src="static/images/edit-small.png" title="edit" alt="edit" width="14" height="15" />
                        </a>""" % category
    
    return """
        <tr>
            %s
            %s
            <td>
                %s
                %s
            </td>
        </tr>
        """ % (author_html, song_html, edit_html, play_html)

def dbdocs2html(docs, category=None):
    return Markup(
        "<table>" +
        ''.join([_dbdoc2html(d, category=category) for d in docs]) +
        "</table>"
    ) if docs else ''


def form2dbdocs(form):
    
    dbdocs = []
    for i in range(fbvoting.conf.N_ITEMS):
        dbdoc = {}
        for field in DIRECT_VOTE:
            value = form.get(field.input_id + str(i))
            if value:
                dbdoc[field.db_id] = value.strip()
        
        if dbdoc:
            dbdocs.append(dbdoc)
    
    return dbdocs

    