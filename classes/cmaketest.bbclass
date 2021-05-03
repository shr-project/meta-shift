inherit cmake
inherit shifttest


OECMAKE_C_FLAGS_append_class-target = " -O0 -fprofile-arcs -ftest-coverage"
OECMAKE_CXX_FLAGS_append_class-target = " -O0 -fprofile-arcs -ftest-coverage"

EXTRA_OECMAKE_append_class-target = " -DCMAKE_CROSSCOMPILING_EMULATOR='${@shiftutils_qemu_cmake_emulator(d)}'"
EXTRA_OECMAKE_append_class-target = " -DCMAKE_EXPORT_COMPILE_COMMANDS=ON"


cmake_do_compile_prepend_class-target() {
    export TARGET_SYS="${TARGET_SYS}"
}

python cmaketest_do_checkcode() {
    bb.build.exec_func("shifttest_do_checkcode", d)
}

python cmaketest_do_test() {
    if isNativeCrossSDK(d.getVar("PN", True) or ""):
        warn("Unsupported class type of the recipe", d)
        return

    env = os.environ.copy()

    # To access the shared libraries of other packages
    env["LD_LIBRARY_PATH"] = d.expand("${SYSROOT_DESTDIR}${libdir}:${LD_LIBRARY_PATH}")

    configured = d.getVar("SHIFT_REPORT_DIR", True)

    if configured:
        report_dir = d.expand("${SHIFT_REPORT_DIR}/${PF}/test")
        mkdirhier(report_dir, True)

        # Create Google test report files
        env["GTEST_OUTPUT"] = "xml:%s/" % report_dir

    for gcdaFile in find_files(d.getVar("B", True), "*.gcda"):
        bb.utils.remove(gcdaFile)

    # Prepare for the coverage reports
    check_call(["lcov", "-c", "-i",
                "-d", d.getVar("B", True),
                "-o", d.expand("${B}/coverage_base.info"),
                "--ignore-errors", "gcov",
                "--gcov-tool", d.expand("${TARGET_PREFIX}gcov"),
                "--rc", "lcov_branch_coverage=1"], d)

    plain("Running tests...", d)
    try:
        timeout(exec_proc, "ctest --output-on-failure", d, env=env, cwd=d.getVar("B", True))
    except bb.process.ExecutionError as e:
        warn(str(e), d)
        if d.getVar("SHIFT_TIMEOUT", True) and e.exitcode == 124:
            err = bb.BBHandledException(e)
            err.exitcode = e.exitcode
            raise err

    if configured:
        if os.path.exists(report_dir):
            # Prepend the package name to each of the classname tags for GTest reports
            xml_files = find_files(report_dir, "*.xml")
            replace_files(xml_files, 'classname="', d.expand('classname="${PN}.'))
        else:
            warn("No test report files found at %s" % report_dir, d)
}

python cmaketest_do_coverage() {
    bb.build.exec_func("shifttest_do_coverage", d)
}

python cmaketest_do_checktest() {
    bb.build.exec_func("shifttest_do_checktest", d)
}

python cmaketest_do_checkrecipe() {
    bb.build.exec_func("shifttest_do_checkrecipe", d)
}

python cmaketest_do_report() {
    bb.build.exec_func("shifttest_do_report", d)
}

EXPORT_FUNCTIONS do_checkcode do_test do_coverage do_checktest do_checkrecipe do_report
