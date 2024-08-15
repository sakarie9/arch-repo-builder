FROM archlinux:multilib-devel

RUN pacman-key --init && \
  printf "[archlinuxcn]\nServer = https://repo.archlinuxcn.org/\$arch\nServer = https://mirrors.ustc.edu.cn/archlinuxcn/\$arch\n" >> /etc/pacman.conf && \
  pacman -Syu --noconfirm git python python-yaml ccache meson archlinuxcn-keyring

WORKDIR /app
ENV PYTHONPATH "${PYTHONPATH}:/app/"
ENV PYTHONUNBUFFERED=1

COPY src /app/src
COPY main.py /app/
COPY makepkg* /app/

ENTRYPOINT [ "python", "/app/main.py" ]
