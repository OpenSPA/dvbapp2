## Our buildserver is currently running on: ##

> Ubuntu 16.04.1 LTS (GNU/3.14.32-xxxx-grs-ipv6-64)

## OpenSPA 7.3 is build using oe-alliance build-environment and several git repositories: ##

> [https://github.com/oe-alliance/oe-alliance-core/tree/4.2](https://github.com/oe-alliance/oe-alliance-core/tree/4.2 "OE-Alliance")
> 
> [https://github.com/OpenSPA/dvbapp](https://github.com/OpenSPA/dvbapp "OpenSPA E2")
> 
> [https://github.com/OpenSPA/OpenSPA_skins](https://github.com/OpenSPA/OpenSPA_skins "OpenSPA Skins")

> and a lot more...


----------

# Building Instructions #

1 - Install packages on your buildserver

    sudo apt-get install -y autoconf automake bison bzip2 cvs diffstat flex g++ gawk gcc gettext git-core gzip help2man ncurses-bin ncurses-dev libc6-dev libtool make texinfo patch perl pkg-config subversion tar texi2html wget zlib1g-dev chrpath libxml2-utils xsltproc libglib2.0-dev python-setuptools zip info coreutils diffstat chrpath libproc-processtable-perl libperl4-corelibs-perl sshpass default-jre default-jre-headless java-common libserf-dev

----------
2 - Set your shell to /bin/bash

    sudo dpkg-reconfigure dash
    When asked: Install dash as /bin/sh?
    select "NO"

----------
3 - Add user openspabuilder

    sudo adduser openspabuilder

----------
4 - Switch to user openspabuilder

    su openspabuilder

----------
5 - Switch to home of openspabuilder

    cd ~

----------
6 - Create folder openspa

    mkdir -p ~/openspa

----------
7 - Switch to folder openspa

    cd openspa

----------
8 - Clone oe-alliance git

    git clone git://github.com/oe-alliance/build-enviroment.git -b 4.2

----------
9 - Switch to folder build-enviroment

    cd build-enviroment

----------
10 - Update build-enviroment

    make update

----------
11 - Finally you can start building a image

    make MACHINE=zgemmah9s DISTRO=openspa DISTRO_TYPE=release image
