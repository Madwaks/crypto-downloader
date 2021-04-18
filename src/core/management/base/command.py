import os
import sys
from abc import abstractmethod, ABC

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

class CommandError(Exception):
    """
    Exception class indicating a problem while executing a management
    command.
    If this exception is raised during the execution of a management
    command, it will be caught and turned into a custom-printed error
    message to the output stream (i.e., stderr); as a
    result, raising this exception (with a sensible description of the
    error) is the preferred way to indicate that something has gone
    wrong in the execution of a command.
    """
    pass


class CommandParser(ArgumentParser):
    """
    Customized ArgumentParser class to improve some error messages and prevent
    SystemExit in several occasions, as SystemExit is unacceptable when a
    command is called programmatically.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def error(self, message):
        raise CommandError(f'Error: {message}')


class BaseCommand(ABC):
    """
    The base class from which all management commands ultimately
    derive.
    Use this class if you want access to all of the mechanisms which
    parse the command-line arguments and work out what code to call in
    response; if you don't need to change any of that behavior,
    consider using one of the subclasses defined in this file.
    If ``handle()`` or ``execute()`` raised any exception (e.g.
    ``CommandError``), command will  instead print an error
    message.
    Thus, the ``handle()`` method is typically the starting point for
    subclasses; many built-in commands and command types either place
    all of their logic in ``handle()``, or perform some additional
    parsing work in ``handle()`` and then delegate from it to more
    specialized methods as needed.
    Several attributes affect behavior at various steps along the way:
    ``help``
        A short description of the command, which will be printed in
        help messages.
    """
    # Metadata about this command.
    help = ''

    # Configuration shortcuts that alter various logic.
    _called_from_command_line = False

    extra_options = None

    def create_parser(self, prog_name, subcommand, **kwargs):
        """
        Create and return the ``ArgumentParser`` which will be used to
        parse the arguments to this command.
        """
        parser = CommandParser(
            prog=f'{os.path.basename(prog_name)} {subcommand}',
            description=self.help or None,
            formatter_class=ArgumentDefaultsHelpFormatter,
            **kwargs
        )
        parser.add_argument(
            '--settings',
            default=os.getenv("APP_SETTINGS_MODULE"),
            help="""The Python path to a settings module, e.g.
             "engine.settings.main". If this isn't provided, the
             APP_SETTINGS_MODULE environment variable will be used.""",
        )
        parser.add_argument(
            '--pythonpath',
            default=os.getenv("PYTHONPATH"),
            help='A directory to add to the Python path, e.g. "/home/user/projects/external_lib".',
        )
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser):
        """
        Entry point for subclassed commands to add custom arguments.
        """
        pass

    def print_help(self, prog_name, subcommand):
        """
        Print the help message for this command, derived from
        ``self.usage()``.
        """
        parser = self.create_parser(prog_name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv, known_args: bool = False):
        """
        Set up any environment changes requested (e.g., Python path
        and app settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        parser = self.create_parser(argv[0], argv[1])
        if known_args:
            options, extra = parser.parse_known_args(argv[2:])
            self.extra_options = extra
        else:
            options = parser.parse_args(argv[2:])
        cmd_options = vars(options)
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop('args', ())
        try:
            output = self.execute(*args, **cmd_options)
            if isinstance(output, (str, bytes)):
                print(output)
                output = 0
            return int(bool(output))
        except Exception as e:
            if not isinstance(e, CommandError):
                raise e
            print(f'[*][r]{e.__class__.__name__}: {e}[/]', file=sys.stderr)
            return 1

    def execute(self, *args, **options):
        """
        Try to execute this command, add system checks if needed.
        """
        output = self.handle(*args, **options)
        return output

    @abstractmethod
    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement
        this method.
        """
        pass

