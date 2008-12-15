from django.core.management.base import BaseCommand
from cssmanagement.util import Stylesheet
import logging
import optparse


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        optparse.make_option(
            "-l", "--list-packed-css", 
            action="store_true", 
            help="List packed CSS file."
        ),
        optparse.make_option(
            "-g", "--generate-packed-css", 
            action="store_true", 
            help="Generate packed CSS file."
        ),
    )
    
    def handle(self, *args, **options):
        level = {'0': logging.WARN, '1': logging.INFO, '2': logging.DEBUG}[options['verbosity']]
        logging.basicConfig(level=level, format="%(name)s: %(levelname)s: %(message)s")

        stylesheet = Stylesheet()

        if options['generate_packed_css']:
            stylesheet.new_production_stylesheet()
        if options['list_packed_css']:
            print "Current packed CSS file: ", stylesheet.get_filename()

        return 0
