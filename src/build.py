import os
import shutil
import subprocess
import fnmatch
from .config import C, BASE_PATH
from .utils import *

makepkg_path = os.path.join(BASE_PATH, "makepkg_root")

def list_pkgbuilds():
    container_path = os.path.join(BASE_PATH, C.pkgbuilds.container)
    return os.listdir(container_path)

def list_pkgbuilds_dir():
    container_path = os.path.join(BASE_PATH, C.pkgbuilds.container)
    # pkgbuilds_paths = list(
    #     map(lambda path: os.path.join(BASE_PATH, path), 
    #         os.listdir(container_path))
    #     )
    # print(pkgbuilds_paths)

    # print(glob(os.path.join(container_path, "*", ""), recursive = False))

    subfolders = [ f.path for f in os.scandir(container_path) if f.is_dir() ]
    # print(subfolders)
    return subfolders

def list_aurs_dir():
    container_path = os.path.join(BASE_PATH, C.aurs.container)
    subfolders = [ f.path for f in os.scandir(container_path) if f.is_dir() ]
    return subfolders

def clone_aur_packages():
    for aur in C.aurs.packages:
        container = os.path.join(BASE_PATH, C.aurs.container)
        url = f"https://aur.archlinux.org/{aur}.git"

        if not os.path.exists(os.path.join(container, aur)):
            subprocess.run(["git", "clone", "--depth=1", url], cwd=container)

def copy_build_packages(path):
    package_name = ""
    package_full_path = ""
    for file in os.listdir(path):
        if fnmatch.fnmatch(file, "*.pkg.tar.zst"):
            package_name = file
            package_full_path = os.path.join(path, file)
            break
    
    repo_path = get_repository_path(C.global_settings.repository)

    os.makedirs(repo_path, exist_ok=True)

    if os.path.exists(package_full_path):
        shutil.copy(package_full_path, repo_path)
    else:
        return

    subprocess.run(
        ["repo-add", "--new", "--remove", get_repository_db_name(C.global_settings.repository), package_name], 
        cwd=repo_path
        )
    

def rebuild(pkgname):
    if pkgname in list_pkgbuilds():
        rebuild_dir = os.path.join(BASE_PATH, C.pkgbuilds.container, pkgname)
    elif pkgname in C.aurs.packages:
        rebuild_dir = os.path.join(BASE_PATH, C.aurs.container, pkgname)
    else:
        raise RuntimeError("Rebuild package requested not exist!")
    
    subprocess.run(["pkgctl", "build", "-w", "1", "--clean", "--rebuild"], cwd=rebuild_dir)

def is_package_exist_in_db(pkgbuild):

    # for git packages, update pkgver first
    if fnmatch.fnmatch(pkgbuild, "*-git"):
        subprocess.run([makepkg_path, "-o", "-d"], cwd=pkgbuild)

    # extract package basename from PKGBUILD
    result = subprocess.run(
        [makepkg_path, "--packagelist"], 
        check=True, stdout=subprocess.PIPE, cwd=pkgbuild
        ).stdout.decode("utf-8")
    pkg = '-'.join(
        (os.path.splitext(os.path.basename(result))[0].split('-'))[:-1]
        )
    # print(pkg)

    # compare package basename to database
    repo_db = os.path.join(BASE_PATH, C.global_settings.repository)
    if os.path.isfile(repo_db):
        result = subprocess.run(
            "tar --exclude='*/*' -tf " + repo_db, 
            check=True, stdout=subprocess.PIPE, shell=True
            ).stdout.decode("utf-8")
        packages_db = [ f[:-1] for f in result.split("\n") if f != "" ]
        if pkg in packages_db:
            return True

    return False

def is_package_been_built(pkgbuild):
    result = subprocess.run(
    [makepkg_path, "--packagelist"], 
    check=True, stdout=subprocess.PIPE, cwd=pkgbuild
    ).stdout.decode("utf-8").split("\n")[0]
    
    if os.path.isfile(result):
        return True
    else:
        return False


def makepkg():
    for pkgbuild in list_pkgbuilds_dir() + list_aurs_dir():
        
        if is_package_exist_in_db(pkgbuild):
            print(f"!!!{pkgbuild} skipped build and copy!")
        elif is_package_been_built(pkgbuild):
            copy_build_packages(pkgbuild)
            print(f"!!!{pkgbuild} skipped build!")
        else:
            # subprocess.run(["pkgctl", "build", "-w", "1", "--clean"], cwd=pkgbuild)
            # subprocess.run(["paru", "--build", "--chroot", "--skipreview", "--clean"], cwd=pkgbuild)
            subprocess.run([makepkg_path, "--syncdeps", "--clean", "--noconfirm"], cwd=pkgbuild)
            copy_build_packages(pkgbuild)



