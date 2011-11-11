from datetime import datetime
from time import strptime
from email import Utils

class LPTime(datetime):
    
    @staticmethod
    def convert_rfc2822_time(time_str):
        """ converts a time-string used in /+text into a time-tuple
        time_str: like 'Tue, 27 Nov 2007 11:15:12 -0000'
        returns: time tuple
        """
        return Utils.parsedate(time_str)[0:6]
    
    @staticmethod
    def convert_text_time(time_str):
        """ converts a time-string used in /+text into a time-tuple
        time_str: like 'Tue, 27 Nov 2007 11:15:12 -0000'
        returns: time tuple
        """
        return strptime(time_str, "%a, %d %b %Y %H:%M:%S -0000")[0:6]
        
    @staticmethod
    def convert_html_time(time_str):
        """ converts a time-string used in html-page into a time-tuple
        time_str: like '2007-11-27 11:15:12 UTC'
        returns: time tuple
        """
        return strptime(time_str, "%Y-%m-%d %H:%M:%S %Z")[0:6]
        
    @staticmethod
    def convert_activity_time(time_str):
        """ converts a time-string used in activity-log-html-page into a time-tuple
        time_str: like '28 Nov 07 20:10'
        returns: time tuple
        """
        return strptime(time_str, "%d %b %y %H:%M")[0:6]
        
    @staticmethod
    def convert_lastcomment_time(time_str):
        """ converts a time-string used in lastzcomment-function into a time-tuple
        time_str: like '2007-12-24'
        returns: time tuple
        """
        return strptime(time_str, "%Y-%m-%d")[0:3]

        
    def __new__(cls, time_str):
        t = None
        conv_functions = (  LPTime.convert_rfc2822_time, LPTime.convert_text_time,
                            LPTime.convert_html_time, LPTime.convert_activity_time,
                            LPTime.convert_lastcomment_time)
        for i in conv_functions:
            try:
                t = i(time_str)
                if t[0] < 1900:
                    continue
                break
            except (ValueError, TypeError):
                continue
        else:
            # there seems to be a problem when parsing timezones
            # in .convert_html_time(), work around this:
            x = time_str.split()
            if x[-1].isalpha():
                try:
                    x[-1] = "UTC"
                    t = LPTime.convert_html_time(" ".join(x))
                    if t[0] < 1900:
                        t = None
                except (ValueError, TypeError):
                    pass
        if not t:
            raise ValueError, "Unknown date format (%s)" %time_str
        obj = super(LPTime, cls).__new__(LPTime, *t)
        # Workaround to fix issue with GUI frameworks
        if obj.year < 1900:
            if obj.year < 50:
                obj = obj.replace(year=obj.year + 2000)
            else:
                obj = obj.replace(year=obj.year + 1900)
        return obj
        
    def __str__(self):
        return self.strftime("%Y-%m-%d %H:%M:%S UTC")
