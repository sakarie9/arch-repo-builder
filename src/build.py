import fnmatch
import os
import shutil
import subprocess

from .config import BASE_PATH, C
from .model import BuildResult, ResultEnum
from .utils import get_repository_db_name, get_repository_path
from .repo import refresh_local_repo

makepkg_path = os.path.join(
    os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "makepkg_root"
)
makepkg_config_path = os.path.join(
    os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "makepkg.conf"
)
print(f"!!!makepkg_path: {makepkg_path}")
print(f"!!!makepkg_config_path: {makepkg_config_path}")

pkgbuilds_container_path = os.path.join(BASE_PATH, C.pkgbuilds.container)
aurs_container_path = os.path.join(BASE_PATH, C.aurs.container)

_db_pkgs = []
build_results = []


def list_pkgbuilds_pkgname():
    if not os.path.exists(pkgbuilds_container_path):
        return []
    return os.listdir(pkgbuilds_container_path)


def list_pkgbuilds_path():
    if not os.path.exists(pkgbuilds_container_path):
        return []
    subfolders = [f.path for f in os.scandir(pkgbuilds_container_path) if f.is_dir()]
    return subfolders


def list_aurs_path():
    subfolders = [
        os.path.join(aurs_container_path, f)
        for f in C.aurs.packages
        if os.path.exists(os.path.join(aurs_container_path, f))
    ]
    return subfolders


def clone_aur_packages():
    for aur in C.aurs.packages:
        url = f"https://aur.archlinux.org/{aur}.git"

        if not os.path.exists(aurs_container_path):
            os.makedirs(aurs_container_path)

        if not os.path.exists(os.path.join(aurs_container_path, aur)):
            subprocess.run(["git", "clone", "--depth=1", url], cwd=aurs_container_path)


def copy_build_packages(path):
    package_name = ""
    package_full_path = ""

    files = os.listdir(path)
    matched_pkgs = [f for f in files if fnmatch.fnmatch(f, "*.pkg.tar.zst")]
    sorted_pkgs = sorted(matched_pkgs, reverse=True)

    if not sorted_pkgs:
        print(f"!!!{os.path.basename(path)} build failed!")
    else:
        package_name = sorted_pkgs[0]
        package_full_path = os.path.join(path, sorted_pkgs[0])

    repo_path = get_repository_path(C.global_settings.repository)

    os.makedirs(repo_path, exist_ok=True)

    if os.path.exists(package_full_path):
        shutil.copy(package_full_path, repo_path)
    else:
        return

    subprocess.run(
        [
            "repo-add",
            "--new",
            "--remove",
            get_repository_db_name(C.global_settings.repository),
            package_name,
        ],
        cwd=repo_path,
    )


def rebuild(pkgname):
    if pkgname in list_pkgbuilds_pkgname():
        rebuild_dir = os.path.join(pkgbuilds_container_path, pkgname)
    elif pkgname in C.aurs.packages:
        rebuild_dir = os.path.join(aurs_container_path, pkgname)
    else:
        raise RuntimeError("Rebuild package requested not exist!")

    subprocess.run(
        ["pkgctl", "build", "-w", "1", "--clean", "--rebuild"], cwd=rebuild_dir
    )


def get_db_pkg_list():
    global _db_pkgs
    if not _db_pkgs:
        repo_db = os.path.join(BASE_PATH, C.global_settings.repository)
        if os.path.isfile(repo_db):
            result = subprocess.run(
                "tar --exclude='*/*' -tf " + repo_db,
                check=True,
                stdout=subprocess.PIPE,
                shell=True,
            ).stdout.decode("utf-8")
            _db_pkgs = [f[:-1] for f in result.split("\n") if f != ""]
            print(f"!!!packages in db:\n{_db_pkgs}")
    return _db_pkgs


def install_package_from_db(pkgname):
    subprocess.run(
        ["pacman", "-U", "--noconfirm", pkgname],
        cwd=get_repository_path(C.global_settings.repository),
    )


def is_package_exist_in_db(pkgbuild):
    # for git packages, update pkgver first
    if fnmatch.fnmatch(pkgbuild, "*-git"):
        subprocess.run([makepkg_path, "-o", "-d"], cwd=pkgbuild)

    # extract package basename from PKGBUILD
    result = subprocess.run(
        [makepkg_path, "--config", makepkg_config_path, "--packagelist"],
        check=True,
        stdout=subprocess.PIPE,
        cwd=pkgbuild,
    ).stdout.decode("utf-8")
    pkg = "-".join((os.path.splitext(os.path.basename(result))[0].split("-"))[:-1])

    print(f"!!!{pkg} read from PKGBUILD")

    # compare package basename to database
    if pkg in get_db_pkg_list():
        # if package exists in db, install it to meet dependency
        pkgname = os.path.basename(result).strip()
        install_package_from_db(pkgname)

        return True

    return False


def is_package_been_built(pkgbuild):
    result = (
        subprocess.run(
            [makepkg_path, "--packagelist"],
            check=True,
            stdout=subprocess.PIPE,
            cwd=pkgbuild,
        )
        .stdout.decode("utf-8")
        .strip()
    )

    if os.path.isfile(result):
        return True
    else:
        return False


def makepkg():
    packages_list = list_pkgbuilds_path() + list_aurs_path()
    print(f"!!!Packages\n{packages_list}")
    for pkgbuild in packages_list:
        pkgname = os.path.basename(pkgbuild)
        print(f"!!!Start build packages {pkgname}")

        if is_package_exist_in_db(pkgbuild):
            print(f"!!!{pkgname} skipped build and copy!")
            build_results.append(BuildResult(pkgname, ResultEnum.SKIP.value))
            continue
        elif is_package_been_built(pkgbuild):
            copy_build_packages(pkgbuild)
            print(f"!!!{pkgname} skipped build!")
            build_results.append(BuildResult(pkgname, ResultEnum.COPY.value))
            continue
        else:
            # subprocess.run(["pkgctl", "build", "-w", "1", "--clean"], cwd=pkgbuild)
            # subprocess.run(["paru", "--build", "--chroot", "--skipreview", "--clean"], cwd=pkgbuild)
            result = subprocess.run(
                [
                    makepkg_path,
                    "--config",
                    makepkg_config_path,
                    "--syncdeps",
                    "--clean",
                    "--noconfirm",
                ],
                cwd=pkgbuild,
            )
            if result.returncode:
                # return non 0, failed
                build_results.append(BuildResult(pkgname, ResultEnum.FAIL.value))
            else:
                copy_build_packages(pkgbuild)
                build_results.append(BuildResult(pkgname, ResultEnum.OK.value))

        # Refresh Local Repo after every build
        refresh_local_repo()

    for result in build_results:
        print(result)
    
    subprocess.run(
        ["realpath", "~/.cache/ccache"]
    )

    subprocess.run(
        ["ls", "-la", "~/.cache/ccache"]
    )
