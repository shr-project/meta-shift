addtask testall after do_populate_sysroot
do_testall[recrdeptask] = "do_testall do_test"
do_testall[recideptask] = "do_${BB_DEFAULT_TASK}"
do_testall() {
    :
}
