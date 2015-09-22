"""
Extension functions for easier form filling.

(This module is a dumping ground for features that may ultimately get
added into the main twill command set.)

Commands:

 * fv_match -- fill in *all* fields that match a regexp (unlike 'formvalue'
        which will complain about multiple matches).  Useful for forms
        with lots of repeated fieldnames -- 'field-1', 'field-2', etc.

 * fv_multi -- fill in multiple form fields at once, e.g.

          fv_multi <formname> field1=value1 field2=value2 field3=value3

 * fv_multi_sub -- same as 'fv_multi', followed by a 'submit'.
        
"""

import twill, twill.utils
import re

__all__ = [ 'fv_match', 'fv_multi_match', 'fv_multi', 'fv_multi_sub' ]

def fv_match(formname, regexp, value):
    """
    >> fv_match <formname> <field regexp> <value>

    Set value of *all* form fields with a name that matches the given
    regular expression.

    (Unlike 'formvalue' or 'fv', this will not complain about multiple
    matches!)
    """
    state = twill.get_browser()
    
    form = state.get_form(formname)
    if not form:
        print 'no such form', formname
        return

    regexp = re.compile(regexp)

    matches = [ ctl for ctl in form.controls if regexp.search(str(ctl.name)) ]

    if matches:
        print '-- matches %d' % (len(matches),)

        n = 0
        for control in matches:
            state.clicked(form, control)
            if control.readonly:
                continue

            n += 1
            twill.utils.set_form_control_value(control, value)

        print 'set %d values total' % (n,)

def fv_multi_match(formname, regexp, *values):
    """
    >> fv_multi_match <formname> <field regexp> <value> [<value> [<value>..]]

    Set value of each consecutive matching form field with the next specified
    value.  If there are no more values, use the last for all remaining form
    fields
    """
    state = twill.get_browser()
    
    form = state.get_form(formname)
    if not form:
        print 'no such form', formname
        return

    regexp = re.compile(regexp)

    matches = [ ctl for ctl in form.controls if regexp.search(str(ctl.name)) ]

    if matches:
        print '-- matches %d, values %d' % (len(matches), len(values))

        n = 0
        for control in matches:
            state.clicked(form, control)
            if control.readonly:
                continue
            try:
                twill.utils.set_form_control_value(control, values[n])
            except IndexError, e:
                twill.utils.set_form_control_value(control, values[-1])
            n += 1

        print 'set %d values total' % (n,)


def fv_multi(formname, *pairs):
    """
    >> fv_multi <formname> [ <pair1> [ <pair2> [ <pair3> ]]]

    Set multiple form fields; each pair should be of the form
    
        fieldname=value

    The pair will be split around the first '=', and
    'fv <formname> fieldname value' will be executed in the order the
    pairs are given.
    """
    from twill import commands

    for p in pairs:
        fieldname, value = p.split('=', 1)
        commands.fv(formname, fieldname, value)

def fv_multi_sub(formname, *pairs):
    """
    >> fv_multi_sub <formname> [ <pair1> [ <pair2> [ <pair3> ]]]

    Set multiple form fields (as with 'fv_multi') and then submit().
    """
    from twill import commands

    for p in pairs:
        fieldname, value = p.split('=', 1)
        commands.fv(formname, fieldname, value)

    commands.submit()
