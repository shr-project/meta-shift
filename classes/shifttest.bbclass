DEPENDS_prepend = "\
    gtest \
    gmock \
    lcov-native \
    python-lcov-cobertura-native \
    qemu-native \
    cppcheck-native \
    cpplint-native \
    compiledb-native \
    sage-native \
    "

DEBUG_BUILD = "1"

shifttest_print_lines() {
    while IFS= read line; do
        bbplain "$line"
    done
}


def plain(s, d):
    if bb.utils.to_boolean(d.getVar("SHIFTTEST_QUIET", True)):
        return
    bb.plain(s)


def warn(s, d):
    if d.getVar("SHIFTTEST_QUIET", True):
        return
    bb.warn(s)


def error(s, d):
    if d.getVar("SHIFTTEST_QUIET", True):
        return
    bb.error(s)


def fatal(s, d):
    if d.getVar("SHIFTTEST_QUIET", True):
        return
    bb.fatal(s)


def find_files(directory, pattern):
    import fnmatch
    found = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if fnmatch.fnmatch(filename, pattern):
                found.append(os.path.join(root, filename))
    return found


def replace_files(files, pattern, repl):
    import fileinput
    import re
    for filename in files:
        bb.debug(1, "Replacing contents: %s" % filename)
        for line in fileinput.input(filename, inplace=True):
            print(re.sub(pattern, repl, line).rstrip())


def exec_func(func, d):
    bb.debug(2, "Executing the function: %s" % func)
    try:
        cwd = os.getcwd()
        bb.build.exec_func(func, d)
    finally:
        os.chdir(cwd)


def exec_funcs(func, d, prefuncs=True, postfuncs=True):
    bb.debug(2, "Executing the function and its preceeding ones: %s" % func)
    def preceedtasks(task):
        preceed = set()
        tasks = d.getVar("__BBTASKS", False)
        if task not in tasks:
            return preceed
        preceed.update(d.getVarFlag(task, "deps", True) or [])
        return preceed

    def runTask(task):
        if prefuncs:
            for func in (d.getVarFlag(task, "prefuncs", True) or "").split():
                exec_func(func, d)
        exec_func(task, d)
        if postfuncs:
            for func in (d.getVarFlag(task, "postfuncs", True) or "").split():
                exec_func(func, d)

    for task in preceedtasks(func):
        runTask(task)
    runTask(func)


def check_call(cmd, d, **options):
    if not "shell" in options:
        options["shell"] = True

    bb.debug(2, 'Executing: "%s"' % cmd)
    import subprocess
    subprocess.check_call(cmd, **options)


def exec_proc(cmd, d, **options):
    if not "shell" in options:
        options["shell"] = True

    bb.debug(2, 'Executing: "%s"' % cmd)
    proc = bb.process.Popen(cmd, **options)

    for line in proc.stdout:
        plain(line.decode("utf-8").rstrip(), d)


addtask checkcode after do_compile
do_checkcode[nostamp] = "1"
do_checkcode[doc] = "Runs static analysis for the target"

python shifttest_do_checkcode() {
    # Configure default arguments
    kwargs = {
        "source-path": d.getVar("S", True),
        "build-path": d.getVar("B", True),
        "tool-path": d.expand("${STAGING_DIR_NATIVE}${bindir}"),
        "target-triple": d.getVar("TARGET_SYS", True),
        "output-path": "",
        "tool-options": "",
    }

    # Configure the output path argument
    if d.getVar("TEST_REPORT_OUTPUT", True):
        report_dir = d.expand("${TEST_REPORT_OUTPUT}/${PF}/checkcode")
        bb.debug(2, "Configuring the checkcode output path: %s" % report_dir)
        bb.utils.remove(report_dir, True)
        bb.utils.mkdirhier(report_dir)
        kwargs["output-path"] = "--output-path=%s" % report_dir

    # Configure tool options
    bb.debug(2, "Configuring the checkcode tool options")
    for tool in (d.getVar("CHECKCODE_TOOLS", True) or "").split():
        kwargs["tool-options"] += " " + tool
        options = d.getVarFlag("CHECKCODE_TOOL_OPTIONS", tool, True)
        if options:
            kwargs["tool-options"] += ":" + options.replace(" ", "\ ")

    try:
        # Make sure that the compile_commands.json file is available
        json_file = d.expand("${B}/compile_commands.json")
        temporary = False

        if not os.path.exists(json_file):
            plain("Creating the compile_commands.json using compiledb", d)
            exec_proc("compiledb --command-style -n make", d, cwd=d.getVar("B", True))
            temporary = True

        # Run sage
        exec_proc("sage --verbose " \
                  "--source-path {source-path} " \
                  "--build-path {build-path} " \
                  "--tool-path {tool-path} " \
                  "--target-triple {target-triple} " \
                  "{output-path} " \
                  "{tool-options}".format(**kwargs), d, cwd=d.getVar("B", True))
    finally:
        if temporary:
            bb.utils.remove(json_file)
}

# In order to overwrite the sstate cache libraries
do_install[nostamp] = "1"

addtask test after do_compile do_populate_sysroot
do_test[nostamp] = "1"
do_test[doc] = "Runs tests for the target"

shifttest_do_test() {
    bbfatal "'inherit shifttest' is not allowed. You should inherit an appropriate bbclass instead."
}

shifttest_prepare_output_dir() {
    if [ ! -z "${TEST_REPORT_OUTPUT}" ]; then
        mkdir -p "${TEST_REPORT_OUTPUT}/${PF}/test"
        rm -rf "${TEST_REPORT_OUTPUT}/${PF}/test/*"
    fi
}

shifttest_prepare_env() {
    if [ ! -z "${TEST_REPORT_OUTPUT}" ]; then
        export GTEST_OUTPUT="xml:${TEST_REPORT_OUTPUT}/${PF}/test/"
    fi
    export LD_LIBRARY_PATH="${SYSROOT_DESTDIR}${libdir}:${LD_LIBRARY_PATH}"

    local LCOV_DATAFILE_BASE="${B}/coverage_base.info"

    lcov -c -i -d ${B} -o ${LCOV_DATAFILE_BASE} \
    --ignore-errors gcov \
    --gcov-tool ${TARGET_PREFIX}gcov \
    --rc lcov_branch_coverage=1
}

shifttest_gtest_update_xmls() {
    [ -z "${TEST_REPORT_OUTPUT}" ] && return
    [ ! -d "${TEST_REPORT_OUTPUT}/${PF}/test" ] && return
    find "${TEST_REPORT_OUTPUT}/${PF}/test" -name "*.xml" \
        -exec sed -i "s|classname=\"|classname=\"${PN}.|g" {} \;
}

shifttest_check_output_dir() {
    [ -z "${TEST_REPORT_OUTPUT}" ] && return
    [ -d "${TEST_REPORT_OUTPUT}/${PF}/test" ] && return
    bbwarn "No test report files found at ${TEST_REPORT_OUTPUT}/${PF}/test"
}


addtask coverage after do_test
do_coverage[nostamp] = "1"
do_coverage[doc] = "Measures code coverage metrics for the target"

python shifttest_do_coverage() {
    LCOV_DATAFILE_BASE = d.expand("${B}/coverage_base.info")
    LCOV_DATAFILE_TEST = d.expand("${B}/coverage_test.info")
    LCOV_DATAFILE_TOTAL = d.expand("${B}/coverage_total.info")
    LCOV_DATAFILE = d.expand("${B}/coverage.info")

    # Remove files if exist
    bb.utils.remove(LCOV_DATAFILE_TOTAL)
    bb.utils.remove(LCOV_DATAFILE)

    if not find_files(d.getVar("B", True), "*.gcda"):
        warn(d.expand("No .gcda files found at ${B}"), d)
        return

    # Prepare for the coverage reports
    check_call("lcov -c -d %s -o %s --gcov-tool %s --rc %s" % (
        d.getVar("B", True),
        LCOV_DATAFILE_TEST,
        d.expand("${TARGET_PREFIX}gcov"),
        "lcov_branch_coverage=1"), d)

    check_call("lcov -a %s -a %s -o %s --rc %s" % (
        LCOV_DATAFILE_BASE,
        LCOV_DATAFILE_TEST,
        LCOV_DATAFILE_TOTAL,
        "lcov_branch_coverage=1"), d)

    check_call('lcov --extract %s --rc %s "%s" -o %s' % (
        LCOV_DATAFILE_TOTAL,
        "lcov_branch_coverage=1",
        d.expand("${S}/*"),
        LCOV_DATAFILE), d)

    plain("GCC Code Coverage Report", d)
    exec_proc("lcov --list %s --rc %s" % (
        LCOV_DATAFILE,
        "lcov_branch_coverage=1"), d)

    if d.getVar("TEST_REPORT_OUTPUT", True):
        report_dir = d.expand("${TEST_REPORT_OUTPUT}/${PF}/coverage")
        xml_file = os.path.join(report_dir, "coverage.xml")

        if os.path.exists(report_dir):
            bb.debug(2, "Removing the existing coverage directory: %s" % report_dir)
            bb.utils.remove(report_dir, True)

        check_call("genhtml %s " \
                   "--demangle-tool %s " \
                   "--demangle-cpp " \
                   "--output-directory %s " \
                   "--ignore-errors %s " \
                   "--rc %s" % (LCOV_DATAFILE,
                                d.expand("${TARGET_PREFIX}c++filt"),
                                report_dir,
                                "source",
                                "genhtml_branch_coverage=1"), d)

        check_call("nativepython -m lcov_cobertura %s " \
                   "--demangle-tool=%s " \
                   "--demangle " \
                   "--output %s" % (LCOV_DATAFILE,
                                    d.expand("${TARGET_PREFIX}c++filt"),
                                    xml_file), d, cwd=d.getVar("S", True))

        if os.path.exists(xml_file):
            # Prepend the package name to each of the package tags
            replace_files([xml_file], '(<package.*name=")', d.expand('\g<1>${PN}.'))
        else:
            warn("No coverage report files generated at %s" % report_dir)
}
