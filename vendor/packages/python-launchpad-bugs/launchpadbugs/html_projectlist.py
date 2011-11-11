"""TODO:
 * adjustments to url handling"""

import re
import libxml2
import urlparse
from exceptions import parse_error, PythonLaunchpadBugsParsingError
from buglistbase import LPBugList, LPBugPage
from projectbase import LPProject, ProjectInfo, ProjectPackageInfo, LPProjectPackage
from lphelper import user, unicode_for_libxml2
from utils import valid_lp_url
from lpconstants import BASEURL

#deactivate error messages from the validation [libxml2.htmlParseDoc]
def noerr( ctx, str ):
    pass

libxml2.registerErrorHandler( noerr, None )

class PInfo( ProjectInfo ):
    def __init__( self, project_name, project_summary, project_url, project_reviewed, project_registrar, project_registered ):
        project_url = valid_lp_url(project_url, BASEURL.PROJECTLIST)
        ProjectInfo.__init__( self, project_name, project_summary, project_url, project_reviewed, project_registrar, project_registered )

class PKGInfo ( ProjectPackageInfo ):
    def __init__( self, package_name, package_url ):
        package_url = valid_lp_url(package_url, BASEURL.PROJECTLIST)
        ProjectPackageInfo.__init__( self, package_name, package_url )
        
class ProjectPackagePage( LPBugPage ):
    
    @staticmethod
    def find_parse_function( connection, url, all_tasks ):
        url = valid_lp_url(url, BASEURL.BUGPAGE)
        lp_content = connection.get( url )
        xmldoc = libxml2.htmlParseDoc( unicode_for_libxml2( lp_content.text ), "UTF-8" )
        u=urlparse.urlsplit( url )
        if "+allpackages" in u[2]:
            result = ProjectPackagePage.parse_html_project_package_list( xmldoc, all_tasks, url )
        else:
            raise PythonLaunchpadBugsParsingError("package_table", url)
        return result
    
    @staticmethod
    def parse_html_project_package_list( xmldoc, all_tasks, url ):
        def _parse():
            if not xmldoc.xpathEval( "//h1" ):
                xmldoc.freeDoc()
                return
            packagelisting=xmldoc.xpathEval( "//p/a" )
            for package in packagelisting:
                package_name=package.content
                package_url="http://launchpad.net" + package.prop( "href" )
                yield PKGInfo( package_name, package_url )
                
        next = xmldoc.xpathEval( '//td[@class="batch-navigation-links"]//a[@rel="next"]//@href' )
        m = xmldoc.xpathEval( '//td[@class="batch-navigation-index"]' )
        if m:
            m = m.pop()
            n = re.search( r'(\d+)\s+results?', m.content )
            parse_error( n, "ProjectPage.parse_html_project_package_list.length", url=url )
            length = n.group( 1 )
            n = m.xpathEval( "strong" )
            batchsize = int( n[1].content ) - int( n[0].content ) + 1
        else:
            length = batchsize = 0
        if next:
            return _parse(), next[0].content, batchsize, int( length )
        return _parse(), False, batchsize, int( length )
        
class ProjectPage( LPBugPage ):
    
    @staticmethod
    def find_parse_function( connection, url, all_tasks ):
        url = valid_lp_url(url, BASEURL.BUGPAGE)
        lp_content = connection.get( url )
        xmldoc = libxml2.htmlParseDoc( unicode_for_libxml2( lp_content.text ), "UTF-8" )
        u = urlparse.urlsplit( url )
        if "projects/+all" in u[2]:
            result = ProjectPage.parse_html_project_list( xmldoc, all_tasks, url )
        return result

    @staticmethod
    def parse_html_project_list( xmldoc, all_tasks, url ):
        getuser_regexp=re.compile( r"~(.*)" )
        def _parse():
            if not xmldoc.xpathEval( '//div[@id="product-listing"]' ):
                xmldoc.freeDoc()
                return
            projectlisting=xmldoc.xpathEval( '//div[@id="product-listing"]/div' )
            for projects in projectlisting:
                # Catch Project URL:
                m=projects.xpathEval( 'a[1]' )
                if m:
                    url="http://launchpad.net%s" % m[0].prop( "href" )
                    reviewed=True
                else:
                    # fetch projects which are not reviewed yet
                    m = projects.xpathEval( 'span[@title]/a[1]' )
                    url = "http://launchpad.net%s" % m[0].prop( "href" )
                    reviewed = False
                # Project name:
                project_name = m[0].prop( "href" )[1:]
                # Catch summary
                m=projects.xpathEval( 'div[@style]/div[1]' )
                summary = m[0].content
                # catch username
                m = projects.xpathEval( 'div[@style]/div[2]/a[1]' )
                username = user.parse_html_user( m[0] )
                # catch registered date
                m = projects.xpathEval( 'div[@style]/div[2]/span[1]' )
                registered = m[0].prop( "title" )
                yield PInfo( project_name, summary, url, reviewed, username, registered )
                
        # batch_size=xmldoc.xpathEval('//td[@class="batch-navigation-index"]/strong[2]')
        #length=batchsize=batch_size[0].content
        next = xmldoc.xpathEval( '//td[@class="batch-navigation-links"]//a[@rel="next"]//@href' )
        m = xmldoc.xpathEval( '//td[@class="batch-navigation-index"]' )
        if m:
            m = m.pop()
            n = re.search( r'(\d+)\s+results?', m.content )
            parse_error( n, "ProjectPage.parse_html_project_list.length", url=url )
            length = n.group( 1 )
            n = m.xpathEval( "strong" )
            batchsize = int( n[1].content ) - int( n[0].content ) + 1
        else:
            length = batchsize = 0
        if next:
            return _parse(), next[0].content, batchsize, int( length )
        return _parse(), False, batchsize, int( length )

                
class ProjectList( LPBugList ):
    """
    returns a SET of LPBugInfo objects
    searches baseurl and its following pages
    """
    def __init__( self, baseurl, connection=None, all_tasks=False, progress_hook=None ):
        if hasattr(baseurl, "baseurl"):
            baseurl.baseurl = valid_lp_url(baseurl.baseurl, BASEURL.PROJECTLIST)
        else:
            baseurl = valid_lp_url(baseurl, BASEURL.PROJECTLIST)
        LPBugList.__init__( self, baseurl, connection, all_tasks,
                    ProjectPage, progress_hook )
        
    def __repr__( self ):
        return "<Projectlist %s>" %self.baseurl.split( "?" )[0]
        
    def __str__( self ):
        return "Projectlist([%s])" %",".join( repr( i ) for i in self )
        
    def add( self, item ):
        assert isinstance( item, ( ProjectInfo, LPProject ) )
        LPBugList.add( self, item )
        
class ProjectPackageList(LPBugList):
    def __init__(self,baseurl,connection=None,all_tasks=False,progress_hook=None):
        LPBugList.__init__(self,baseurl,connection,all_tasks, ProjectPackagePage, progress_hook)
        
    def __repr__(self):
        return "<ProjectPackageList %s>" % self.baseurl.split("?")[0]
    
    def add(self,item):
        assert isinstance(item,(ProjectPackageInfo, LPProjectPackage))
        LPBugList.add(self,item)
    
    def __str__( self ):
        return "ProjectPackageList([%s])" % ",".join( repr( i ) for i in self )
