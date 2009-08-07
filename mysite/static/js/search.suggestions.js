Suggns = {
    '$list': null,
    '$toggleLink': null,
    '$submitButton': null,
    '$suggestionsToHide': null,
    '$terms': null,
    '$queryField': null,
    'allSuggestionsVisible': true,
    'init': function() {

        // Initialize variables that store jQuery objects.
        Suggns.$list = $('form#suggested_searches ul');
        Suggns.$toggleLink = $('#toggle-more-suggestions');
        Suggns.$submitButton = $('form#suggested_searches input:submit');
        Suggns.$terms = $('form#suggested_searches li');
        Suggns.$queryField = $('#language');

        Suggns.updateSuggestionsToHide();
        Suggns.toggler();

        // Bind event handlers.
        Suggns.bindToggler();
        Suggns.bindQueryManipulators();
        Suggns.bindCheckboxUpdater();
        Suggns.bindCheckboxLabelEmphasisToggler();

        // The submit button's only for when Javascript isn't happening.
        Suggns.$submitButton.hide();
    },
    'updateSuggestionsToHide': function() {
        // At first, prepare to conceal *all* suggestions.
        Suggns.$suggestionsToHide = $('#suggested_searches li');

        var keepMeVisible = function() {
            // Call this function on a jQuery object that
            // stands in for a single checkbox. 
            Suggns.$suggestionsToHide =
                Suggns.$suggestionsToHide.not($(this).parent());
        };

        var $checkboxen = Suggns.$terms.find('input:checkbox');

        // Don't conceal the checked suggestions.
        $checkboxen.filter(':checked').each(keepMeVisible);

        // Don't conceal the first four unchecked suggestions.
        $checkboxen.not(':checked').slice(0,4).each(keepMeVisible);
    },
    'bindToggler': function() {
        Suggns.$toggleLink.click(Suggns.toggler);
    },
    'toggler': function() {
        Suggns.updateSuggestionsToHide();
        if (Suggns.allSuggestionsVisible) {
            Suggns.$suggestionsToHide.hide();
            Suggns.allSuggestionsVisible = false;
        }
        else {
            Suggns.$suggestionsToHide.show();
            Suggns.allSuggestionsVisible = true;
        }
        var determiner = Suggns.allSuggestionsVisible ? 'fewer' : 'more';
        Suggns.$toggleLink.find('span').text(determiner);
        return false;
    },
    'bindQueryManipulators': function() {
        Suggns.$terms.find('input:checkbox').change(
                Suggns.queryManipulator);
    },
    'queryManipulator': function() {
        var query = Suggns.$queryField.val()
        if(query == Suggns.$queryField[0].title) {
            query = "";
            Suggns.$queryField.removeClass('default-text-active');
        }
        var term = $.trim($(this).parent().find('label').text());

        // Add quotes to terms with whitespace.
        if (term.match(/\s/) !== null) {
            term = "\"" + term + "\"";
        }

        // Remove all instances of term from query.
        var termRegExp = new RegExp(RegExp.escape(term) + "\\s", "gi");
        query = (query+" ").replace(termRegExp, "");
        console.log(query);

        // Append the term if the checkbox is being turned on.
        if ($(this).is(":checked")) {
            // Add a space if query isn't blank.
            if (query.replace(/\s/g, "") != "") query += " ";
            query += term;
        }
        console.log(query);

        queryCleaned = $.trim(query.replace(/\s+/g, " "));
        Suggns.$queryField.val(queryCleaned);
    },
    'checkboxUpdater': function() {
        var query = Suggns.$queryField.val();
        var termDelimiter = RegExp(/\s/);
        var termsLC = query.toLowerCase().split(termDelimiter);
        Suggns.$terms.each(function() {
            var value = "";
            termLC = $(this).find('label').text().toLowerCase();
            if (termsLC.contains(termLC)) {
                value = "checked";
            }
            $(this).find('input:checkbox')
            .attr('checked', value)
            .each(Suggns.checkboxLabelEmphasisToggler);
        });
    },
    'bindCheckboxUpdater': function() {
        Suggns.$queryField.keyup(Suggns.checkboxUpdater);
    },
    'checkboxLabelEmphasisToggler': function() {
        console.log('yeah');
        var isChecked = $(this).is(':checked');
        var method = (isChecked ? "add" : "remove") + "Class";
        $(this).parent().find('label')[method]("on");
    },
    'bindCheckboxLabelEmphasisToggler': function() {
        Suggns.$terms.find('input:checkbox').change(Suggns.checkboxLabelEmphasisToggler);
    }
};
$(Suggns.init);
