from setuptools import setup, find_packages

setup(
    name='nuwa',
    version='0.2.4',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'nuwa=nuwa.src.utils.cli:main',
        ],
    },
    # 依赖项可以在这里列出，例如：
    install_requires=[
        'numpy',
        'torch'
    ],
    # 其他元数据，例如作者、描述、许可证等...
)


