$(document).ready(function() {
    $('a.collapse-button').click(function(e) {
        e.preventDefault();

        var div = $(this).parent().next();
        var display = div.css('display');
        var text = $(this).text();
        var newDisplay = (display == 'none') ? 'block' : 'none';
        var newText = (text == '-') ? '+' : '-';

        div.css('display', newDisplay);
        $(this).text(newText);
    });

    function toggleCollapseAll(collapse) {
        var display = (collapse === true) ? 'none' : 'block';
        var text = (collapse === true) ? '+' : '-';

        $('ul.list-hidden').css('display', display);
        $('a.collapse-button').text(text);
    }

    $('#collapseAllButton').click(function(e) {
        e.preventDefault();
        toggleCollapseAll(true);
    });

    $('#expandAllButton').click(function(e) {
        e.preventDefault();
        toggleCollapseAll(false);
    });

    $('#resetButton').click(function (e) {
        e.preventDefault();

        $('#filter_name').val('');
        $('#filter_company_name').val('');
        $('#filter_email').val('');
        $('#filter_language').val('');
        $('ul.list-hidden input[type="checkbox"][name="skills"]').prop('checked', false);
        $('ul.list-hidden input[type="checkbox"][name="organizations"]').prop('checked', false);
        $('ul.list-hidden input[type="checkbox"][name="causes"]').prop('checked', false);
        $('ul.list-hidden input[type="checkbox"][name="languages"]').prop('checked', false);
        $('ul.list-hidden input[type="checkbox"][name="duration"]').prop('checked', false);
        $('ul.list-hidden input[type="radio"][name="time_to_commit"]').prop('checked', false);
        $('ul.list-hidden input[type="radio"][name="opensource"]').prop('checked', false);
    });
});
