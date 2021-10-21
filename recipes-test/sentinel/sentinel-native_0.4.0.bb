SUMMARY = "Mutation Testing Tool"
DESCRIPTION = "The mutation testing tool for the meta-shift project"
AUTHOR = "Sung Gon Kim"
HOMEPAGE = "http://mod.lge.com/hub/yocto/sentinel"
BUGTRACKER = "http://mod.lge.com/hub/yocto/sentinel/issues"
SECTION = "devel"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=68afeac0415f7ffea472ec34ec9d20c7 \
                    file://external/args-6.2.3/LICENSE;md5=b5d002ff26328bc38158aff274711f1d \
                    file://external/tinyxml2/LICENSE.txt;md5=135624eef03e1f1101b9ba9ac9b5fffd \
                    file://external/fmt/LICENSE.rst;md5=af88d758f75f3c5c48a967501f24384b"

DEPENDS_class-native += "\
    clang-cross-${TUNE_ARCH} \
    libgit2-native \
    ncurses-native \
"

SRC_URI = "git://mod.lge.com/hub/yocto/sentinel.git;protocol=http;nobranch=1"
SRCREV = "b88b71e8609ba1a7f1f4e7230ec1f028bb68ee57"

S = "${WORKDIR}/git"

inherit cmake native

