import datetime, logging
from collections import defaultdict
from operator import itemgetter

from flask import render_template, Markup

from fbvoting.apis.fb import get_user_id
from fbvoting.db.directvote import has_direct_or_delegate_vote
from fbvoting.db.delegatevote import delegation_category_and_date_generator
from fbvoting.db.users import get_rank_and_percentiles
from fbvoting.db.categories import categories
from fbvoting.conf import DOMAIN
import commons

logger = logging.getLogger(__name__)

def build_profile():
    
    userid = get_user_id()
    
    count_genre, count_time = get_stat_counters(userid)
    total_nominations = sum(count_genre.values())
    dates, date_values, timeplot_options = prepare_time_plot(count_time)
    
    data = commons.get_base_data()
    data.update({
        'active_section': 'profile',
        'brief_comment': get_plural_and_brief_comment(total_nominations),
        'total_nominations': total_nominations,
        'nonzero': total_nominations > 0
    })
    
    if total_nominations > 0:
        best_category = max(count_genre.items(), key=itemgetter(1))[0]
        data.update({
            'share_message': get_share_message(total_nominations, best_category),
            'picture': '%s/static/images/categories/%s.jpg' % (DOMAIN, best_category),
            'dates': dates,
            'date_values': date_values,
            'categories': categories(),
            'category_values': [count_genre.get(c, 0) for c in categories()],
            'timeplot_options': timeplot_options,
            'categories_with_requests': categories_with_requests(userid, count_genre)
        })
        
        data.update(get_ranking_infos(userid))
        
    else:
        data.update({
            'picture': DOMAIN + '/static/images/liquid-fm-icon-medium.png',
            'share_message': """
            Do you trust my taste in music, or you'd like to share yours?
            Do it with Liquid FM!
            """
        })
    
    return render_template('profile.html', **data)


_fmt = lambda x : ("%.0f" % x) if x > 1 else str(x) 

def get_ranking_infos(user):
    stats = get_rank_and_percentiles(user)
    
    infos = sorted( [
            (cat, scores['perc'])
            for (cat, scores) in stats.items()
            if scores['perc'] < 51
        ], key = itemgetter(1))
    
    if not infos:
        return {}
    else:
        results = {}
    
    best_genre, best_perc = infos[0]
    guru_status = best_perc < 10
    
    title = (best_genre + " " +
        ("guru" if guru_status else "expert") + "!"
    )
    
    share_msg = (
        title + ' I am in the top ' + _fmt(best_perc) + '% of all ' +
        'Liquid FM users when it comes to ' + best_genre + ' music!'
    )
    
    details = (
                "<p>According to our ranking system, " +
                "you're <strong>in the top " + _fmt(best_perc) + "%</strong> of all Liquid FM "+
                "users when it comes to <strong>" + best_genre + "</strong> music! " +
                "That means <a href='votes/" + best_genre + "'>your " +
                best_genre + " votes</a> are " +
                ("very " if guru_status else "") + "important to the community. </p>"
              )
    
    if len(infos) > 1:
        details += "<p>Also, you're"
        other_genres = [ ("in the top <strong>" + _fmt(p) + "%</strong> for <strong>" + c + "</strong>") for (c, p) in infos[1:]]
        
        if len(other_genres) == 1:
            details +=  " " + other_genres[0] + "."
        else:
            details += ": <ul><li>" + "</li><li>".join(other_genres) + "</li></ul>"
        
        details += "</p>"
    
    
    results['ranking_infos'] = Markup("""
        <div class="row"><div class="span3">
        <img class="circled" width="150" height="150" alt="" src="/static/images/categories/%s.jpg" />
        </div><div class="span6 guru-status"><h1>%s</h1></div></div>
        %s
        """ % (best_genre, title, details) )
    
    results['picture_guru'] = DOMAIN + ('/static/images/categories/%s.jpg' % best_genre)
    results['share_guru'] = share_msg
    
    return results



def get_plural_and_brief_comment(n):
    if n == 0:
        return "s, yet!"
    if n == 1:
        return " from a friend!"
    return "s from your friends!"

def categories_with_requests(user, stats_genre):
    assert type(user) in (int, long)
    
    return [
        genre for genre, nominations in stats_genre.items()
        if nominations > 0
        and not has_direct_or_delegate_vote(user, genre)
    ]
    


def get_share_message(tot, best_category):
    times = ("%i times " % tot) if tot > 1 else ""
    return ("I've been nominated %son Liquid FM, and\
             I've discovered that my friends trust my taste in %s music!"
            % (times, best_category) )


def get_stat_counters(userid):
    count_genre = defaultdict(int)
    count_time = defaultdict(int)
    
    for category, date in delegation_category_and_date_generator(userid):
        count_genre[category] += 1
        week = date.timetuple().tm_yday / 7
        count_time[date.year, week] += 1
    
    return count_genre, count_time

def get_current_year_week():
    now = datetime.datetime.now().timetuple()
    return now.tm_year, now.tm_yday / 7


def prepare_time_plot(count_time):
    if len(count_time) == 0:
        return [datetime.datetime.now().strftime("%d %B %Y")], [0], {}
    
    labels = []
    data = []
    
    today = datetime.date.today()
    
    def get_label(year, week):
        date = datetime.date(year, 1, 1) + datetime.timedelta(7 * (week +1))
        if date > today: # it does not make sense to show future dates
            date = today
        return date.strftime("%d %B %Y")
    
    
    year, week = min(count_time.keys())
    labels.append(get_label(year, week - 1))
    data.append(0)
    
    total_value = 0
    for ((year, week), value) in sorted(count_time.items()):
        labels.append(get_label(year, week))
        total_value += value
        data.append(total_value)
    
    current_year, current_week = get_current_year_week()
    while year < current_year or week < (current_week-1):
        week += 1
        if week == 52:
            week = 0
            year += 1
        
        labels.append(get_label(year, week))
        data.append(total_value)
    
    
    if len(data) < 10:
        options = {
        'scaleOverride' : True,
        'scaleSteps' : max(data),
        'scaleStepWidth' : 1,
        'scaleStartValue' : 0,
        }
    else:
        options = {}
    
    return labels, data, options
    


