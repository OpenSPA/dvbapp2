## Our buildserver is currently running on: ##

> Ubuntu 24.04.1 (GNU/Linux 6.8.0-51-generic x86_64)

## minimum hardware requirement : ##

> RAM:  16GB
> 
> SWAP: 8GB
> 
> CPU: CPU: Multi-Core/Multi-Threaded
>
> Storage: 250 GB free for a single build; 500 GB+ for multi-builds

## openSPA 8.x is build using oe-alliance build-environment and several git repositories: ##

> [https://github.com/oe-alliance/oe-alliance-core/tree/5.5.1](https://github.com/oe-alliance/oe-alliance-core/tree/5.5.1 "OE-Alliance")
> 
> [https://github.com/openspa/dvbapp2/tree/master](https://github.com/openspa/dvbapp2/tree/master "OpenSPA E2") based on [https://github.com/openatv/enigma2](https://github.com/openatv/enigma2 "openATV E2")
> 
> [https://github.com/openspa/MetrixHD](https://github.com/openspa/MetrixHD/tree/py3 "OpenSPA Skin")

> and a lot more...


----------

# Building Instructions #

1 - Install packages on your buildserver

    sudo apt-get install -y autoconf automake bison bzip2 chrpath cmake coreutils cpio curl cvs debianutils default-jre default-jre-headless diffstat flex g++ gawk gcc gcc-12 gcc-multilib g++-multilib gettext git gzip help2man info iputils-ping java-common libc6-dev libc6-dev-i386 libglib2.0-dev libncurses-dev libperl4-corelibs-perl libproc-processtable-perl libsdl1.2-dev libserf-dev libtool libxml2-utils make ncurses-bin patch perl pkg-config psmisc python3 python3-git python3-jinja2 python3-pexpect python3-pip python3-setuptools quilt socat sshpass subversion tar texi2html texinfo unzip wget xsltproc xterm xz-utils zip zlib1g-dev zstd fakeroot lz4 git-lfs
    
----------
2 - Set python3 as preferred provider for python

    sudo update-alternatives --install /usr/bin/python python /usr/bin/python2 1
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 2
    sudo update-alternatives --config python
    select python3
    
----------    
3 - Set your shell to /bin/bash.

    sudo ln -sf /bin/bash /bin/sh

----------
4 - modify max_user_watches

    echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf

    sudo sysctl -n -w fs.inotify.max_user_watches=524288

----------
5 - Modify AppArmor config.

    echo 'kernel.apparmor_restrict_unprivileged_userns=0' | sudo tee /etc/sysctl.d/60-apparmor-namespace.conf > /dev/null && sudo sysctl --system

    sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0

----------
6 - Add user openspabuilder

    sudo adduser openspabuilder

----------
7 - Switch to user openspabuilder

    su - openspabuilder

----------
8 - Add your git user and email

    git config --global user.email "you@example.com"

    git config --global user.name "Your Name"

----------
9 - Create folder openspa8.x

    mkdir -p ~/openspa8.x

----------
10 - Switch to folder openspa8.x

    cd openspa8.x

----------
11 - Clone oe-alliance git

    git clone git://github.com/oe-alliance/build-enviroment.git -b 5.5.1

----------
12 - Switch to folder build-enviroment

    cd build-enviroment

----------
13 - Update build-enviroment

    make update

----------
14 - Finally you can start building a image

* Build an image with feed (build time 5-12h)

      MACHINE=zgemmah9combo DISTRO=openspa DISTRO_TYPE=release make image

* Build an image without feed (build time 1-2h)

      MACHINE=zgemmah9combo DISTRO=openspa DISTRO_TYPE=release make enigma2-image

* Build the feeds

      MACHINE=zgemmah9combo DISTRO=openspa DISTRO_TYPE=release make feeds

* Build specific packages

      MACHINE=zgemmah9combo DISTRO=openspa DISTRO_TYPE=release make init

      cd builds/openspa/release/zgemmah9combo/

      source env.source

      bitbake nfs-utils rpcbind ...

----------
