from setuptools import setup, find_packages

setup(
    name="rag_medical_chatbot",
    version="0.1.0",
    author="Shayan Banerjee",
    author_email="shayanbanerjee96@gmail.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "langchain<1.0",
        "jupyterlab",
        "jupyter",
        "flask==3.1.1",
        "python-dotenv==1.1.0",
        "sentence-transformers==4.1.0",
        "pypdf==5.6.1",
        "langchain-pinecone<1.0",
        "langchain-openai<1.0",
        "langchain-community<1.0",
    ],
)
