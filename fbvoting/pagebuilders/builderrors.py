from random import choice
import logging

from flask import render_template

from fbvoting.db.chart import chart_iterator
from fbvoting.db.categories import categories
from fbvoting.mylogging import report

logger = logging.getLogger(__name__)

def build_error(error_code):
    
    data = dict()
    
    try:
        category = choice(categories())
        data['video'] = next(chart_iterator(category))['advice']['video']
        data['extra_message'] = "Here's some of our best %s music to chill you out." % category
    except:
        logger.exception("An error message with error code %i has encountered a problem even with serving a video :-(", error_code)
    
    report.mark('error' + str(error_code))
    
    return render_template('error.html', **data)
