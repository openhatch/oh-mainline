$(document).ready(function () {
		$text_inputs = $('input[type="text"], textarea');
		$text_inputs.focus(function () { $(this).addClass('focus'); });
		$text_inputs.blur(function() { $(this).removeClass('focus'); });
		});
