$.fn.hoverClass = function(c) {
        return this.each(function(){
            $(this).hover( 
                function() { $(this).addClass(c); },
                function() { $(this).removeClass(c); }
            );
        });
    };

Portfolio = {};

Portfolio.editCallback = function(value, settings) {
  data = {};
  data[this.id] = value;
  $.post('/people/info/edit/do', data);
  return value;
};

Portfolio.initialize = function() {
    console.log('Portfolio.initialize');
    $('.project-escutcheon').hoverClass('hover');
    $('.editable').editable(Portfolio.editCallback,
      {'type': 'text',
       'submit': 'OK',
       'indicator': 'Saving...',
       'tooltip': 'Click to edit',
       'placeholder': 'Click to edit',
       'onblue': 'submit'});
    
};

$(Portfolio.initialize);
