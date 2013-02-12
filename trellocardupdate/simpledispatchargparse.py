import argparse
import inspect
import sys
from functools import partial

class ParserWithSimpleDispatch(argparse.ArgumentParser):
    """Parses and dispatches mutually exclusive command line functions before normal parsing

    Used to add a set of mutually exclusive command line options to argparse,
    with normal parsing only proceeding if none of these mutually exclusive flags appear.
    The functions must take 1 or 0 arguments.
    If one of these is dispatched, Python will exit after this command runs.
    """
    def __init__(self, *args, **kwargs):
        self.simple_functions_by_flag = {}
        super(ParserWithSimpleDispatch, self).__init__(*args, **kwargs)
        self.simple_parser = argparse.ArgumentParser()
        self.simple_group = self.simple_parser.add_mutually_exclusive_group()
        self.doc_group = self.add_argument_group("special options", "mutually exclusive (with each other and normal args) special options")

    def dispatch_if_known(self, args):
        if not (set(self.simple_functions_by_flag) & set(args)):
            return
        parsed_args = self.simple_parser.parse_args(args)
        for func_flag, func in self.simple_functions_by_flag.iteritems():
            value = getattr(parsed_args, func.func_name)
            if value is not None:
                if len(inspect.getargspec(func).args) == 1:
                    func(value)
                else:
                    func()
                sys.exit()

    def parse_args(self, args=None, namespace=None):
        self.dispatch_if_known(args)
        parsed_args = super(ParserWithSimpleDispatch, self).parse_args(args=args, namespace=namespace)
        return parsed_args

    def add_command(self, func_by_accident=None, **command_kwargs):
        def add_command_with_args(self, func):
            """Adds command to a parser and saves it for later dispatch"""
            # the exact opposite of flag = ... happens when argparse converts the flag to a dest name
            flag = '--' + func.func_name.replace('_','-')

            # I wish you could do partial application of methods! But all there is operator.methodcaller,
            # which doesn't let you add more arguments later
            def add_simple_argument(parser, *args, **kwargs):
                args = (flag,) + args
                kwargs['help'] = func.func_doc or ''
                kwargs.update(command_kwargs)
                parser.add_argument(*args, **kwargs)

            if len(inspect.getargspec(func).args) == 0:
                add_simple_argument(self.simple_group, action='store_true', default=None)
                add_simple_argument(self.doc_group, action='store_true', default=None)
            elif len(inspect.getargspec(func).args) == 1:
                add_simple_argument(self.simple_group, default=None)
                add_simple_argument(self.doc_group, default=None)
            else:
                raise TypeError("Functions need to take one or zero args")
            self.simple_functions_by_flag[flag] = func
            return func
        if callable(func_by_accident):
            return add_command_with_args(self, func_by_accident)
        return partial(add_command_with_args, self)
