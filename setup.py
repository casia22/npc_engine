from setuptools import setup, find_packages

import nuwa

setup(
    name='nuwa',
    version=nuwa.__version__,
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
    package_data={
        # 确保你的包名正确
        'nuwa': ['./material/templates/template.zip'],
    },
    # 其他元数据，例如作者、描述、许可证等...
)


