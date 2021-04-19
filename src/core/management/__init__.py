import functools
import os
import pkgutil
import sys
from importlib import import_module
from pathlib import Path

from .base import BaseCommand, CommandError, CommandParser


def find_commands(management_dir):
    """
    Given a path to a management directory, return a list of all the command
    names that are available.
    """
    command_dir = Path(management_dir) / "commands"
    return [
        name
        for _, name, is_pkg in pkgutil.iter_modules([command_dir])
        if not is_pkg and not name.startswith("_")
    ]


def load_command_class(name):
    """
    Given a command name and an application name, return the Command
    class instance. Allow all errors raised by the import process
    (ImportError, AttributeError) to propagate.
    """
    module = import_module(f"core.management.commands.{name}")
    return module.Command()


@functools.lru_cache(maxsize=None)
def get_commands():
    """
    Return a dictionary mapping command names to their callback applications.
    Look for a management.commands package in ``core``, then register all
    commands in that package.
    The dictionary is cached on the first call and reused on subsequent
    calls.
    """
    commands = {name: "core" for name in find_commands(__path__[0])}

    return commands


def call_command(command_name, *args, **options):
    """
    Call the given command, with the given options and args/kwargs.
    This is the primary API you should use for calling specific commands.
    `command_name` may be a string or a command object. Using a string is
    preferred unless the command object is required for further processing or
    testing.
    Some examples:
        call_command('shell')
        # Do something with cmd ...
    """
    # Load the command object by name.
    try:
        app_name = get_commands()[command_name]
    except KeyError:
        raise CommandError(f"Unknown command: {command_name}")

    if isinstance(app_name, BaseCommand):
        # If the command is already loaded, use it directly.
        command = app_name
    else:
        command = load_command_class(command_name)

    # Simulate argument parsing to get the option defaults (see #10080 for details).
    parser = command.create_parser("", command_name)
    # Use the `dest` option name from the parser option
    opt_mapping = {
        min(s_opt.option_strings).lstrip("-").replace("-", "_"): s_opt.dest
        for s_opt in parser._actions
        if s_opt.option_strings
    }
    arg_options = {opt_mapping.get(key, key): value for key, value in options.items()}
    parse_args = [str(a) for a in args]
    # Any required arguments which are passed in via **options must be passed
    # to parse_args().
    parse_args += [
        f"{min(opt.option_strings)}={arg_options[opt.dest]}"
        for opt in parser._actions
        if opt.required and opt.dest in options
    ]
    defaults = parser.parse_args(args=parse_args)
    defaults = dict(defaults._get_kwargs(), **arg_options)

    return command.execute(*args, **defaults)


class ManagementUtility:
    """
    Encapsulate the logic of the engine utilities.
    """

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        self.settings_exception = None

    def main_help_text(self):
        """
        Return the script's main help text, as a string.
        """
        usage = ['List of available subcommands for "engine":']
        usage.extend(sorted(get_commands()))
        return "\n * ".join(usage)

    def fetch_command(self, subcommand):
        """
        Try to fetch the given subcommand, printing a message with the
        appropriate command called from the command line (usually
        "api.py") if it can't be found.
        """
        # Get commands outside of try block to prevent swallowing exceptions
        commands = get_commands()
        try:
            app_name = commands[subcommand]
        except KeyError:
            print(
                (
                    f"[*][r]Unknown command: [y]{subcommand}[/]\n"
                    f"[*][r]Run '[y]python {self.prog_name} help[r]' for usage.[/]"
                ),
                file=sys.stderr,
            )
            raise SystemExit(1)
        if isinstance(app_name, BaseCommand):
            # If the command is already loaded, use it directly.
            klass = app_name
        else:
            klass = load_command_class(subcommand)
        return klass

    def execute(self):
        """
        Given the command-line arguments, figure out which subcommand is being
        run, create a parser appropriate to that command, and run it.
        """
        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = "help"  # Display help if no arguments were given.

        # Preprocess options to extract --settings and --pythonpath.
        # These options could affect the commands that are available, so they
        # must be processed early.
        parser = CommandParser(
            usage="%(prog)s subcommand [options] [args]",
            add_help=False,
            allow_abbrev=False,
        )
        parser.add_argument("--settings")
        parser.add_argument("--pythonpath")
        parser.add_argument("args", nargs="*")  # catch-all
        try:
            options, args = parser.parse_known_args(self.argv[2:])
        except CommandError:
            pass  # Ignore any option errors at this point.

        if subcommand == "help":
            if not options.args:
                print(self.main_help_text())
            else:
                self.fetch_command(options.args[0]).print_help(
                    self.prog_name, options.args[0]
                )
            return 0
        elif self.argv[1:] in (["--help"], ["-h"]):
            print(self.main_help_text())
            return 0
        else:
            return self.fetch_command(subcommand).run_from_argv(self.argv)


def execute_from_command_line(argv=None):
    """Run a ManagementUtility."""
    utility = ManagementUtility(argv)
    return utility.execute()
