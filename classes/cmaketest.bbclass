inherit cmake
inherit shifttest
inherit shiftutils

OECMAKE_C_FLAGS_append = " -O0 -fprofile-arcs -ftest-coverage"
OECMAKE_CXX_FLAGS_append = " -O0 -fprofile-arcs -ftest-coverage"

EXTRA_OECMAKE += "-DCMAKE_CROSSCOMPILING_EMULATOR='${@shiftutils_qemu_cmake_emulator(d)}'"
EXTRA_OECMAKE += "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"

cmaketest_do_checkcode() {
    shifttest_do_checkcode
}

cmaketest_do_test() {
    shifttest_prepare_output_dir
    shifttest_prepare_env
    echo "Running tests..." | shifttest_print_lines
    cd ${B}
    ctest --output-on-failure | shifttest_print_lines
    shifttest_gtest_update_xmls
    shifttest_check_output_dir
}

cmaketest_do_coverage() {
    shifttest_do_coverage
}

EXPORT_FUNCTIONS do_checkcode do_test do_coverage
