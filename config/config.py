import sys

from config.scan_config import ScanConfig, get_scan_parser
from config.exporter_config import ExportConfig, get_export_parser


def parse_error(commands):
    available_commands = ', '.join(commands.keys())
    message = f"you need to choose one of these commands: {available_commands}"
    message += "\nusage: python spyder.py [command] [flags]"
    print(message)
    sys.exit()


def get_config():
    commands = {
        "scan": (ScanConfig, get_scan_parser()),
        "exporter": (ExportConfig, get_export_parser())
    }

    selected_command = sys.argv[1] if len(sys.argv) >= 2 else ""
    config_class, parser = commands.get(selected_command, (None, None))

    if config_class and parser:
        args = parser.parse_args()
        config_instance = config_class(parser, **vars(args))

        if hasattr(config_instance, "_validate"):
            config_instance._validate()

        return config_instance, selected_command

    parse_error(commands)