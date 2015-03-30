/* load previous rating asynchronously */
var loadRatingOn = function(videoPlayingInterface) {
    var songData = videoPlayingInterface.data('songData');
    
    $.ajax({
        url: personal('/feedback/get/'+songData.category+'/'+songData.advice.video),
        dataType: 'text',
        success: function(rating) {
            rating = parseInt(rating);
            if (rating > 0) {
                videoPlayingInterface.children('.dislike-btn').removeClass('dislike-h');
                videoPlayingInterface.children('.like-btn').addClass('like-h');
            } else if (rating < 0) {
                videoPlayingInterface.children('.dislike-btn').addClass('dislike-h');
                videoPlayingInterface.children('.like-btn').removeClass('like-h');
            } else {
                videoPlayingInterface.children('.dislike-btn').removeClass('dislike-h');
                videoPlayingInterface.children('.like-btn').removeClass('like-h');
            }
        }
    });
};

$( document ).ready(function() {
    
    /* On like button click */
    $('.video-playing-interface .like-btn').click(function() {
        
        var currentlyLiked = $(this).hasClass('like-h');
        var songData = $(this).parents('.video-playing-interface').data('songData');
        
        var newRating = currentlyLiked ? 0 : 1;
        
        var feedbackUrl = personal('/feedback/put/'+songData.category+'/'+songData.advice.video);
        
        $.get(feedbackUrl, {rating: newRating})
            .fail(function() {alert('Error while saving rating.');});
        $(this).toggleClass('like-h');
        $(this).parent().children('.dislike-btn').removeClass('dislike-h');
        
    });
    
    /* On dislike button click */
    $('.video-playing-interface .dislike-btn').click(function() {
        
        var currentlyDisiked = $(this).hasClass('dislike-h');
        var songData = $(this).parents('.video-playing-interface').data('songData');
        
        var newRating = currentlyDisiked ? 0 : -1;
        
        var feedbackUrl = personal('/feedback/put/'+songData.category+'/'+songData.advice.video);
        
        $.get(feedbackUrl, {rating: newRating})
            .fail(function() {alert('Error while saving rating.');});
        $(this).toggleClass('dislike-h');
        $(this).parent().children('.like-btn').removeClass('like-h');
        
    });
    
    /* On share button click */
    $('.video-playing-interface .share-btn').click(function() {
        var songData = $(this).parents('.video-playing-interface').data('songData');
        var song = songData.advice.author + " - " + songData.advice.song;
        var link = 'https://apps.facebook.com/1404463766474015/chart/';
        link = link + songData.category + '?query=' + songData.advice.video;
        FB.ui({
            method: 'feed',
            link: link,
            picture: 'ssl.law.di.unimi.it' + songData.advice.cover,
            description: "Liquid FM is recommending me to listen to " + song + "!",
            caption: "Liquid FM: find the best music, through friends.",
        }, function(response){});
    });
    
});