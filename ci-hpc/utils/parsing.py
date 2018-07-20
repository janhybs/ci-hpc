#!/usr/bin/python3
# author: Jan Hybs

import argparse

class RawFormatter(argparse.HelpFormatter):
    """
    Class SmartFormatter prints help messages without any formatting
        or unwanted line breaks, acivated when help starts with R|
    """

    def _split_lines(self, text, width):
        if text.startswith('R|\n'):
            text = text[3:].rstrip()
            lines = text.splitlines()
            first_indent = len(lines[0]) - len(lines[0].lstrip())
            return [l[first_indent:] for l in lines]
        elif text.startswith('R|'):
            return [l.lstrip() for l in text[2:].strip().splitlines()]

        # this is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)