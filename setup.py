from setuptools import setup
from setuptools_rust import Binding, RustExtension
import os
import sys

# Добавляем версию в одном месте для удобного обновления
VERSION = "0.1.1"
PACKAGE_NAME = "v-queue-python"

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    packages=[],
    description="Python bindings for v-queue with support for Individual model",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/ваша-организация/v-queue-python",
    rust_extensions=[
        RustExtension(
            "vqueue", 
            path="Cargo.toml",
            binding=Binding.PyO3
        )
    ],
    setup_requires=["setuptools-rust"],
    install_requires=[],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Rust",
        "Topic :: Software Development :: Libraries",
    ],
    zip_safe=False,
)
