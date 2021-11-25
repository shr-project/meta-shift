"""
Copyright (c) 2020 LG Electronics Inc.
SPDX-License-Identifier: MIT
"""

import sys
import os
import argparse
import glob
import fnmatch
import re
import logging
import scriptutils
import oe.recipeutils
import bb
import json
import subprocess
from collections import OrderedDict

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from oelint_adv.cls_rule import load_rules  # nopep8
from oelint_parser.cls_stash import Stash  # nopep8

logger = logging.getLogger('recipetool')

tinfoil = None


def tinfoil_init(instance):
    global tinfoil
    tinfoil = instance


def make_plain_report(issues):
    return "\n".join([x[1] for x in issues]) + "\n"


def make_json_report(issues):
    json_dict = dict()
    json_dict["issues"] = list()
    for issue in issues:
        item = dict()
        split_data = issue[1].split(":")

        item["file"] = split_data[0]
        item["line"] = int(split_data[1])
        item["severity"] = split_data[2]
        item["rule"] = split_data[3]
        item["description"] = split_data[4]
        json_dict["issues"].append(item)

    return json.dumps(json_dict, indent=2) + "\n"


def check(args, files):
    rules = [x for x in load_rules(args)]
    _loadedIDs = []
    for r in rules:
        _loadedIDs += r.GetIDs()
    stash = Stash(args)
    issues = []
    for f in files:
        try:
            stash.AddFile(f)
        except (IOError, OSError):
            pass

    stash.Finalize()

    for f in list(set(stash.GetRecipes() + stash.GetLoneAppends())):
        for r in rules:
            if not r.OnAppend and f.endswith(".bbappend"):
                continue
            if r.OnlyAppend and not f.endswith(".bbappend"):
                continue
            issues += r.check(f, stash)

    issues = sorted(set(issues), key=lambda x: x[0])

    if args.output:
        output = open(args.output, "w")
        output.write(make_json_report(issues))
        output.close()

    sys.stderr.write(make_plain_report(issues))


def checkrecipes(args):
    logger.info("Checking the specified recipes or files for the styling issues...")
    files = []
    for recipe in args.recipes:
        if os.path.isfile(recipe):
            if recipe.split(".")[-1] in ["bb", "bbappend", "inc"]:
                files.append(recipe)
            else:
                sys.stderr.write("Not a BitBake file: '{}'\n".format(recipe))
        else:
            recipefile = oe.recipeutils.pn_to_recipe(tinfoil.cooker, recipe)
            if recipefile:
                files.append(recipefile)
                files.extend(tinfoil.cooker.collection.get_file_appends(recipefile))
            else:
                sys.stderr.write("Failed to find the recipe file for '{}'\n".format(recipe))
    check(args, files)
    logger.info("Done.")


def register_command(subparsers):
    check_parser = subparsers.add_parser('check',
                                         help="Check specified recipes or files for the OpenEmbedded Style Guide issues.",
                                         description="Check specified recipes or files for the OpenEmbedded Style Guide issues.")
    check_parser.add_argument("-o", "--output", help="save the output to a file")
    check_parser.add_argument("recipes", metavar="RECIPE", nargs='+', help="recipe or file to parse")
    check_parser.set_defaults(func=checkrecipes, parserecipes=True)
