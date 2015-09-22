function add_style_element(relative_ref) {
  var head = document.getElementsByTagName("head")[0];
  var css = document.createElement("link");
  css.type = "text/css";
  css.rel = "stylesheet";
  css.href = relative_ref;
  css.media = "screen";
  head.appendChild(css);
}
/* enable max-width workaround */
add_style_element("/styles/maxwidth.css");
