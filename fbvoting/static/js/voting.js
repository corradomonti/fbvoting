$( document ).ready(function() {
    // deactivate ENTER on text input fields to prevent accidental submit
    $('form input').keypress(function(event) { return event.keyCode != 13; });
    
    // detect change
    $('.dv-author').change( function() {
        clearVideos( $(this).data('num') );
        $('#changed').val('true');
    });
    $('.dv-song').change( function() {
        clearVideos( $(this).data('num') );
        $('#changed').val('true');
    });
    $('.dv-youtube-id').change( function() {$('#changed').val('true'); });
    
    $("#delegate_id").change(function() {
        $('#changed').val('true');
        if ($("#delegate_id").val().length > 0) {
            $('#notify-delegate').fadeIn();
        }
    });
    
    // ask confirm to exit if changed
    window.onbeforeunload = function() {
        if ($('#changed').val() == "true") {
            return "Your vote has not been submitted yet. Are you sure you want to leave?";
        } else {
            return null;
        }
    };
    
    
    // define error messaging functions
    var remove_error_msg = function() {
        $('#error-msg').hide();
        $('.input-error').removeClass('input-error');
    }
    
    var show_error = function(msg, field_selector) {
        $('#error-msg p').html(msg);
        $('#error-msg').show();
        
        if (field_selector != undefined) {
            $(field_selector).addClass('input-error');
            $(field_selector).change(remove_error_msg);
        }
    };
    
    // on form submit
    $('#input').submit(function() {
        
        // check if user has selected a friend from the autocomplete
        if ($('#delegate').val().length > 0 && $('#delegate_id').val().length == 0) {
            show_error("<strong>Person not found!</strong> You have to select a friend from the autocompleter: just start to write the correct name of one of your friends and it will appear.", '#delegate');
            return false;
        }
        
        // check if at least 1 field has been filled
        isFilled = function(form_id) { return ($.trim($('#' + form_id).val()).length > 0); };
        var delegateExists = isFilled("delegate_id");
        var directvoteExists = false;
        for (i = 0; i < N_ITEMS; i++) {
            if (isFilled('dv-author' + i) || isFilled('dv-song' + i) ) {
                directvoteExists = true;
                break;
            }
        }
        
        if (!delegateExists && !directvoteExists) {
            show_error("<strong>You can't submit an empty form! </strong> Please indicate at least a direct vote or a delegate.");
            return false; 
        }
        
        if (directvoteExists) {
            // first: check user has filled both author and title
            for (i = 0; i < N_ITEMS; i++) { 
                if (isFilled('dv-song' + i) && !isFilled('dv-author' + i)) {
                    show_error("To validate your vote, you \
                        have to insert also an author for your song n. "+i+".",
                        '#dv-author' + i);
                    return false; 
                }
                
                if (isFilled('dv-author' + i) && !isFilled('dv-song' + i)) {
                    show_error("To validate your vote n. "+ (i+1) +", you \
                        have to insert also a song title.", '#dv-song' + i);
                    return false; 
                }
            }
            
            // second: check validity of vote (in directvote.js)
            if (!valid_direct_vote(show_error)) {
                return false;
            }
            
            // third: check a youtube video has been selected
            for (i = 0; i < N_ITEMS; i++) { 
                if (isFilled('dv-song' + i) && !isFilled('dv-youtube-id' + i)) {
                    show_error("To validate your vote n. "+(i+1)+", you \
                        have to select also its youtube video.");
                    proposeVideo(i);
                    $('#dv-song' + i).addClass('input-error');
                    $('#dv-youtube-id' + i ).change(remove_error_msg);
                    return false; 
                }
            }
        }
        
        // no more "are you sure" upon leaving page
        window.onbeforeunload = function() { return null; };
    });
    
});