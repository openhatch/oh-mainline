/*
Simple OpenID Plugin
http://code.google.com/p/openid-selector/

This code is licenced under the New BSD License.
*/

var providers_large = {
  google: {
    name: 'Google',
    url: 'https://www.google.com/accounts/o8/id'
  },
  yahoo: {
    name: 'Yahoo',      
    url: 'http://yahoo.com/'
  },    
  aol: {
    name: 'AOL',     
    label: 'Enter your AOL screenname.',
    url: 'http://openid.aol.com/{username}/'
  },
  openid: {
    name: 'OpenID',     
    label: 'Enter your OpenID.',
    url: null
  }
};
var providers_small = {
  myopenid: {
    name: 'MyOpenID',
    label: 'Enter your MyOpenID username.',
    url: 'http://{username}.myopenid.com/'
  },
  livejournal: {
    name: 'LiveJournal',
    label: 'Enter your Livejournal username.',
    url: 'http://{username}.livejournal.com/'
  },
  flickr: {
    name: 'Flickr',        
    label: 'Enter your Flickr username.',
    url: 'http://flickr.com/{username}/'
  },
  technorati: {
    name: 'Technorati',
    label: 'Enter your Technorati username.',
    url: 'http://technorati.com/people/technorati/{username}/'
  },
  wordpress: {
    name: 'Wordpress',
    label: 'Enter your Wordpress.com subdomain.',
    url: 'http://{username}.wordpress.com/'
  },
  blogger: {
    name: 'Blogger',
    label: 'Enter your Blogger username.',
    url: 'http://{username}.blogspot.com/'
  },
  verisign: {
    name: 'Verisign',
    label: 'Enter your Verisign username.',
    url: 'http://{username}.pip.verisignlabs.com/'
  },
  vidoop: {
    name: 'Vidoop',
    label: 'Enter your Vidoop username.',
    url: 'http://{username}.myvidoop.com/'
  },
  claimid: {
    name: 'ClaimID',
    label: 'Enter your ClaimID username.',
    url: 'http://claimid.com/{username}'
  },
  launchpad: {
    name: 'LaunchPad',
    label: 'Enter your Launchpad username.',
    url: 'https://launchpad.net/~{username}'
  },
  fedora: {
    name: 'Fedora',
    label: 'Enter your Fedora username.',
    url: 'https://admin.fedoraproject.org/accounts/openid/id/{username}'
  }
};
var providers = $.extend({}, providers_large, providers_small);

var openid = {

  cookie_expires: 6*30,	// 6 months.
  cookie_name: 'openid_provider',
  cookie_path: '/',

  img_path: '/static/openid/images/',

  input_id: null,
  provider_url: null,
  provider_name: null,

  init: function(input_id) {

    var openid_btns = $('#openid_btns');

    this.input_id = input_id;
    
    $("#"+ input_id).type = "hidden"

    $('#openid_choice').show();
    $('#openid_input_area').empty();

    // add box for each provider
    for (id in providers_large) {

      openid_btns.find('.large').append(this.getBoxHTML(providers_large[id], 'large', '.gif'));
    }
    if (providers_small) {
      //openid_btns.append('<br/>');

      for (id in providers_small) {

        openid_btns.find('.small').append(this.getBoxHTML(providers_small[id], 'small', '.png'));
      }
    }
    $('#openid_form').submit(this.submit);

    var self = this;
    $('.openidProvider').bind("click", function(e) {

            /*
             * If the user clicked 'Google' or 'Yahoo',
             * we're about to redirect them to a Google or Yahoo page.
             * In at least Firefox, this means that the user will be
             * waiting around on our site for a few seconds while the
             * external page loads. It's not always terribly clear the
             * browser is actually doing something during these few seconds,
             * and users might get the idea that our website is a
             * load of crap.
             *
             * To avoid this situation, let's indicate explicitly
             * that we are contacting Google/Yahoo.
             */

            var provider_id = e.target.id;
            if (provider_id == 'google' || provider_id == 'yahoo') {

                // Hide form and display explanatory message.
                $('#openid_form p').hide();
                $('#openid_btns').html(
                    '<div id="openid_while_u_wait">' +
                    'Requesting credentials from ' +
                    providers_large[provider_id].name +
                    '&hellip;</div>');

                // If the user has recently clicked another provider,
                // a textfield, labelled, for example, "Enter your Flickr username",
                // will be visible. Let's remove that.
                $('#openid_input_area').remove();

                // Remove the "Sign in with a password" link.
                $('a#sign-in-with-a-password').remove();

                /*
                 * Note that removing the form itself seems to cause problems.
                 */
            }

            self.signin(e.target.id);
            return false;
            });

    var box_id = this.readCookie();
    if (box_id) {
      this.signin(box_id, true);
    }  

  },
  getBoxHTML: function(provider, box_size, image_ext) {

    var box_id = provider["name"].toLowerCase();
    return '<a title="'+provider["name"]+'" href="#" id="' + box_id + '"' +
    ' style="-moz-border-radius: 8px; border-radius: 8px; background: #fff url(' + this.img_path + box_id + image_ext+') no-repeat center center" ' + 
    'class="openidProvider ' + box_id + ' openid_' + box_size + '_btn"></a>';    

  },

  /* Provider image click */
  signin: function(box_id, onload) {

    var provider = providers[box_id];
    if (! provider) {
      return;
    }

    this.highlight(box_id);
    this.setCookie(box_id);

    // prompt user for input?
    if (provider['label']) {

      this.useInputBox(provider);
      this.provider_url = provider['url'];
      this.provider_name = provider['name'];

    } else {
      this.provider_url = null;
      this.setOpenIdUrl(provider['url']);
      if (! onload) {
        $('#openid_form').submit();
      }	
    }
  },
  /* Sign-in button click */
  submit: function() {
    var url = openid.provider_url;
    if (url) {
      if(openid.provider_name=='Wordpress'){
        url = url.replace('http://', '')
      }
      url = url.replace('{username}', $('#openid_username').val());
      openid.setOpenIdUrl(url);
    } 
    return true;
  },
  
  setOpenIdUrl: function (url) {
    var hidden = $('#'+this.input_id);
    if (hidden.length > 0) {
      hidden.val(url);
    } else {
      $('#openid_form').append('<input type="hidden" id="' + this.input_id + '" name="openid_url" value="'+url+'"/>');
    }
    
  },
  highlight: function (box_id) {

    // remove previous highlight.
    var highlight = $('#openid_highlight');
    if (highlight) {
      highlight.replaceWith($('#openid_highlight a')[0]);
    }
    // add new highlight.
    $('.'+box_id).wrap('<div id="openid_highlight"></div>');
  },
  setCookie: function (value) {

    var date = new Date();
    date.setTime(date.getTime()+(this.cookie_expires*24*60*60*1000));
    var expires = "; expires="+date.toGMTString();

    document.cookie = this.cookie_name+"="+value+expires+"; path=" + this.cookie_path;
  },
  readCookie: function () {
    var nameEQ = this.cookie_name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
      var c = ca[i];
      while (c.charAt(0)==' ') c = c.substring(1,c.length);
      if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
  },
  useInputBox: function (provider) {

    var input_area = $('#openid_input_area');

    var html = '';
    var id = 'openid_username';
    var name = id;
    var value = '';
    var label = provider['label'];
    var style = '';
    var before_submit = '';

    if (label) {
      html = '<p>' + label + '</p>';
    }
    if (provider['name'] == 'OpenID') {
      id = this.input_id;
      name = "openid_url";
      value = 'http://';
      style = 'background:#FFF url('+this.img_path+'openid-inputicon.gif) no-repeat scroll 0 50%; padding-left:18px;';
    }
    else if (provider['name'] == 'Wordpress') {
      value = 'http://';
      before_submit = '<span id="wordpress-domain">.wordpress.com</span>'
    }
    html += '<input id="'+id+'" type="text" style="'+style+'" name="'+name+'" value="'+value+'" />' + before_submit +
    '<input id="openid_submit" type="submit" value="Sign in"/>';

    input_area.empty();
    input_area.append(html);

    $('#'+id).focus();
  }
};
