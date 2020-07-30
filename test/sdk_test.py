#!/usr/bin/python

import pytest
import os


def test_populate_sdk_pkgs_check(sdk_build):
    pkgs = sdk_build.files.read("buildhistory/sdk/{SDK_NAME}{SDK_EXT}/{IMAGE_BASENAME}/host/installed-packages.txt")
    assert pkgs.contains("nativesdk-cmake_3.15.3-r0_x86_64-nativesdk.ipk")
    assert pkgs.contains("nativesdk-cppcheck_2.0-r0_x86_64-nativesdk.ipk")
    assert pkgs.contains("nativesdk-cpplint_1.4.5-r0_x86_64-nativesdk.ipk")
    assert pkgs.contains("nativesdk-gcovr_4.2-r0_x86_64-nativesdk.ipk")
    assert pkgs.contains("nativesdk-lcov_1.14-r0_x86_64-nativesdk.ipk")
    assert pkgs.contains("nativesdk-qemu_4.1.0-r0_x86_64-nativesdk.ipk")

    pkgs = sdk_build.files.read("buildhistory/sdk/{SDK_NAME}{SDK_EXT}/{IMAGE_BASENAME}/target/installed-packages.txt")
    assert pkgs.contains("fff_1.0-r0_{TUNE_PKGARCH}.ipk")
    assert pkgs.contains("googletest_1.8.1-r0_{TUNE_PKGARCH}.ipk")

    pkgs = sdk_build.files.read("buildhistory/sdk/{SDK_NAME}{SDK_EXT}/{IMAGE_BASENAME}/files-in-sdk.txt")
    assert pkgs.contains("{SDKTARGETSYSROOT}/usr/include/fff/fff.h")
    assert pkgs.contains("{SDKPATHNATIVE}/usr/share/cmake-3.15/Modules/CMakeUtils.cmake")
    assert pkgs.contains("{SDKPATHNATIVE}/usr/share/cmake-3.15/Modules/FindGMock.cmake")
    assert pkgs.contains("{SDKPATHNATIVE}/usr/share/cmake/OEToolchainConfig.cmake.d/crosscompiling_emulator.cmake")


def test_humidifier_project_test(sdk_build):
    project_dir = "humidifier-project"
    sdk_build.sdk_shell.execute("git clone http://mod.lge.com/hub/yocto/sample/humidifier-project.git {}".format(project_dir))
    assert sdk_build.files.exists(project_dir)

    cd_cmd = 'cd {0} && '.format(project_dir)
    o = sdk_build.sdk_shell.execute(cd_cmd + 'cmake -DENABLE_TESTS=ON .')

    assert o.stdout.contains("gcc -- works")
    assert o.stdout.contains("g++ -- works")
    assert o.stdout.contains("-- Found cross-compiling emulator: TRUE")
    assert o.stdout.contains("-- Found CPPCHECK code checker: TRUE")
    assert o.stdout.contains("-- Found CPPLINT code checker: TRUE")
    assert o.stdout.contains("-- Found gcovr program: TRUE")
    assert o.stdout.contains("-- Found GTest: {0}/sysroots/{1}/usr/lib/libgtest.a".format(sdk_build.sdk_dir, sdk_build.kwargs['REAL_MULTIMACH_TARGET_SYS']))
    assert o.stdout.contains("-- Found GMock: {0}/sysroots/{1}/usr/lib/libgmock.a".format(sdk_build.sdk_dir, sdk_build.kwargs['REAL_MULTIMACH_TARGET_SYS']))

    o = sdk_build.sdk_shell.execute(cd_cmd + 'make all')
    assert o.returncode == 0

    o = sdk_build.sdk_shell.execute(cd_cmd + 'make test')
    assert o.stdout.contains("HumidifierTest.testNothingHappensWhenInitialized .......................   Passed")
    assert o.stdout.contains("HumidifierTest.testNothingChangesWhenHumidityLevelAsDesired ............   Passed")
    assert o.stdout.contains("HumidifierTest.testIncreaseHumidityLevelWhenCurrentLowerThanDesired ....   Passed")
    assert o.stdout.contains("HumidifierTest.testDecreaseHumidityLevelWhenCurrentLargerThanDesired ...   Passed")
    assert o.stdout.contains("100% tests passed, 0 tests failed out of 4")

    o = sdk_build.sdk_shell.execute(cd_cmd + 'make coverage')
    assert o.stdout.contains("Running gcovr...")
    assert o.stdout.contains("lines: 100.0%")
    assert o.stdout.contains("branches: ")
    assert not o.stdout.contains("branches: 0.0%")

    sdk_build.files.remove(project_dir)


def test_cppcheck(sdk_build):
    cppcheck_path = "{0}/usr/bin/cppcheck".format(sdk_build.oecore_native_sysroot)
    assert os.path.exists(cppcheck_path), '{0} not found: {1}'.format('cppcheck', cppcheck_path)
    tmp_dir = "testcppcheck"

    o = sdk_build.sdk_shell.execute('mkdir {0} -p && cd {0} && echo \\"int main(){{int a[10]; a[10] = 0;}}\\" > abc.cpp && {1} --enable=all abc.cpp'.format(tmp_dir, cppcheck_path))
    assert o.stderr.contains("abc.cpp:1:24: error: Array 'a[10]' accessed at index 10, which is out of bounds.")
    assert o.stderr.contains("style: Variable 'a[10]' is assigned a value that is never used.")

    sdk_build.files.remove(tmp_dir)


def test_cpplint(sdk_build):
    cpplint_path = "{0}/usr/bin/cpplint".format(sdk_build.oecore_native_sysroot)
    assert os.path.exists(cpplint_path), '{0} not found: {1}'.format('cpplint', cpplint_path)

    tmp_dir = "testcpplint"
    o = sdk_build.sdk_shell.execute('mkdir {0} -p && cd {0} && echo \\"int main(){{int a[10]; a[10] = 0;}}\\" > abc.cpp && {1} abc.cpp'.format(tmp_dir, cpplint_path))
    assert o.stderr.contains("abc.cpp:0:  No copyright message found.  You should have a line: \"Copyright [year] <Copyright Owner>\"  [legal/copyright] [5]")
    assert o.stderr.contains("abc.cpp:1:  Missing space before {{  [whitespace/braces] [5]")

    sdk_build.files.remove(tmp_dir)
