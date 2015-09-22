function DateTimeShortcutsInitial() {
    var datetime_load = false;
    var calendar_load = false;
    var gettext_load = false;
    var admin_prefix_load = false;
    try{
        if(DateTimeShortcuts != null)
            datetime_load = true;
        if(gettext != null)
            gettext_load = true;
        if(CalendarNamespace)
            calendar_load = true;
        if(window.__admin_media_prefix__)
            admin_prefix_load = true;
    }
    catch(err) {
    }
    if (datetime_load && calendar_load && gettext_load && admin_prefix_load){
        DateTimeShortcuts.init();
        addEvent = function(num) {
        };
    }
    else {
        setTimeout(DateTimeShortcutsInitial, 500);
    }
}
DateTimeShortcutsInitial();
