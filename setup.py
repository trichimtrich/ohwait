from distutils.core import setup, Extension


def main():
    setup(
        name="ohwait",
        version="0.0.1",
        description="",
        author="trichimtrich",
        author_email="trichimtrich@gmail.com",
        packages=["ohwait"],
        package_dir={"ohwait": "lib/ohwait"},
        ext_modules=[Extension("ohwait._ohno", ["src/_ohno.c"])],
    )


if __name__ == "__main__":
    main()
