
// Initialize the Facebook JavaScript SDK
window.fbAsyncInit = function() {
  $('#loading-wheel').show();
  FB.init({
    appId  : {{app_id}},
    status : true, // check login status
    cookie : true, // enable cookies to allow the server to access the session
    xfbml  : true  // parse XFBML
  });
  
  // Check if the current user is logged in and has authorized the app
  FB.getLoginStatus(checkLoginStatus);
  
};

(function() {
  var e = document.createElement('script');
  e.src = 'https://connect.facebook.net/en_US/all.js';
  e.async = true;
  document.getElementById('fb-root').appendChild(e);
}());

// Function to authenticate the user for my scopes
function authUser() {
  $('#loginButton').hide();
  $('#loading-wheel').show();
  FB.login(checkLoginStatus, {scope: {{FBAPI_SCOPE|json}} });
}

function authWithButton() {
    $('#fb-error-msg').show().html('<p>\
                To use Liquid FM you need to log in on Facebook. <br /> \
                A pop-up window to authenticate should be opening right now. \
            </p>');
    authUser();
}

// Check the result of the user status and display login button if necessary
function checkLoginStatus(response) {
  if(response && response.status == 'connected') {
    
    // Get token to server
    $.ajax({
        url: '/auth',
        type: 'POST',
        data: {'token': FB.getAuthResponse().accessToken },
        success: function() {
            // Say to the rest of the page "hey, FB is ready, come to eat!"
            $('body').trigger('onFacebookLoaded');
        },
        error: function() {
            $('#fb-error-msg').show().html('<p>\
                There is a problem communicating from Facebook to our server. <br /> \
                Please, try again or <a href="/about#contacts">contact us</a>. \
            </p>');
            $('.loading-authentication').hide();
        }
    });
    
  } else {
        $('#loginButton').show();
        $('#loading-wheel').hide();
  }
  
}
