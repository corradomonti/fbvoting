select_delegate = function (friend) {
    $('#delegate').hide();
    $('#asking-name').hide();
    $('#delegate').val(friend.name);
    
    $('#chosen').show();
    FB.api('/'+friend.id+'/', function(friend) {
        imgsrc = "https://graph.facebook.com/"
            + friend.id + "/picture?"
            + "width=80&height=80";
       
        $('#chosen img').attr("src", imgsrc);
    });
    $('#chosen .name').text(friend.name);
    $("#delegate_id").val(friend.id);
    $("#delegate_id").trigger('change');
    $("#delegate").trigger('change');
    $('#notify-delegate input').attr('checked', true);
};

unselect_delegate = function () {
    $('#chosen').fadeOut();
    $('#notify-delegate').fadeOut();
    $('#chosen img').attr("src", '/static/images/80px-loader.gif');
    $('#chosen .name').text('');
    $("#delegate_id").val('');
    $("#delegate_id").trigger('change');
    
    $('#delegate').show();
    $('#asking-name').show();
    $('#delegate-input-container').html('<input class="xlarge" autocomplete="off" id="delegate" name="delegate" size="30" type="text">'); // i need to redo this, apparently
    activateDelegateAutocomplete();
}

activateDelegateAutocomplete = function() {
    $('#delegate').facebookAutocomplete({
      showAvatars: true,
      avatarSize: 50,
      maxSuggestions: 4,
      onpick: select_delegate
    });
};

$('body').on( "onFacebookLoaded", activateDelegateAutocomplete);