import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="json_rag_ast",  # Replace with your package name
    version="0.0.1",       # Initial version
    author="Paul Spedding",    # Replace with your name
    author_email="paulspedding@duck.com",  # Replace with your email
    description="A tool for producing JSON nested AST's and recreating JSON to .py which I made for RAG ingestion.", # Short description
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/superpauly/json-rag-ast-generator",  # Replace with your repo URL
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Replace if using a different license
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6', # Minimum Python version
    install_requires=[       # List your dependencies
        # e.g., "requests >= 2.20",
    ],
)