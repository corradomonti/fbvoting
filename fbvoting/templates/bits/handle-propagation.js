{% if token %}
    var token = {{token|json}};
{% endif %}
var domain = {{domain|json}};

// in case user has third-party cookies banned, I'll propagate tokens via GET
var personal = function(u) {
    
    if (typeof token === 'undefined') {
        try {
            var token = FB.getAuthResponse().accessToken;
        } catch (err) {
            return u;
        }
    }
    
    u = new Url(u);
    if (u.host == domain) {
        u.query.token = token;
    }
    
    return u.toString();
};

var update_links = function() {
    $("a[href]").each(function() { this.href =   personal(this.href);   });
    $('form'   ).each(function() { this.action = personal(this.action); });
};

$('body').on('onFacebookLoaded', function() {
    $.getJSON('/ajax/check-token/', function(r) {
        var cookiesWork = r['results'];
        
        if (!cookiesWork) {
            update_links();
        } else {
            personal = function(u) { return u; };
            update_links = $.noop;
        }
        $('body').trigger('propagationDefined');
        
    });
});

