import src.build as build

if __name__ == "__main__":
    build.clone_aur_packages()
    build.makepkg()
