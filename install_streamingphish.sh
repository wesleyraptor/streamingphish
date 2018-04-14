#!/bin/bash
# Copyright 2018 Wes Connell
# License: Apache 2.0

# Check if user is running as root.
check_root(){
    if [[ $EUID -ne 0 ]]; then
        printf "[-] This script must be run with root privileges - exiting.\n"
        exit 1
    fi
}

# Check that is a linux platform.
check_linux(){
    KERNEL="$(uname -s)"
    if [ $KERNEL == "Linux" ]; then
        printf "[+] Detected a Linux kernel.\n"
    else
        printf "[-] Unable to detect linux system - exiting.\n"
        exit 1
    fi
}

# Check linux distro.
check_distro(){
    if [ -f /etc/os-release ]; then
        # Freedesktop or systemd.
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        printf "[+] Detected OS $OS running version $VER.\n"
    elif type lsb_release >/dev/null 2>&1; then
        # Linuxbase.
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
        printf "[+] Detected OS $OS running version $VER.\n"
    elif [ -f /etc/lsb-release ]; then
        # Varying versions of Debian/Ubuntu w/o lsb_release.
        . /etc/lsb-release
        OS=$DISTRIB_ID
        VER=$DISTRIB_RELEASE
        printf "[+] Detected OS $OS running version $VER.\n"
    elif [ -f /etc/debian_version ]; then
        # Older Debian/Ubuntu.
        OS=Debian
        VER=$(cat /etc/debian_version)
        printf "[+] Detected OS $OS running version $VER.\n"
    else
        printf "[-] Unable to detect Linux distro - exiting.\n"
        exit 1
    fi
}

# Ensure curl is installed, do so if it's missing.
install_curl(){
    curl -V > /dev/null 2>&1
    RC=$?
    if [[ $RC -ne 0 ]]; then
        # Install it.
        printf "[*] Installing curl...\n"
        apt-get -y install curl 2>&1
        RC=$?
        if [[ $RC -ne 0 ]]; then
            yum -y install curl
            RC=$?
            if [[ $RC -ne 0 ]]; then
                printf "[-] Unable to install curl - exiting.\n"
                exit 1
            fi
        printf "[+] Installed curl.\n"
        fi
    fi
}

# Check if Docker is installed, do so if it's missing.
install_docker(){
    docker -v > /dev/null 2>&1
    RC=$?
    if [[ $RC -ne 0 ]]; then
        printf "[*] Attempting to install Docker via convenience script...\n"
        curl -fsSL get.docker.com -o get-docker.sh > /dev/null 2>&1
        chmod +x get-docker.sh > /dev/null 2>&1
        ./get-docker.sh > /dev/null 2>&1
        RC=$?
        if [[ $RC -ne 0 ]]; then
            printf "[-] Unable to install Docker (error: $RC) - try these instructions:\n"
            printf " >>> https://runnable.com/docker/install-docker-on-linux\n"
            exit 1
        fi
    else
        printf "[+] Confirmed Docker is installed.\n"
    fi
}

# Check if Docker Compose is installed, do so if it's missing.
install_docker_compose(){
    docker-compose -v > /dev/null 2>&1
    RC=$?
    if [[ $RC -ne 0 ]]; then
        printf "[*] Attempting to install Docker Compose...\n"
        # Instructions say install to /usr/local/bin/, but that's not in the $PATH for sudo on
        # several linux machines. Instead I'll write to /usr/bin/ unless there's a better approach.
        curl -L https://github.com/docker/compose/releases/download/1.19.0/docker-compose-`uname -s`-`uname -m` -o /usr/bin/docker-compose > /dev/null 2>&1
        chmod +x /usr/bin/docker-compose > /dev/null 2>&1
        RC=$?
        if [[ $RC -ne 0 ]]; then
            printf "[-] Unable to install Docker Compose (error: $RC) - exiting.\n"
            exit 1
        fi
    else
        printf "[+] Confirmed Docker Compose is installed.\n\n"
    fi
}

# Run the containers in daemon mode.
profit(){
    service docker start
    docker-compose up -d
    RC=$?
    if [[ $RC -ne 0 ]]; then
        printf "[-] Error running the application (error code: $RC) - exiting.\n"
        exit 1
    else
        printf "\n[+] Successfully built and started the applications in daemon mode.\n\n"
    fi
}

# Print basic instructions for running the application.
print_instructions(){
    printf "I suggest adding your user to the docker group so you don't have to use sudo each time, like this:\n"
    printf "   $ sudo usermod -aG docker \$(whoami)\n\n"
    printf "You'll have to logout and log back in for the changes to take effect.\n\n"
    printf "There are 3 services embedded within this application:\n"
    printf " - db\n - cli\n - notebook\n\n"
    printf "Primary actions:\n"
    printf "  1. The Jupyter notebook is currently available at <your_servers_ip_address>:9000.\n"
    printf "  2. Run streamingphish CLI utility:\n   $ docker-compose exec cli streamingphish\n\n"
    printf "See the Github README for further instructions on starting/stopping services, rebuilding the containers, etc.\n"
}

check_root
check_linux
check_distro
install_curl
install_docker
install_docker_compose
profit
print_instructions
