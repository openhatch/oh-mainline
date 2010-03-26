// requires jQuery and the jQuery Tipsy plugin

$(function () {
    $("[rel='tipsy-north']").tipsy({'gravity': 'n'});
    $("[rel='tipsy-east']").tipsy({'gravity': 'e'});
    $("[rel='tipsy-west']").tipsy({'gravity': 'w'});
    $("[rel='tipsy-south']").tipsy({'gravity': 's'});
});
