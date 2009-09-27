$.fn.hoverClass = function(c) {
        return this.each(function(){
            $(this).hover( 
                function() { $(this).addClass(c); },
                function() { $(this).removeClass(c); }
            );
        });
    };

Portfolio = {};

Portfolio.initialize = function() {
    console.log('Portfolio.initialize');
    $('.project-escutcheon').hoverClass('hover');
};

$(Portfolio.initialize);
