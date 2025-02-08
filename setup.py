from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name="v-queue-python",
    version="0.1.0",
    description="Python bindings for v-queue",
    rust_extensions=[
        RustExtension(
            "vqueue", 
            path="Cargo.toml",
            binding=Binding.PyO3
        )
    ],
    setup_requires=["setuptools-rust"],
    python_requires=">=3.7",
    zip_safe=False
)
