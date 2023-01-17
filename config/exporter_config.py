import argparse

from motor.motor_asyncio import AsyncIOMotorClient


class ExportConfig(argparse.Namespace):
    mongo_database = AsyncIOMotorClient(serverSelectionTimeoutMS=5000).scan

    def __init__(self, parser, **kwargs):
        self.parser = parser
        super().__init__(**kwargs)


def get_export_parser():
    parser = argparse.ArgumentParser(
        usage="python spyder.py [command] [flags]",
        description="for more information, please visit https://github.com/GuiDotPy/spyder",
    )
    parser.add_argument("exporter")
    parser.add_argument(
        "-es",
        "--export-status",
        type=int,
        nargs="+",
        default=[],
        help="export url by status"
    )
    parser.add_argument(
        "-ect",
        "--export-content-type",
        type=str,
        nargs="+",
        default=[],
        help="export url by content-type"
    )
    parser.add_argument(
        "-er",
        "--export-regex",
        type=str,
        help="export urls that match the specified regex"
    )
    parser.add_argument(
        "-eurls",
        "--export-urls",
        action=argparse.BooleanOptionalAction,
        help="export all urls"
    )
    parser.add_argument(
        "-ed",
        "--export-downloadable",
        action=argparse.BooleanOptionalAction,
        help="export downloadable urls"
    )
    return parser
