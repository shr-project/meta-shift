#!/usr/bin/python

import pytest


def test_default_format(bare_build):
    o = bare_build.shell.execute("recipetool inspect cpplint")
    assert o.stdout.containsAll("General Information",
                                "-------------------",
                                "Name: cpplint",
                                "Summary: CPPLint - a static code analyzer for C/C++",
                                "Description: A Static code analyzer for C/C++ written in python",
                                "Author: Google Inc.",
                                "Homepage: https://github.com/cpplint/cpplint",
                                "Bugtracker: https://github.com/cpplint/cpplint/issues",
                                "Section: devel/python",
                                "License: BSD-3-Clause",
                                "Version: 1.4.5",
                                "Revision: r0",
                                "Layer: meta-shift",
                                "Testable: False")


def test_json_format(bare_build):
    o = bare_build.shell.execute("recipetool inspect cpplint --json")
    assert o.stdout.containsAll('"General Information": {',
                                '"Author": "Google Inc."',
                                '"Homepage": "https://github.com/cpplint/cpplint"',
                                '"Layer": "meta-shift"',
                                '"Bugtracker": "https://github.com/cpplint/cpplint/issues"',
                                '"Summary": "CPPLint - a static code analyzer for C/C++"',
                                '"Name": "cpplint"',
                                '"Version": "1.4.5"',
                                '"Section": "devel/python"',
                                '"Revision": "r0"',
                                '"Testable": false',
                                '"License": "BSD-3-Clause"',
                                '"Description": "A Static code analyzer for C/C++ written in python"')


def test_cmake_project_without_test_enabled(release_build):
    o = release_build.shell.execute("recipetool inspect cmake-project")
    assert o.stdout.containsAll("Name: cmake-project",
                                "Layer: meta-sample",
                                "Testable: False")


def test_cmake_project_with_test_enabled(test_build):
    o = test_build.shell.execute("recipetool inspect cmake-project")
    assert o.stdout.containsAll("Name: cmake-project",
                                "Layer: meta-sample",
                                "Testable: True")
