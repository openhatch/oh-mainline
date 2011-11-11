import lpconstants as lpc
import utils

from lphelper import LateBindingProperty

class ProjectInfo(object):
    def __init__( self, project_name, project_summary, project_url, project_reviewed, project_registrar, project_date ):
        self.__project_name = project_name
        self.__project_summary = project_summary
        self.__project_url = project_url
        self.__project_license_reviewed = project_reviewed
        self.__project_registar = project_registrar
        self.__project_date = project_date
        
    @property
    def name( self ):
        return self.__project_name
    
    @property
    def summary( self ):
        return self.__project_summary
    
    @property
    def url( self ):
        return self.__project_url
    
    @property
    def registrar( self ):
        return self.__project_registar

    @property 
    def license_reviewed( self ):
        return self.__project_license_reviewed
 
    @property
    def registered( self ):
        return self.__project_date
    
    def __repr__( self ):
        return "<ProjectInfo %s>" %self.name
    
    def __str__( self ):
        return "[Project '%s': %s]" %( self.name, self.registrar or "" )
    
class ProjectPackageInfo( object ):
    def __init__( self, pkg_name, pkg_src_url ):
        self.__pkg_name=pkg_name
        self.__pkg_src_url=pkg_src_url
    
    @property
    def package_name( self ):
        return self.__pkg_name
    
    @property
    def package_url( self ):
        return self.__pkg_src_url
    
    def __repr__( self ):
        return "<ProjectPackageInfo %s>" % self.package_name
    
    def __str__( self ):
        return "[Package '%s': '%s']" % ( self.package_name, self.package_url or "" )
    


class LPProject( object ):
    def __init__( self, url, connection ):
        self.__url = utils.valid_lp_url( url, utils.PROJECT )
        self._connection = connection
        
class LPProjectPackage( object ):
    def __init__( self, url, connection ):
        self.__url = utils.valid_lp_url( url, utils.PROJECT_PACKAGES )
        self._connection = connection   
        
