import logging, os, os.path, subprocess, functools, re, random

from flask import Markup, abort, redirect, request, make_response

from fbvoting.db.directvote import count_all_nontest_votes, replace_all_videos
import fbvoting.db.delegatevote
import fbvoting.notifications.missingvotes
import fbvoting.db.categories
import fbvoting.apis.fb
import fbvoting.test
import fbvoting.conf
from fbvoting.lib import url_for
from fbvoting.serverutils import refresh_token

logger = logging.getLogger(__name__)

def for_admin(func):
    @functools.wraps(func)
    def func_for_admin(*a, **ka):
        if fbvoting.apis.fb.get_user_id() in fbvoting.conf.ADMIN_FB_IDS:
            return func(*a, **ka)
        else:
            logger.warn('somebody tried to access %s without admin privilege', func.__name__)
            logger.warn('ip address of unauthorized client: %s', request.remote_addr)
            abort(401)
    
    return func_for_admin


def authorized_ip_or_admin(func):
    @functools.wraps(func)
    def func_for_admin(*a, **ka):
        if (request.remote_addr in fbvoting.conf.AUTHORIZED_IPS
            or fbvoting.apis.fb.get_user_id() in fbvoting.conf.ADMIN_FB_IDS):
            logger.info("Ip address %s authorized for %s", request.remote_addr, func.__name__)
            return func(*a, **ka)
        else:
            logger.warn('somebody tried to access %s without admin privilege', func.__name__)
            logger.warn('ip address of unauthorized client: %s', request.remote_addr)
            abort(401)
    
    return func_for_admin

def invoke_jar():
    logger.warn("Manual updating of java ranking...")
    original_cwd = os.getcwd()
    JAR = fbvoting.conf.JAVA_CHART_JAR_PATH
    os.chdir(os.path.dirname(JAR))
    return_code = subprocess.call('java -jar ' + JAR, shell=True)
    subprocess.call('redis-cli FLUSHALL', shell=True)
    os.chdir(original_cwd)
    return return_code
    
def activate_admin_interface(route):
    
    style = """<style> body { font-family: "Monaco", monospace; } </style>"""
    dec = lambda s : s.decode('utf-8', 'ignore')
    
    @route('/admin/log/')
    @refresh_token
    @for_admin
    def _view_log_overview():
        out = dec(subprocess.check_output(
          r"ls -1t `find %s -name \*.log -mtime -1 ! -size 0` | xargs tail -n 4"
          % fbvoting.conf.LOGGING_DIRECTORY,
          shell=True))
        
        return Markup( style
            + out.replace('==>', '<h2>').replace('<==', '</h2>')
                 .replace('\n', '<br />')
                 .replace(fbvoting.conf.LOGGING_DIRECTORY , '<br />')
            )
    
    @route('/admin/log/<filename>')
    @refresh_token
    @for_admin
    def _view_specific_log(filename):
        if not re.match(r'^[\w-]+$', filename):
            return "Invalid filename"
        limit = int(request.args.get('limit', 40)) * 1000
        out = subprocess.check_output([ 'tac', # reverse of cat :-)
            fbvoting.conf.LOGGING_DIRECTORY + filename + ".log" ])
        return Markup(style + dec(out[:limit].replace('\n', '<br />')))
    
    @route('/admin/updatecharts')
    @refresh_token
    @for_admin
    def _update_charts():
        return_code = invoke_jar()
        
        if return_code == 0:
            return redirect(url_for('chart'))
        else:
            logger.error("Java chart ranking has exited with status " + str(return_code) )
            abort(500)
    
    
    @route('/admin/stats')
    @refresh_token
    @for_admin
    def _stats():
        s = ''
        for category_stat_func in (fbvoting.db.delegatevote.count_all_nontest_nominations, count_all_nontest_votes):
            s += "<h1>%s</h1><ul>" % category_stat_func.__name__
            tot = 0
            for cat in fbvoting.db.categories.categories():
                count = category_stat_func(cat)
                s += '<li>%s --> %i</li>' % (cat, count)
                tot += count
            
            s+= '</ul><p>Total: %i</p><hr />' % tot
        
        return Markup(style + s)
    
    
    @route('/admin/fakeusers')
    @refresh_token
    @for_admin
    def _fakeusers():
        fbvoting.test.tester.make_votes_for_all_category()
        logger.info("Votes created for fake users.")
        return Markup(
                "Votes created for the following users, in all categories:<ul><li>" +
                "</li><li>".join(map(str, fbvoting.test.TEST_USER_IDS)) +
                "</li></ul>"
                )
    
    @route('/admin/send-notification/missing-votes')
    @refresh_token
    @authorized_ip_or_admin
    def _send_notification():
        fbvoting.notifications.missingvotes.send_notifications()
        return "OK"
    
    @route('/admin/correct-videos/<wrongvideo>/<correctvideo>')
    @refresh_token
    @for_admin
    def _change_videos(wrongvideo, correctvideo):
        result = replace_all_videos(wrongvideo, correctvideo)
        invoke_jar()
        return Markup(style + '<br />'.join([("%s:\t%s" % x) for x in result.items()]))
    
    
    @route('/admin/remove-test-link/<p>/<category>')
    @refresh_token
    @for_admin
    def _remove_some_test_link(p, category):
        if category == 'all':
            categories = fbvoting.db.delegatevote.categories()
        else:
            categories = [category]
        
        n = 0
        for category in categories:
            for user in fbvoting.conf.TEST_USER_IDS:
                if fbvoting.db.delegatevote.get_delegate(user, category):
                    if random.random() < float(p):
                        fbvoting.db.delegatevote.assign_delegate(user, category, None)
                        logger.info("Removed test arc of user %s in category %s", user, category)
                        n += 1
        
        return "%i arcs removed" % n
    
    
    
    @route('/admin/download-graph/<category>')
    @refresh_token
    @for_admin
    def _get_graph(category):
        logger.info("Producing graph for user %s, category %s", fbvoting.apis.fb.get_user_id(), category)
        if category not in fbvoting.db.categories.categories():
            return "Category not found. Valid categories: %s" % fbvoting.db.categories.categories()
        graph = subprocess.check_output([ 'sh', fbvoting.conf.BASEPATH+ 'print-graph.sh', category])
        response = make_response(graph)
        response.headers["Content-Disposition"] = "attachment; filename=%s.dot" % category
        response.headers["Content-Type"] = "application/doc"
        logger.info("Graph produced")
        return response
    
    
    
    @route('/admin/redis')
    @refresh_token
    @for_admin
    def _redis_ping():
        out = dec(subprocess.check_output(r"redis-cli ping", shell=True))
        return Markup(style + "$> PING <br/>" + out)
    
    
