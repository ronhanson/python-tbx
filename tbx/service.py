#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
:Author: Ronan Delacroix
:Copyright: 2014 Ronan Delacroix


1 - HOW TO WITH FUNCTION :

    def my_service(arg=None):
        print('Hello %s' % arg)

    tbx.service.launch_function(my_service, arg="Ronan")


2 - HOW TO WITH CLASS :

    class MyService(tbx.service.Service):
        def run(self):
            print("Hello %s (debug:%s)" % (self.arg, self.debug))

    tbx.service.launch_service(MyService, arg="Ronan")

"""
import logging
import time
import argparse


class Service:
    """
    Service class.
    Can be launched once or in loop mode.
    """
    def __init__(self, **kwargs):
        self.loop_duration = kwargs.pop('loop_duration', 1.0)

        logging.debug("Created service %s" % self.service_name)
        for k in kwargs:
            setattr(self, k, kwargs[k])
        self.setup()

    @property
    def service_name(self):
        return self.__class__.__name__.replace('Service', '')

    def setup(self):
        """
        Empty method. Can be overridden.
        Called at object creation.
        """
        logging.debug("Setting up service %s" % self.service_name)

    def destroy(self):
        """
        Empty method. Can be overridden.
        Called at object disposal.
        """
        logging.debug("Destroying service %s" % self.service_name)
        return None

    def run(self):
        """
        Abstract method. Shall be overridden by sub classes.
        """
        raise Exception('run method shall be overridden in sub class.')

    def loop(self):
        """
        Run the demo suite in a loop.
        """
        logging.info("Running %s in loop mode." % self.service_name)

        res = None
        while True:
            try:
                res = self.run()
                time.sleep(self.loop_duration)
            except KeyboardInterrupt:
                logging.warning("Keyboard Interrupt during loop, stopping %s service now..." % self.service_name)
                break
            except Exception as e:
                logging.exception("Error in main loop! (%s)" % e)
                raise e
        return res  # returns last result

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        r = self.destroy()
        return r or self


def launch_function(function, description=None, **kwargs):
    if not description:
        description = function.__doc__

    def custom_run(svc):
        function(**kwargs)

    custom_service = type(function.__name__, (Service,), {'run': custom_run})

    return launch_service(custom_service, description=description)


def launch_service(service, description=None, parser_callback=None, **kwargs):
    if not description:
        description = service.__doc__

    parser = argparse.ArgumentParser(description=description)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--loop', dest='loop', action="store_true",
                       help='Run the service in loop mode (Default mode).', default=True)
    group.add_argument('-1', '--once', dest='loop', action="store_false",
                       help='Run the service once.', default=True)
    parser.add_argument("-t", "--loop-duration", dest="loop_duration", type=float,
                        help="Looping duration in seconds (Default 2).", metavar='DURATION', default=1.0)
    parser.add_argument("-d", "--debug", dest="debug", action="store_true",
                        help="Debug mode.", default=False)

    if parser_callback:
        parser_callback(parser)

    args = parser.parse_args()

    # get the data out of args
    data = dict(args._get_kwargs())
    data.pop('loop')
    data.pop('loop_duration')

    kwargs.update(data)  # this will set kwargs["debug"] value at least, plus the arguments added by the parser_callback

    result = None
    svc = service(**kwargs)
    svc.loop_duration = args.loop_duration

    if args.loop:
        result = svc.loop()
    else:
        result = svc.run()

    logging.info("Exiting %s service." % svc.service_name)
    svc.destroy()

    return result

