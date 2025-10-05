from setuptools import setup, find_packages

setup(
    name='embdloader',
    version='1.0.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'boto3',
        'asyncpg',
        'pgvector',
        'pandas',
        'pydantic',
        'tenacity',
        'google-generativeai',
        'sentence-transformers',
        'faiss-cpu',
        'chromadb',
        'openai',
        'scikit-learn',
        'numpy',
    ],
    description='Embedding Loader Package for CSV to Vector Stores',
    author='Your Name',
    license='MIT',
)
