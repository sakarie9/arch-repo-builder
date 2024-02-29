FROM archlinux:multilib-devel

RUN pacman -Syu --noconfirm git python python-yaml

WORKDIR /app

COPY src /app/
COPY main.py /app/
COPY makepkg* /app/

COPY run.bash /run.bash

# ENTRYPOINT ["/run.bash"]