## Our buildserver is currently running on: ##

> Ubuntu 18.04.1 LTS (Kernel 4.15.0)

## OpenSPA 7.4 is build using oe-alliance build-environment and several git repositories: ##

> [https://github.com/oe-alliance/oe-alliance-core/tree/4.3](https://github.com/oe-alliance/oe-alliance-core/tree/4.3 "OE-Alliance")
> 
> [https://github.com/OpenSPA/dvbapp](https://github.com/OpenSPA/dvbapp2 "OpenSPA E2")
> 
> [https://github.com/OpenSPA/OpenSPA_skins](https://github.com/OpenSPA/OpenSPA_skins "OpenSPA Skins")

> and a lot more...


----------

# Building Instructions #

1 - Install packages on your buildserver

    sudo apt-get install -y psmisc autoconf automake bison bzip2 curl cvs diffstat flex g++ gawk gcc gettext git gzip help2man ncurses-bin libncurses5-dev libc6-dev libtool make texinfo patch perl pkg-config subversion tar texi2html wget zlib1g-dev chrpath libxml2-utils xsltproc libglib2.0-dev python-setuptools zip info coreutils diffstat chrpath libproc-processtable-perl libperl4-corelibs-perl sshpass default-jre default-jre-headless java-common libserf-dev qemu quilt libssl-dev ----------
2 - Set your shell to /bin/bash.

    sudo dpkg-reconfigure dash
    When asked: Install dash as /bin/sh?
    select "NO"

----------

3 - modify max_user_watches

    echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf

    sysctl -n -w fs.inotify.max_user_watches=524288

----------
4 - Add user openspabuilder

    sudo adduser openspabuilder

----------
5 - Switch to user openspabuilder

    su openspabuilder

----------
6 - Switch to home of openspabuilder

    cd ~

----------
7 - Create folder openspa

    mkdir -p ~/openspa

----------
8 - Switch to folder openspa

    cd openspa

----------
9 - Clone oe-alliance git

    git clone git://github.com/oe-alliance/build-enviroment.git -b 4.3

----------
10 - Switch to folder build-enviroment

    cd build-enviroment

----------
11 - Update build-enviroment

    make update

----------
12 - Finally you can start building a image

    MACHINE=zgemmah9s DISTRO=openspa DISTRO_TYPE=release make image
