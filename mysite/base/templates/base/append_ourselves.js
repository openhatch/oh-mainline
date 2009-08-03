var in_string = {{ in_string|safe }};

var thisScript = /openhatch-widget.js/;
var theScripts = document.getElementsByTagName('SCRIPT');
for (var i = 0 ; i < theScripts.length; i++) {
    if(theScripts[i].src.match(thisScript)) {
        var inForm = false;
        var currentNode = theScripts[i].parentNode;
        while (currentNode != null) {
            if (currentNode.nodeType == 1) {
                if (currentNode.tagName.toLowerCase() == 'form') {
                    inForm = true;
                    break;
                }
            }
            /* always */
            currentNode = currentNode.parentNode;
        }
        
        if (inForm) {
            /* if we are inside a form, we do not want to create
               another form tag. So replace our FORM tag with
               a DIV.
            */
            in_string = in_string.replace('<form ', '<div ');
            in_string = in_string.replace('</form>', '</div>');
        }
        var my_div = document.createElement('DIV');
        my_div.innerHTML = in_string;

        theScripts[i].parentNode.insertBefore(my_div, theScripts[i]);
        theScripts[i].parentNode.removeChild(theScripts[i]);
        break;
    }
}
