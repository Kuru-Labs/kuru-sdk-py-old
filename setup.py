from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kuru-sdk",
    version="0.2.8",
    author="Kuru Labs",
    author_email="tech@kurulabs.xyz",
    description="Python SDK for Kuru's Central Limit Orderbook (CLOB)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kuru/kuru-py-sdk",
    packages=find_packages(),
    package_data={
        'kuru_sdk': ['abi/*.json'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "web3[async]>=7.6.0",
        "eth-typing>=3.5.0",
        "eth-utils>=2.3.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.1",
        "python-socketio[client]>=5.11.0"
    ],
)