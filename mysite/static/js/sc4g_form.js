jQuery(document).ready(function($) {
    'use strict';

    (function() {
        function parseInputFields() {
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

            var getResponses = function(selector) {
                var responses = [];



                return responses;
            };

            String.prototype.trim = function() {
                return this.replace(/^\s\s*/, '').replace(/\s\s*$/, '');
            };

            form.find('div.webform-component').each(function (index, element) {
                var inputType = null;
                var label = $(this).find('label').eq(0).text().trim();
                var requiredLabel = $(this).find('label').eq(0).next('span.form-required');
                var values = [];
                var responses = [];
                var required = (requiredLabel.length) ? true : false;
                if (label.indexOf('*') > -1) {
                    required = true;
                    label = label.substring(0, label.indexOf('*')).trim();
                }

                if ($(this).find('input[type=text]').length > 0) {
                    // text or url
                    var text = $(this).find('input[type=text]');
                    if (text !== undefined && text.attr('id').search('url') > 0) {
                        inputType = 'url';
                    } else {
                        inputType = 'text';
                    }
                    responses = [ $(this).find('input[type=text]').val() ];
                } else if ($(this).find('input[type=email]').length > 0) {
                    inputType = 'text';
                    responses = [ $(this).find('input[type=email]').val() ];
                } else if ($(this).find('input[type=file]').length > 0) {
                    inputType = 'file';
                } else if ($(this).find('input[type=radio]').length > 0) {
                    inputType = 'single';
                    values = getValues($(this).find('input[type=radio]'));
                    responses = getResponses($(this).find('input[type=radio]'));
                } else if ($(this).find('input[type=checkbox]').length > 0 ||
                        $(this).find('select').length > 0) {
                    inputType = 'multi';
                    values = getValues($(this).find('input[type=checkbox], option'));
                    responses = getResponses($(this).find('input[type=checkbox], option'));
                } else if ($(this).find('textarea').length > 0) {
                    inputType = 'textarea';
                    responses = [ $(this).find('textarea').val() ];
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

            console.log(questions);

            $.post('http://127.0.0.1:8000/account/signup', { data: JSON.stringify(questions) })
                .success(function(response) {
                    //submit form
                }).error(function(response) {

                });
        }

        $('form').submit(function(e) {
            e.preventDefault();
            parseInputFields();
        });

    }(jQuery));
});
