
$( document ).ready(function() {
    
    // initialize autocompleters
    $('.dv-author').autocomplete({
        serviceUrl: '/ajax/musicbrainz/search/artist',
        paramName: 'q',
        minChars:4,
        deferRequestBy: 100, //milliseconds
        triggerSelectOnValidInput: false,
        preventBadQueries: false,
        params:  { category: $('#category').val() },
        onSearchStart:    function() { $(this).addClass('loading');    },
        onSearchComplete: function() { $(this).removeClass('loading'); },
        onSearchError:    function() { $(this).removeClass('loading'); }
    });
    
    $('.dv-song').autocomplete({
        serviceUrl: '/ajax/musicbrainz/search/song',
        paramName: 'q',
        deferRequestBy: 100, //milliseconds
        triggerSelectOnValidInput: false,
        params:  { category: $('#category').val(), artist: undefined },
        onSearchStart:    function() {
            var currentArtist = $('#dv-author' + $(this).data('num') ).val();
            $(this).autocomplete().options.params.artist = currentArtist;
            $(this).addClass('loading');
        },
        preventBadQueries: false,
        onSearchComplete: function() { $(this).removeClass('loading'); },
        onSearchError:    function() { $(this).removeClass('loading'); },
        onSelect:         function() { proposeVideo( $(this).data('num') ); }
    });
    
});

// functions for loading youtube videos from results of apis
var loadYoutubeVideoById = function(videoId) {
    var ytSrc = "https://www.youtube.com/embed/"+ videoId +"?rel=0&autoplay=0";
    $("#videoselect iframe").attr("src", ytSrc);
};

var loadYoutubeResult = function(i) {
    loadYoutubeVideoById($('#videoselect').data('results')[i].id.videoId);
    $('#videoselect').data('currentVideo', i);
};

// refuse the current api result
var nextYoutubeResult = function() {
    var total = $('#videoselect').data('results').length;
    var next = ($('#videoselect').data('currentVideo') + 1) % total;
    loadYoutubeResult(next);
}

// accept the current api result
var acceptYoutubeVideo = function() {
    var whichVideo = $('#videoselect').data('currentVideo');
    var whichVote = $('#videoselect').data('which-vote');
    var videoId = $('#videoselect').data('results')[whichVideo].id.videoId;
    $('#dv-youtube-id' + whichVote ).val(videoId);
    $('#dv-youtube-id' + whichVote ).trigger('change');
    $('#videoselect-input').fadeOut();
    $("#videoselect iframe").attr("src", "");
    $('#videoselect-thanks').fadeIn();
};

// search apis and propose videos
var proposeVideo = function(i) {
    
    if ($('#dv-song' + i).val().length > 0) {
        
        $('#video-match-what').text(" " + $('#dv-song' + i).val());
        $('#videoselect').data('which-vote', i);
        
        var ajaxQueryUrl = '/ajax/youtube/search?';
        ajaxQueryUrl+= $.param( {
            'q':  ($('#dv-author' + i).val() + ' ' + $('#dv-song' + i).val()),
            'max-results': 10
            } );
        
        $('#videoselect-input').show();
        $('#videoselect-thanks').hide();
        $('#videoselect-error').hide();
        
        $('#videoselect').fadeIn(1000);
        $.ajax(ajaxQueryUrl)
            .done(function(response) {
                if (response.results.length == 0) {
                    $('#videoselect-error').show();
                    $('#videoselect-input').hide();
                } else {
                    $('#videoselect').data('results', response.results);
                    loadYoutubeResult(0);
                }
            });
    }
    
};

// clear results
var clearVideos = function(i) {
    $('#videoselect').data('results', undefined);
    $('#videoselect').data('which-vote', undefined);
    $('#dv-youtube-id' + i).val('');
    $('#videoselect-input').show();
    $('#videoselect').hide();
    $('#videoselect-thanks').hide();
    $('#videoselect-error').hide();
}

var correct = function(field, s, which) {
    var element = $('#' + field + which);
    element.autocomplete().disable();
    element.val(s);
    element.trigger('change');
    $('#error-msg').fadeOut(200);
    if (field == "dv-song") {
        proposeVideo(element.data('num'));
    }
    element.autocomplete().enable();
};

// validation after submission
var validation;
var valid_direct_vote = function(show_error_func) {
    
    $('#submit-btn').parent().addClass('loading');
    validation = undefined;
    $.ajax({
        url: '/ajax/musicbrainz/check/',
        type: 'POST',
        data: $('#input').serialize(),
        async: false,
    }).done(function(response) {
        validation = response; // must be synchronous here
    });
    $('#submit-btn').parent().removeClass('loading');
    
    if (validation === undefined) {
        /* server-side error (logged there) */
        show_error_func("Something went wrong with your vote :-( <br /> \
            Please, try again or <a href='/about#contacts'>contact us</a>.");
        return false;
    }
    
    if (validation.results[0] /* is ok */) {
            return true;
        } else {
            if (show_error_func != undefined) {
                show_error_func(validation.results[1], '#' + validation.results[2]);
            }
            clearVideos();
            return false;
        }
};
