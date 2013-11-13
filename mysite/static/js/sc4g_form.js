jQuery(document).ready(function($) {
    'use strict';

    (function() {
        function parseInputFields(formElement) {
            var questions = [];
            var form = $('form.webform-client-form');

            var getValues = function(selector) {
                var valueArray = [];

                $(selector).each(function(index, element) {
                    if ($(element).is('option')) {
                        valueArray.push($(element).text());
                    } else {
                        valueArray.push($(element).next('label').eq(0).text());
                    }
                });

                return valueArray;
            };

            var getSelectValue = function(selector) {
                var valueArray = [];

                var pushValue = function(index, element) {
                    valueArray.push($(this).text());
                };

                if ($(selector).find('option').length > 0 && $(selector).val() !== null) {
                    var values = $(selector).val();
                    for (var i = 0; i < values.length; i++) {
                        $(selector).find('option[value=\'' + values[i] + '\']').each(pushValue);
                    }
                }

                return valueArray;
            };

            var getSelectType = function(selector) {
                if ($(selector).is('[size]') && parseInt($(selector).attr('size')) > 1) {
                    return 'multi';
                }
                return 'single';
            };

            String.prototype.trim = function() {
                return this.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
            };

            var errors = false;
            form.find('div.webform-component').each(function (index, element) {
                var inputType = null;
                var label = $(this).find('label').eq(0).text().trim();
                var requiredLabel = $(this).find('label').eq(0).next('span.form-required');
                var values = [];
                var responses = [];
                var required = (requiredLabel.length) ? true : false;
                var required_filled = false;
                if (label.indexOf('*') > -1) {
                    required = true;
                    label = label.substring(0, label.indexOf('*')).trim();
                }

                var value = null;
                if ($(this).find('input[type=text]').length > 0) {
                    // text or url
                    var text = $(this).find('input[type=text]');
                    if (text !== undefined && text.attr('id').search('url') > 0) {
                        inputType = 'url';
                    } else {
                        inputType = 'text';
                    }
                    value = $(this).find('input[type=text]').val();
                    responses = [ value ];
                    if (required && value.length > 0) { required_filled = true; }
                } else if ($(this).find('input[type=email]').length > 0) {
                    inputType = 'text';
                    value = $(this).find('input[type=email]').val();
                    responses = [ value ];
                    if (required && value.length > 0) { required_filled = true; }
                } else if ($(this).find('input[type=file]').length > 0) {
                    inputType = 'file';
                    value = $(this).find('input[type=file]').val();
                    responses = [ value ];
                    if (required && $(this).find('input[type=file]').val().length > 0) { required_filled = true; }
                } else if ($(this).find('input[type=radio]').length > 0) {
                    inputType = 'single';
                    values = getValues($(this).find('input[type=radio]'));
                    responses = getValues($(this).find('input[type=radio]:checked'));
                    if (required && responses.length > 0) { required_filled = true; }
                } else if ($(this).find('select').length > 0) {
                    var select = $(this).find('select');
                    inputType = getSelectType(select);
                    values = getValues($(this).find('option'));
                    responses = getSelectValue(select);
                    if (required && responses.length > 0) { required_filled = true; }
                } else if ($(this).find('input[type=checkbox]').length > 0) {
                    inputType = 'multi';
                    values = getValues($(this).find('input[type=checkbox]'));
                    responses = getValues($(this).find('input[type=checkbox]:checked'));
                    if (required && responses.length > 0) { required_filled = true; }
                } else if ($(this).find('textarea').length > 0) {
                    inputType = 'textarea';
                    value = $(this).find('textarea').val();
                    responses = [ value ];
                    if (required && value.length > 0) { required_filled = true; }
                }
                if (required && !required_filled) {
                    var errorDiv = document.createElement('div');
                    $(errorDiv).addClass('error').text('This field is required!');
                    if ($(element).find('div.error').length <= 0) {
                        $(element).find('label').first().before(errorDiv);
                    }
                    errors = true;
                    return true;
                } else {
                    var errorElement = $(element).find('div.error');
                    if (errorElement.length > 0) {
                        $(errorElement).remove();
                    }
                }

                if (inputType === null) {
                    return true;
                }

                var question = {
                    inputType: inputType,
                    label: label,
                    values: values,
                    required: required,
                    responses: responses
                };
                questions.push(question);
            });

            if (errors) {
                window.scrollTo(0, 0);

                if ($('#top-error').length <= 0) {
                    var topErrorDiv = document.createElement('div');
                    $(topErrorDiv).addClass('error error-top').attr('id', 'top-error')
                        .text('Please fill out all required fields.');
                    $('form').first().before(topErrorDiv);
                }
                alert('Please fill out all required fields.');
            } else {
                var topError = $('#top-error');
                if (topError.length > 0) {
                    $(topError).remove();
                }

                $.post('http://127.0.0.1:8000/account/signup', { data: JSON.stringify(questions) })
                    .success(function(response) {
                        formElement.attr('data-success', 'true');
                        formElement.submit();
                    }).error(function(response) {
                        alert('There was an error while processing the form.');
                    });
            }
        }

        $('form').attr('data-success', 'false');

        $('form').submit(function(e) {
            var success = $(this).attr('data-success');
            if (success === 'false') {
                e.preventDefault();
                parseInputFields($(this));
            }
        });

    }(jQuery));
});
