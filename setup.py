import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="azubiheftApi",
    version="0.0.94",
    author="Leon Kohlhaussen",
    author_email="kohli.leon@gmail.com",
    description="Azubiheft.de custom api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leonkohli/azubiheft-api",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "datetime",
        "bs4",
        "beautifulsoup4",
        "requests",
    ],
)
