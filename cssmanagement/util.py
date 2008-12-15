from django.conf import settings
from django.template.loader import render_to_string
import logging, datetime, time
import optparse, os


CSS_VERSION_FILE = '.css_version'
CSS_MODIFICATION_FILE = '.css_modification'
CSS_PATH = '/'.join([settings.MEDIA_ROOT,'css'])
CSS_LINK = '<link rel="stylesheet" type="text/css" href="%s">'

class Pack(object):
    def pack(data):
        raise NotImplementedError()

class NaivePack(Pack):
    def __init__(self,replace_chars=['\n','\t','\r']):
        self.replace_chars = replace_chars
    def pack(self,data):
        for rchar in self.replace_chars:
            data = data.replace(rchar,'')
        return data

class Stylesheet(object):

    def get_version(cls,date_only=False,int_only=False):
        version_date = datetime.datetime.strftime( datetime.datetime.now(), "%Y%m%d" )
        version_int = 0
        version = "%s_%d"%(version_date,int(version_int))

        try:
            version_file = open('/'.join([CSS_PATH,CSS_VERSION_FILE]),'r')
            version_date = version_file.readline().strip(' \n')
            version_int = version_file.readline().strip(' \n')
            version = "%s_%d"%(version_date,int(version_int))
            version_file.close()
        except IOError:
            logging.debug("Generating new version information")

        if int_only:
            return int(version_int)
        elif date_only:
            return version_date
        return version

    get_version = classmethod(get_version)

    def inc_version(cls):
        version_date = cls.get_version(date_only=True)
        version_int = cls.get_version(int_only=True)+1

        try:
            version_file = open('/'.join([CSS_PATH,CSS_VERSION_FILE]),'w')        
            version_file.write("%s\n"%version_date)
            version_file.write("%d\n"%version_int)
        except IOError, e:
            logging.error("Could not increment version: %s"%str(e))
        finally:
            version_file.close()

    inc_version = classmethod(inc_version)

    def _get_filename(cls):
        return '.'.join(['/'.join([CSS_PATH,cls.get_version()]),'css'])

    get_filename = classmethod(_get_filename)

    def get_unmanaged_stylesheets(cls):
        unmanaged_stylesheets = list()
        cur_filename = Stylesheet.get_filename()

        for root, dirs, files in os.walk(CSS_PATH):
            # NOTE: hackish
            if '.svn' in dirs: 
                dirs.remove('.svn')
            for asset in files:
                if asset.endswith('.css') and not cur_filename.endswith(asset):
                    unmanaged_stylesheets.append(asset)

    def get_stylesheet_list(cls,rendered):
        stylesheets = ""
        files = None
        root_path = '/'.join([settings.MEDIA_URL,'css'])
        
        # collect dependencies and compile complete/absolute paths
        if hasattr(settings,'CSS_MANAGED_FILES'):
            files = settings.CSS_MANAGED_FILES
        else:
            files = Stylesheet.get_unmanaged_stylesheets()

        translated_files = []
        for file in files:
            translated_files.append( '/'.join([root_path,file]) )

        # if requested, return only paths
        if not rendered:
            return translated_files

        for path in translated_files:
            stylesheets = "%s\n%s" % \
                (stylesheets,render_to_string('cssmanagement/link.html',{'src':path}))
        return stylesheets

    get_stylesheet_list = classmethod(get_stylesheet_list)

    def get_production_stylesheet(cls,rendered):
        src = '.'.join(["/".join([settings.MEDIA_URL,'css',cls.get_version()]),'css'])
        if not rendered:
            return src
        return render_to_string('cssmanagement/link.html',{'src':src})

    get_production_stylesheet = classmethod(get_production_stylesheet)

    def _get_last_modification(cls):
        last_modified_str = ''
        try:
            last_modified_str = open('/'.join([CSS_PATH,CSS_MODIFICATION_FILE]),'r').read()
        except IOError:
            pass

        if last_modified_str: return float(last_modified_str)
        else:                 return 0.0

    get_last_modification = classmethod(_get_last_modification)

    def _set_last_modification(cls,last_modified):
        mod_file = open('/'.join([CSS_PATH,CSS_MODIFICATION_FILE]),'w')
        mod_file.write(str(last_modified))
        mod_file.close()

    #last_modified = property(_get_last_modification,_set_last_modification)
    set_last_modification = classmethod(_set_last_modification)

    def remove_old_stylesheet(self):
        cur_filename = Stylesheet.get_filename()
        if cur_filename:
            os.remove(cur_filename)

    def stylesheets_modified(self):
        last_modified = Stylesheet.get_last_modification()
        cur_filename = Stylesheet.get_filename()

        if hasattr(settings,'CSS_MANAGED_FILES'):
            logging.info("Using explicit stylesheet list in settings.CSS_MANAGED_FILES")
            for asset in settings.CSS_MANAGED_FILES:
                if asset.endswith('.css'):
                    stat = os.stat('/'.join([CSS_PATH,asset]))
                    # NOTE: found in practice we need a little
                    #       fudge factor ... :/
                    if stat.st_mtime > last_modified+1:
                        last_modified = stat.st_mtime
        else:
            for root, dirs, files in os.walk(CSS_PATH):
                # NOTE: hackish
                if '.svn' in dirs: 
                    dirs.remove('.svn')
                for asset in files:
                    if asset.endswith('.css') and not cur_filename.endswith(asset):
                        stat = os.stat('/'.join([root,asset]))
                        # NOTE: found in practice we need a little
                        #       fudge factor ... :/
                        if stat.st_mtime > last_modified+1:
                            last_modified = stat.st_mtime

        if last_modified > Stylesheet.get_last_modification():
            Stylesheet.set_last_modification(last_modified)
            return True
        return False

    def get_packed_content( self, old_data, new_data, file=None ):
        # TOOD: add customizable packing algorithms via project settings
        new_data_packed = NaivePack().pack(new_data)
        if file:
            logging.info( "Compressed %s by a factor of %s%%" % (file,str(100*(len(new_data_packed)/float(len(new_data))))) )
        return ''.join([old_data,new_data_packed])

    def new_production_stylesheet(self):
        """
        A naive algorithm that collects all stylesheets either specified in ``settings.CSS_MANAGED_FILES``
        or under those stylesheets found under ``MEDIA_ROOT/css`` and packs them into a single file.

        """

        if self.stylesheets_modified():
            if Stylesheet.get_version(int_only=True) > 0:
                self.remove_old_stylesheet()
            Stylesheet.inc_version()

            css_prod_content = ""
            if hasattr(settings,'CSS_MANAGED_FILES'):
                for asset in settings.CSS_MANAGED_FILES:
                    asset_file = open('/'.join([CSS_PATH,asset]))
                    css_prod_content = self.get_packed_content(css_prod_content,asset_file.read(),asset)
                    asset_file.close()
            else:
                for root, dirs, files in os.walk(CSS_PATH):
                    for asset in files:
                        if asset.endswith('.css'):
                            asset_file = open('/'.join([root,asset]))
                            css_prod_content = self.get_packed_content(css_prod_content,asset_file.read(),asset)
                            asset_file.close()

            css_prod_file = open(Stylesheet.get_filename(),'w')
            css_prod_file.write(css_prod_content)
            css_prod_file.close()

            logging.info( "Wrote out packed stylesheet: %s", Stylesheet.get_filename() )
            return True

        logging.info( "No changed detected. Exiting." )
        return False

    def render(cls,render_html=True):
        if not settings.DEBUG:
            return cls.get_production_stylesheet(render_html)
        else:
            return cls.get_stylesheet_list(render_html)

    render = classmethod(render)
