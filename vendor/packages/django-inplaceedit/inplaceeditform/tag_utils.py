# Copyright (c) 2010-2013 by Yaco Sistemas <goinnn@gmail.com> or <pmartin@yaco.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this programe.  If not, see <http://www.gnu.org/licenses/>.

from django import template
from django.utils.encoding import smart_str
from django.template.loader import render_to_string


def parse_args_kwargs(parser, token):
    """
    Parse uniformly args and kwargs from a templatetag

    Usage::

      For parsing a template like this:

      {% footag my_contents,height=10,zoom=20 as myvar %}

      You simply do this:

      @register.tag
      def footag(parser, token):
          args, kwargs = parse_args_kwargs(parser, token)
    """
    bits = token.contents.split(' ')

    if len(bits) <= 1:
        raise template.TemplateSyntaxError("'%s' takes at least one argument" % bits[0])

    if token.contents[13] == '"':
        end_quote = token.contents.index('"', 14) + 1
        args = [template.Variable(token.contents[13:end_quote])]
        kwargs_start = end_quote
    else:
        try:
            next_space = token.contents.index(' ', 14)
            kwargs_start = next_space + 1
        except ValueError:
            next_space = None
            kwargs_start = None
        args = [template.Variable(token.contents[13:next_space])]

    kwargs = {}
    kwargs_list = token.contents[kwargs_start:].split(',')
    for kwargs_item in kwargs_list:
        if '=' in kwargs_item:
            k, v = kwargs_item.split('=', 1)
            k = k.strip()
            kwargs[k] = template.Variable(v)
    return args, kwargs


def get_args_and_kwargs(args, kwargs, context):
    out_args = [arg.resolve(context) for arg in args]
    out_kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context)) for k, v in kwargs.items()])
    return out_args, out_kwargs


class RenderWithArgsAndKwargsNode(template.Node):
    """
    Node for templatetags which renders templates with parsed args and kwargs

    Usage::

      class FooNode(RenderWithArgsAndKwargsNode):
          def prepare_context(self, context, args, kwargs):
              context['result_list'] = kwargs['result_list']
              return context

      @register.tag
      def footag(parser, token):
          args, kwargs = parse_args_kwargs(parser, token)
          return FooNode(args, kwargs, template='footag.html')
    """

    def __init__(self, args, kwargs, template):
        self.args = args
        self.kwargs = kwargs
        self.template = template

    def prepare_context(self, args, kwargs, context):
        """
        Hook for overriding in subclasses.

        Note that "args" and "kwargs" parameters are already resolved with context
        """
        return context

    def render(self, context):
        args, kwargs = get_args_and_kwargs(self.args, self.kwargs, context)
        context = self.prepare_context(args, kwargs, context)
        return render_to_string(self.template, context)
