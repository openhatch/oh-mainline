var css_tag = document.createElement('style');
css_tag.type = 'text/css';
var text = document.createTextNode("@import url('/static/css/only-if-javascript.css') all;");
css_tag.appendChild(text);
document.getElementsByTagName('head')[0].appendChild(css_tag);
