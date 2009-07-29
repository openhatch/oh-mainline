// Depends on jQuery

if (typeof $ == 'undefined') {
    alert('Oops, somebody forgot to import jQuery (a Javascript library)!');
}

var abstractTabLinkClickHandler = function (link) {
    $('.tab-links a').addClass('my-tab-is-hidden');
    $(link).removeClass('my-tab-is-hidden');
    $('.tab').addClass('invisible_if_js');
    var tab_selector = $(link).attr('tab_selector');
    $(tab_selector).removeClass('invisible_if_js');
    return false;
};

var tabLinkClickHandler = function() {
    return abstractTabLinkClickHandler(this);
};

var bindTabEventHandlers = function () {
    $('.tab-links a').click(tabLinkClickHandler);
};

var prepareTabs = function () {
    // Hide all tabbed panels except the first.
    $('.tab:not(:eq(0))').addClass('invisible_if_js');
    $('.tab-links li:not(:first-child) a').addClass('my-tab-is-hidden');

    // Check if we want to enable a particular tab.
    var hash = document.location.href.split('#')[1];
    if (hash) {
	if (hash.substr(0, 4) == 'tab=') {
	    tab_name = hash.substr(4);
	    /* Find the right <a> */
	    var link = $("a[tab_selector=#" + 
			 tab_name + "]")[0];
	    abstractTabLinkClickHandler(link);
	}
    }
}

$(bindTabEventHandlers);
$(prepareTabs);
