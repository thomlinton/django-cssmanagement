from django.core.management.base import BaseCommand
from blog.util import Stylesheet
import logging
import optparse


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "-l", "--list-packed-css", 
            action="store_true", 
            help="List packed CSS file."
        ),
    )
    
    def handle(self, *args, **options):
        level = {'0': logging.WARN, '1': logging.INFO, '2': logging.DEBUG}[options['verbosity']]
        logging.basicConfig(level=level, format="%(name)s: %(levelname)s: %(message)s")

        if options['list_packed_css']:
            print "Current packed CSS file: ", self.filename
            return 0

        stylesheet = Stylesheet()
        stylesheet.new_production_stylesheet()
        return 0
