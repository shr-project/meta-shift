SUMMARY = "Static Analyzer Group Executor"
DESCRIPTION = "Execute the set of static analysis tools against the given source code"
AUTHOR = "Sung Gon Kim"
HOMEPAGE = "https://github.com/shift-left-test/sage"
BUGTRACKER = "https://github.com/shift-left-test/sage/issues"
SECTION = "devel"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=df949e8c96ecf1483905048fb77276b5"

SRC_URI = "git://github.com/shift-left-test/sage.git;protocol=https;nobranch=1"

SRCREV = "88f24c5863da5484f4804abb5bb61e18f3a0ac02"

S = "${WORKDIR}/git"

inherit setuptools


DEPENDS += "\
    ${PYTHON_PN}-texttable \
    duplo \
    metrixpp \
"

RDEPENDS_${PN} += "\
    ${PYTHON_PN}-texttable \
"

do_install_append_class-native() {
    if test -e ${D}${bindir} ; then
        for i in ${D}${bindir}/* ; do \
            sed -i -e s:${bindir}/python-native/python:${USRBINPATH}/env\ nativepython:g $i
        done
    fi
}

BBCLASSEXTEND = "native nativesdk"
