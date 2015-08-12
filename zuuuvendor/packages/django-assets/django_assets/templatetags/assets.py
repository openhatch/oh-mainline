import tokenize

from django import template
from django_assets.conf import settings
from django_assets.merge import process
from django_assets.bundle import Bundle
from django_assets import registry


class AssetsNode(template.Node):
    def __init__(self, filter, output, files, childnodes):
        self.childnodes = childnodes
        self.output = output
        self.files = files
        self.filter = filter

    def resolve(self, context={}):
        """We allow variables to be used for all arguments; this function
        resolves all data against a given context;

        This is a separate method as the management command must have
        the ability to check if the tag can be resolved without a context.
        """
        def resolve_var(x):
            if x is None:
                return None
            else:
                try:
                    return template.Variable(x).resolve(context)
                except template.VariableDoesNotExist, e:
                    # Django seems to hide those; we don't want to expose
                    # them either, I guess.
                    raise
        def resolve_bundle(x):
            bundle = registry.get(x)
            if bundle:
                return bundle
            return x

        registry.autoload()
        return Bundle(*[resolve_bundle(resolve_var(f)) for f in self.files],
                      **{'output': resolve_var(self.output),
                         'filters': resolve_var(self.filter)})

    def render(self, context):
        bundle = self.resolve(context)

        result = u""
        for url in process(bundle):
            context.update({'ASSET_URL': url})
            try:
                result += self.childnodes.render(context)
            finally:
                context.pop()
        return result


def assets(parser, token):
    filter = None
    output = None
    files = []

    # parse the arguments
    args = token.split_contents()[1:]
    for arg in args:
        # Handle separating comma; for backwards-compatibility
        # reasons, this is currently optional, but is enforced by
        # the Jinja extension already.
        if arg[-1] == ',':
            arg = arg[:-1]
            if not arg:
                continue

        # determine if keyword or positional argument
        arg = arg.split('=', 1)
        if len(arg) == 1:
            name = None
            value = arg[0]
        else:
            name, value = arg

        # handle known keyword arguments
        if name == 'output':
            output = value
        elif name == 'filter':
            filter = value
        # positional arguments are source files
        elif name is None:
            files.append(value)
        else:
            raise template.TemplateSyntaxError('Unsupported keyword argument "%s"'%name)

    # capture until closing tag
    childnodes = parser.parse(("endassets",))
    parser.delete_first_token()
    return AssetsNode(filter, output, files, childnodes)



# if Coffin is installed, expose the Jinja2 extension
try:
    from coffin.template import Library as CoffinLibrary
except ImportError:
    register = template.Library()
else:
    register = CoffinLibrary()
    from django_assets.jinja2.extension import AssetsExtension
    register.tag(AssetsExtension)

# expose the default Django tag
register.tag('assets', assets)