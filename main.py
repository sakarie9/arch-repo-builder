import src.build as build
import src.repo as repo

if __name__ == "__main__":
    repo.add_local_repo()
    build.clone_aur_packages()
    build.makepkg()
