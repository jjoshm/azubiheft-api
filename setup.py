import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="azubiheftApi",
    version="0.0.1",
    author="Josh Münte",
    author_email="joshmuente@gmail.com",
    description="Azubiheft.de custom api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joshmuente/azubiheft-api",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
