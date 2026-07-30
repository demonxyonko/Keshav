from setuptools import find_packages, setup


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Keshav",
    version="0.1.0",
    author="Ricky",
    description="A local-first desktop AI assistant with chat, vision, tools, and live voice",
    url="https://github.com/demonxyonko/Keshav",
    packages=find_packages(),
    install_requires=[
        "pydantic~=2.10.4",
        "openai>=1.58.1,<1.67.0",
        "tenacity~=9.0.0",
        "pyyaml~=6.0.2",
        "loguru~=0.7.3",
        "numpy",
        "datasets>=3.2,<3.5",
        "html2text~=2024.2.26",
        "gymnasium>=1.0,<1.2",
        "pillow>=10.4,<11.2",
        "browsergym~=0.14.3",
        "uvicorn~=0.34.0",
        "unidiff~=0.7.5",
        "browser-use~=0.13.7",
        "googlesearch-python~=1.3.0",
        "aiofiles~=24.1.0",
        "pydantic_core>=2.27.2,<2.28.0",
        "colorama~=0.4.6",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "keshav=main:main",
        ],
    },
)
