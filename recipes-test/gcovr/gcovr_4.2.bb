SUMMARY = "gcovr"
DESCRIPTION = "generate code coverage reports with gcc/gcov"
AUTHOR = "gcovr authors"
HOMEPAGE = "https://github.com/gcovr/gcovr"
BUGTRACKER = "https://github.com/gcovr/gcovr/issues"
LICENSE = "BSD-3-Clause"
LIC_FILES_CHKSUM = "file://LICENSE.txt;md5=221e634a1ceafe02ef74462cbff2fb16"

SRC_URI = "git://github.com/gcovr/gcovr.git;protocol=https;tag=${PV};nobranch=1"

S = "${WORKDIR}/git"

DEPENDS += "${PYTHON_PN}-pytest-runner-native"

inherit setuptools3

RDEPENDS_${PN} += "python3-jinja2 python3-lxml"

BBCLASSEXTEND = "native nativesdk"
