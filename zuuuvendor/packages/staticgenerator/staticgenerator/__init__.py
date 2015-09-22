#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""Static file generator for Django."""
import stat

from django.utils.functional import Promise

from filesystem import FileSystem
from handlers import DummyHandler


class StaticGeneratorException(Exception):
    pass

class StaticGenerator(object):
    """
    The StaticGenerator class is created for Django applications, like a blog,
    that are not updated per request.

    Usage is simple::

        from staticgenerator import quick_publish
        quick_publish('/', Post.objects.live(), FlatPage)

    The class accepts a list of 'resources' which can be any of the 
    following: URL path (string), Model (class or instance), Manager, or 
    QuerySet.

    As of v1.1, StaticGenerator includes file and path deletion::

        from staticgenerator import quick_delete
        quick_delete('/page-to-delete/')

    The most effective usage is to associate a StaticGenerator with a model's
    post_save and post_delete signal.

    The reason for having all the optional parameters is to reduce coupling
    with django in order for more effectively unit testing.
    """

    def __init__(self, *resources, **kw):
        self.parse_dependencies(kw)

        self.resources = self.extract_resources(resources)
        self.server_name = self.get_server_name()

        try:
            self.web_root = getattr(self.settings, 'WEB_ROOT')
        except AttributeError:
            raise StaticGeneratorException('You must specify WEB_ROOT in settings.py')

    def parse_dependencies(self, kw):
        http_request = kw.get('http_request', None)
        model_base = kw.get('model_base', None)
        manager = kw.get('manager', None)
        model = kw.get('model', None)
        queryset = kw.get('queryset', None)
        settings = kw.get('settings', None)
        site = kw.get('site', None)
        fs = kw.get('fs', None)
        
        self.http_request = http_request
        if not http_request:
            from django.http import HttpRequest
            self.http_request = HttpRequest

        self.model_base = model_base
        if not model_base:
            from django.db.models.base import ModelBase
            self.model_base = ModelBase

        self.manager = manager
        if not manager:
            from django.db.models.manager import Manager
            self.manager = Manager

        self.model = model
        if not model:
            from django.db.models import Model
            self.model = Model

        self.queryset = queryset
        if not queryset:
            from django.db.models.query import QuerySet
            self.queryset = QuerySet

        self.settings = settings
        if not settings:
            from django.conf import settings
            self.settings = settings

        self.fs = fs
        if not fs:
            self.fs = FileSystem()

        self.site = site

    def extract_resources(self, resources):
        """Takes a list of resources, and gets paths by type"""
        extracted = []

        for resource in resources:

            # A URL string
            if isinstance(resource, (str, unicode, Promise)):
                extracted.append(str(resource))
                continue

            # A model instance; requires get_absolute_url method
            if isinstance(resource, self.model):
                extracted.append(resource.get_absolute_url())
                continue

            # If it's a Model, we get the base Manager
            if isinstance(resource, self.model_base):
                resource = resource._default_manager

            # If it's a Manager, we get the QuerySet
            if isinstance(resource, self.manager):
                resource = resource.all()

            # Append all paths from obj.get_absolute_url() to list
            if isinstance(resource, self.queryset):
                extracted += [obj.get_absolute_url() for obj in resource]

        return extracted

    def get_server_name(self):
        '''Tries to get the server name.
        First we look in the django settings.
        If it's not found we try to get it from the current Site.
        Otherwise, return "localhost".
        '''
        try:
            return getattr(self.settings, 'SERVER_NAME')
        except:
            pass

        try:
            if not self.site:
                from django.contrib.sites.models import Site
                self.site = Site
            return self.site.objects.get_current().domain
        except:
            print '*** Warning ***: Using "localhost" for domain name. Use django.contrib.sites or set settings.SERVER_NAME to disable this warning.'
            return 'localhost'

    def get_content_from_path(self, path):
        """
        Imitates a basic http request using DummyHandler to retrieve
        resulting output (HTML, XML, whatever)
        """

        request = self.http_request()
        request.path_info = path
        request.META.setdefault('SERVER_PORT', 80)
        request.META.setdefault('SERVER_NAME', self.server_name)

        handler = DummyHandler()
        try:
            response = handler(request)
        except Exception, err:
            raise StaticGeneratorException("The requested page(\"%s\") raised an exception. Static Generation failed. Error: %s" % (path, str(err)))

        if int(response.status_code) != 200:
            raise StaticGeneratorException("The requested page(\"%s\") returned http code %d. Static Generation failed." % (path, int(response.status_code)))

        return response.content

    def get_filename_from_path(self, path):
        """
        Returns (filename, directory)
        Creates index.html for path if necessary
        """
        if path.endswith('/'):
            path = '%sindex.html' % path

        filename = self.fs.join(self.web_root, path.lstrip('/')).encode('utf-8')
        return filename, self.fs.dirname(filename)

    def publish_from_path(self, path, content=None):
        """
        Gets filename and content for a path, attempts to create directory if 
        necessary, writes to file.
        """
        filename, directory = self.get_filename_from_path(path)
        if not content:
            content = self.get_content_from_path(path)

        if not self.fs.exists(directory):
            try:
                self.fs.makedirs(directory)
            except:
                raise StaticGeneratorException('Could not create the directory: %s' % directory)

        try:
            f, tmpname = self.fs.tempfile(directory=directory)
            self.fs.write(f, content)
            self.fs.close(f)
            self.fs.chmod(tmpname, stat.S_IREAD | stat.S_IWRITE | stat.S_IWUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            self.fs.rename(tmpname, filename)
        except:
            raise StaticGeneratorException('Could not create the file: %s' % filename)

    def delete_from_path(self, path):
        """Deletes file, attempts to delete directory"""
        filename, directory = self.get_filename_from_path(path)
        try:
            if self.fs.exists(filename):
                self.fs.remove(filename)
        except:
            raise StaticGeneratorException('Could not delete file: %s' % filename)

        try:
            self.fs.rmdir(directory)
        except OSError:
            # Will fail if a directory is not empty, in which case we don't 
            # want to delete it anyway
            pass

    def do_all(self, func):
        return [func(path) for path in self.resources]

    def delete(self):
        return self.do_all(self.delete_from_path)

    def publish(self):
        return self.do_all(self.publish_from_path)

def quick_publish(*resources):
    return StaticGenerator(*resources).publish()

def quick_delete(*resources):
    return StaticGenerator(*resources).delete()
