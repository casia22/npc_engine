# https://stackoverflow.com/questions/71863714/packagenotfound-error-while-executing-exe-file-made-by-pyinstaller

pyinstaller --onefile --recursive-copy-metadata sentence_transformers  --hidden-import=pytorch --collect-data torch --copy-metadata torch --copy-metadata tqdm --copy-metadata regex  --copy-metadata requests --copy-metadata filelock --copy-metadata packaging  --copy-metadata numpy --copy-metadata tokenizers --copy-metadata importlib_metadata --copy-metadata huggingface-hub --hidden-import="sklearn.utils._cython_blas" --hidden-import="sklearn.neighbors.typedefs" --hidden-import="sklearn.neighbors.quad_tree" --hidden-import="sklearn.tree" --hidden-import="sklearn.tree._utils" ../../nuwa/src/nuwa.py &&dist/nuwa