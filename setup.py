from setuptools import setup, find_packages

setup(
    name="ComfyUI-VideoDirCombiner",
    version="0.1.0",
    description="ComfyUI custom node for combining multiple videos from a directory",
    author="Dario Fernandez Torre",
    packages=find_packages(),
    install_requires=[
        "numpy",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)