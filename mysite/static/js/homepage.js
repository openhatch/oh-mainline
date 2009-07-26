// Depends on jQuery

if (typeof $ == 'undefined') {
    alert('Oops, somebody forgot to import jQuery (a Javascript library)!');
}

var tabLinkClickHandler = function () {
    var link = this;
    $('.tab-links a').addClass('my-tab-is-hidden');
    $(link).removeClass('my-tab-is-hidden');
    console.log("tablinkclickhandler's this = ", $(link));
    $('.tab').addClass('invisible_if_js');
    var tab_selector = $(link).attr('tab_selector');
    $(tab_selector).removeClass('invisible_if_js');
    return false;
};

var bindTabEventHandlers = function () {
    $('.tab-links a').click(tabLinkClickHandler);
};

var prepareTabs = function () {
    // Hide all tabbed panels except the first.
    $('.tab:not(:eq(0))').addClass('invisible_if_js');
    $('.tab-links li:not(:first-child) a').addClass('my-tab-is-hidden');
}

$(bindTabEventHandlers);
$(prepareTabs);
