DefaultText = {
    '$elements': null,
    'init': function() {
        DefaultText.$elements = $("input.default-text");
        DefaultText.bindFocusHandler();
        DefaultText.bindBlurHandler();
        DefaultText.$elements.trigger('focus');
        DefaultText.$elements.trigger('blur');
    },  
    'bindFocusHandler': function() {
        DefaultText.$elements.focus(DefaultText.focusHandler);
    },
    'focusHandler': function() {
        if ($(this).val() == $(this)[0].title) {
            $(this).removeClass("default-text-active");
            $(this).val("");
        }
    },
    'bindBlurHandler': function() {
        DefaultText.$elements.blur(DefaultText.blurHandler);
    },
    'blurHandler': function() {
        if ($(this).val() == "") {
            $(this).addClass("default-text-active");
            $(this).val($(this)[0].title);
        }
    }
};
$(DefaultText.init);
