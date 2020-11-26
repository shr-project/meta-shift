# MIT License
#
# Copyright (c) 2020 Sung Gon Kim
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import bb.utils
import collections
import json
import logging
import os
import sys

logger = logging.getLogger("bitbake-layers")

tinfoil = None


def tinfoil_init(instance):
    global tinfoil
    tinfoil = instance


class Reporter:
    def __init__(self):
        self.result = []

    def section(self, section_name):
        self.result.append("\n%s\n%s\n" % (section_name, ('-' * len(section_name))))

    def add_value(self, key, value):
        if isinstance(value, dict):
            self.result.append("%s:\n" % key)
            for v_key in sorted(value.keys()):
                v_value = value[v_key]
                self.result.append("    %s: %s\n" % (v_key, v_value))
        elif isinstance(value, list):
            self.result.append("%s:\n" % key)
            for v_value in sorted(value):
                self.result.append("    %s\n" % v_value)
        else:
            self.result.append("%s: " % key)
            self.result.append("%s\n" % value)

    def dump(self, output=sys.stdout):
        for line in self.result:
            output.write(line)


class ReporterJson(Reporter):
    def __init__(self):
        self.result = {}
        self.current_section = None

    def section(self, section_name):
        self.current_section = {}
        self.result[section_name] = self.current_section

    def add_value(self, key, value):
        self.current_section[key] = value
        pass

    def dump(self, output=sys.stdout):
        output.write(json.dumps(self.result, indent=2))
        output.write("\n")


def inspect(args):
    def findByName(layername):
        layerconfs = tinfoil.config_data.varhistory.get_variable_items_files("BBFILE_COLLECTIONS", tinfoil.config_data)
        for name, path in layerconfs.items():
            layerdir = os.path.dirname(os.path.dirname(path))
            if layername == os.path.basename(layerdir):
                return layername, name, layerdir, path
        return None, None, None, None

    def getVar(key, default=""):
        return tinfoil.config_data.getVar(key, True) or default

    def findFiles(path, suffix=".conf"):
        if not os.path.exists(path):
            return []
        return [ os.path.splitext(os.path.basename(f))[0] for f in os.listdir(path) if f.endswith(suffix) ]

    def findImages(layername):
        images = []
        pkg_pn = tinfoil.cooker.recipecaches[''].pkg_pn
        (latest_versions, preferred_versions) = tinfoil.find_providers()
        for p in sorted(pkg_pn):
            pref = preferred_versions[p]
            realfn = bb.cache.virtualfn2realfn(pref[1])
            preffile = realfn[0]
            layerdir = bb.utils.get_file_layer(preffile, tinfoil.config_data)
            if layername != layerdir:
                continue
            if not any("core-image" == os.path.splitext(os.path.basename(inherit_class))[0] for
                       inherit_class in tinfoil.cooker_data.inherits.get(preffile, [])):
                continue
            images.append(p)
        return images

    layer, name, path, layerconf = findByName(args.layername)

    if not layer:
        sys.stderr.write("Specified layer '%s' doesn't exist\n" % args.layername)
        return

    report = ReporterJson() if args.json else Reporter()

    report.section("General Information")
    report.add_value("Layer", layer)
    report.add_value("Name", name)
    report.add_value("Path", path)
    report.add_value("Conf", layerconf)
    report.add_value("Priority", getVar("BBFILE_PRIORITY_%s" % name))
    report.add_value("Version", getVar("LAYERVERSION_%s" % name))
    report.add_value("Compatibilities", getVar("LAYERSERIES_COMPAT_%s" % name))
    report.add_value("Dependencies", getVar("LAYERDEPENDS_%s" % name))

    report.section("Additional Information")
    report.add_value("Images", findImages(name))
    report.add_value("Machines", findFiles(os.path.join(path, "conf", "machine")))
    report.add_value("Distros", findFiles(os.path.join(path, "conf", "distro")))
    report.add_value("Classes", findFiles(os.path.join(path, "classes"), ".bbclass"))

    report.dump(open(args.output, "w") if args.output else sys.stdout)


def register_commands(subparsers):
    parser = subparsers.add_parser("inspect",
                                   help="Show the detailed information on the specified layer",
                                   description="Return the detailed information on the specified layer including images, machines, distros, etc.")
    parser.add_argument("-j", "--json", help="prints JSON formatted information", action="store_true")
    parser.add_argument("-o", "--output", help="save the output to a file")
    parser.add_argument("layername", help="the layer name to inspect")
    parser.set_defaults(func=inspect, parserecipes=True)
