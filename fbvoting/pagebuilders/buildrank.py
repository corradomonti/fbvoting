# -*- coding: utf-8 -*-
from __future__ import division

from math import ceil
import logging

from flask import render_template, Markup

import fbvoting.apis.fb as fbapi
import fbvoting.db.chart as dbchart
from jsonchart import HOW_MANY_PER_PAGE as JSON_ITEMS
import commons

logger = logging.getLogger(__name__)

N_ITEM_PER_PAGE = 6

N_JSON_PAGES = int(N_ITEM_PER_PAGE / JSON_ITEMS)

assert N_ITEM_PER_PAGE % JSON_ITEMS == 0

def build_chart_overview():
    data = commons.get_base_data()
    header ="""
            Global Recommendations
            <small>
                Best tunes, from liquid democracy
            </small>
            """
    
    data.update({
        'active_section': 'charts',
        'header': Markup(header),
        'rank_type': 'chart'
    })
    
    return render_template('rank.html', **data)



def build_recommendation_overview():
    fbapi.ensure_token_is_valid()
    
    data = commons.get_base_data()
    header ="""
            Your Recommendations
            <small>
                Liquid advices from your delegates!
            </small>
            """
    
    
    data.update({
        'active_section': 'recommendation',
        'header': Markup(header),
        'rank_type': 'recommendation'
    })
    
    return render_template('rank.html', **data)


def build_category_chart_from_query(category, query):
    try:
        position = dbchart.find_position(query, category)
    except:
        logger.exception('Error while looking for recommendation with id "%s" in category %s.', query, category)
    
    if position is None:
        logger.warn('Somebody looked for recommendations with id "%s" in category %s but I dunno where that is.', query, category)
    else:
        return build_category_chart(category, int(position / N_ITEM_PER_PAGE), autoplay=query)
    
    return build_category_chart(category)



def build_category_chart(category, frontend_page=0, autoplay=None, playfirst=False):
    assert type(category) in (str, unicode)
    assert type(frontend_page) is int
    
    data = commons.get_base_data()
    
    data.update({
        'active_section': 'charts',
        'header': "Best tunes selected by liquid democracy",
        'rank_type': 'chart',
        'category': category,
        'json_pages': range(frontend_page*N_JSON_PAGES, (frontend_page+1)*N_JSON_PAGES),
        'pages': accessible_pages_from(frontend_page,  max_frontend_page_for(category)),
        'playfirst': playfirst
    })
    
    if autoplay is not None:
        data['autoplay_id'] = autoplay
    
    return render_template('rank-category.html', **data)

    
def build_category_recommendation(category, frontend_page=0, playfirst=False):
    fbapi.ensure_token_is_valid()
    data = commons.get_base_data()
    
    data.update({
        'active_section': 'recommendation',
        'header': "Advices from your Liquid delegates!",
        'rank_type': 'recommendation',
        'category': category,
        'json_pages': range(frontend_page*N_JSON_PAGES, (frontend_page+1)*N_JSON_PAGES),
        'pages': accessible_pages_from(frontend_page,  max_frontend_page_for(category)),
        'playfirst': playfirst
    })
    
    return render_template('rank-category.html', **data)    


def max_frontend_page_for(category):
    return int(ceil(dbchart.count(category) / N_ITEM_PER_PAGE))


HOW_MANY_LINKS = 3

def accessible_pages_from(n, max_number):
    assert type(n) is int
    assert type(max_number is int)
    
    before = range(max(0, n - HOW_MANY_LINKS), n)
    after = range(n+1, min(max_number, n + HOW_MANY_LINKS + 1))
    
    before = [(i, str(i + 1) ) for i in before]
    after  = [(i, str(i + 1) ) for i in after]
    
    if n > 0:
        before = [(n-1, u'← Previous')] + before
    
    if n < max_number - 1:
        after = after + [(n + 1, u'Next →')]
    
    return before + [ (n+1, None) ] + after




