"""
Scrapy Shell

See documentation in docs/topics/shell.rst
"""

from scrapy.command import ScrapyCommand
from scrapy.shell import Shell
from scrapy import log

class Command(ScrapyCommand):

    requires_project = False
    default_settings = {'KEEP_ALIVE': True, 'LOGSTATS_INTERVAL': 0}

    def syntax(self):
        return "[url|file]"

    def short_desc(self):
        return "Interactive scraping console"

    def long_desc(self):
        return "Interactive console for scraping the given url"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_option("-c", dest="code",
            help="evaluate the code in the shell, print the result and exit")

    def update_vars(self, vars):
        """You can use this function to update the Scrapy objects that will be
        available in the shell
        """
        pass

    def run(self, args, opts):
        url = args[0] if args else None
        shell = Shell(self.crawler, update_vars=self.update_vars, inthread=True, \
            code=opts.code)
        def err(f):
            log.err(f, "Shell error")
            self.exitcode = 1
        d = shell.start(url=url)
        d.addErrback(err)
        d.addBoth(lambda _: self.crawler.stop())
        self.crawler.start()
