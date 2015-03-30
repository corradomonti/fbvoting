

var requestRank = function(parentId, category, type, page, afterLoading) {
    if (typeof(type) === "undefined") { type = "chart"; }
    if (typeof(page) === "undefined") { page = 0; }
    
    var url = personal("/ajax/rank/" + type + "/" + category + "?page=" + page);
    $.getJSON(url, success=function(data) {
        
        $('#' + parentId).find('.loading-ranks').remove();
    
        $.each(data.results, function(i, item) {
            appendElement(parentId, category, item);
        });
        
        if (data.results.length > 0) {
            if (afterLoading) {
                afterLoading();
            }
            
            assignHoverEvents();
            update_links();
        } else {
            $('#' + parentId).html("<big>No more songs on this page!</big>");
        }

    });
};

var appendElement = function(parentId, category, item) {
    var rank = Math.round(Number(item.rank) * 1000) / 10;
    var video = item.advice.video;
    
    var html = '                                                        \
        <div class="span3 column rank-item">                            \
            <div class="rank-infos position hover-infos">               \
                <big>#' + item['position'] + '</big><br />              \
                <span>hype: ' + rank + '% </span>                       \
            </div>                                                      \
            <div class="playable" id="'+parentId+'-play-'+video+'" >    \
                <a href="javascript:;">                                 \
                    <img src="' + item.advice.cover + '">               \
                </a>                                                    \
            </div>                                                      \
            <div class="rank-infos">                                    \
                <strong>' + item.advice.author + '</strong>             \
                <br /> ' + item.advice.song + '  <br />                 \
            </div>                                                      \
        </div>                                                          \
    ';
    
    item.category = category;
    item.playerHookId = category+'-video-hook';
    
    $('#' + parentId).append(html);
    $('#'+parentId+'-play-'+video+' a').click(item, loadVideo);
};

var findAndLoadNextVideo = function(clickItemEvent) {
    var currentIndex = $('.playable a').index(clickItemEvent.currentTarget);
    var indexToLoad = currentIndex + 1;
    
    if (indexToLoad < $('.playable a').length) {
        //element is on the page: just click it
        $('.playable a').get(indexToLoad).click();
    } else {
        var url = new Url(window.location.href);
        var currentPage = url.query.page;
        var nextPage = (currentPage === undefined) ? "1" : (parseInt(currentPage) + 1).toString();
        url.query.page = nextPage;
        url.query.playfirst = "1";
        window.location.href = url.toString();
    }
};

var loadVideo = function(clickItemEvent) {
    
    songData = clickItemEvent.data;
    videoId = songData.advice.video;
    playerHookId = clickItemEvent.data.playerHookId;
    
    // create and append the video iframe    
    var ytSrc = "https://www.youtube.com/embed/"+ videoId +"?rel=0&autoplay=1&autohide=0";
    ytSrc = ytSrc + '&enablejsapi=1';
    var playerId = playerHookId+'-player';
    var player = '\
        <div class="span my-player">                                   \
            <iframe id="'+playerId+'" src="' + ytSrc + '"              \
               class="youtube-player" type="text/html" frameborder="0">\
            </iframe>                                                  \
        </div>                                                         \
    ';
    $(".video-player").empty();
    $("#" + playerHookId).append(player);
    
    // change global function triggered by api loading
    onYouTubePlayerAPIReady = function() {
        ytfullplayer = new YT.Player(playerId, {
            events: {
              'onStateChange': function(ytEvent) {
                    feedbackVideo(ytEvent.data, clickItemEvent.data);
                    if (ytEvent.data == YT.PlayerState.ENDED ) {
                        findAndLoadNextVideo(clickItemEvent);
                    }
                }
            }
        });
    };
    
    // introduce youtube api js library asynchronously
    if ($('#yt-api-js-lib').length > 0) {
        onYouTubePlayerAPIReady(); // force the call
    } else {
        var tag = document.createElement('script');
        tag.src = "https://www.youtube.com/player_api";
        tag.setAttribute("id", "yt-api-js-lib");
        var firstScriptTag = document.getElementsByTagName('script')[0];
        firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }
    
    // assign data for playbutton.js
    $("#" + playerHookId).parent('.video-playing-interface').data('songData', songData);
    loadRatingOn($("#" + playerHookId).parent('.video-playing-interface'));
    
    // show everything, buttons included
    $('.video-playing-interface').hide();
    $("#" + playerHookId).parent('.video-playing-interface').show();


    
}

// send youtube feedback on behalf of the logged-in user
function feedbackVideo(youtubeStatus, adviceData) {
    
    if (youtubeStatus == YT.PlayerState.PLAYING) {
        playingStarted = new Date().getTime();
        currentlyPlaying = adviceData;
    }
    
    if (youtubeStatus == YT.PlayerState.PAUSED || youtubeStatus == YT.PlayerState.ENDED) {
        
        if (adviceData === undefined) {
            return;
        }
        
        var elapsedTime = (new Date().getTime() - playingStarted) / 1000;
        playingStarted = undefined;
        
        var feedbackUrl = personal('/feedback/put/'+adviceData['category']+'/'+adviceData.advice.video);
        $.get(feedbackUrl, {video_playback: elapsedTime})
            .fail(
                function() {console.log('Error while sending yt feedback.');}
            );
    }
}

// if user closes, I'll force the ENDED yt status, calling feedback
$(window).bind("beforeunload", function() {
    if ('YT' in window) {
        feedbackVideo(YT.PlayerState.ENDED, currentlyPlaying);
    }
})

// global variables needed by youtube api
var ytfullplayer;
function onYouTubePlayerAPIReady() {
    console.log('ERROR: YouTubePlayerAPI should not be loaded outside loadVideo().');
}

// global variables to give feedback
var playingStarted, currentlyPlaying;

// function to assign the transparency effect for playing button over image,
// after they've been loaded
var assignHoverEvents = function() {
    
    $('.rank-item img').unbind('mouseenter mouseleave');
    
    $('.rank-item img').hover(
        function() {
            $(this).closest('.rank-item').find('.hover-infos').css('opacity', 1);
            $(this).fadeTo("slow", 0.1);
        },
        function() {
            $(this).fadeTo("slow", 1.0);
            $(this).closest('.rank-item').find('.hover-infos').css('opacity', 0);
        }
    );
};
