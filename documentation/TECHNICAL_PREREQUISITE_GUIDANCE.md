# Technical Guidance
Deckard is a python suite that is designed to run on CUDA in Linux.

## Hardware


## Software

### Nvidia drivers, etc.
From bare metal, many nvidia drivers

https://medium.com/@metechsolutions/setup-nvidia-gpu-in-ubuntu-22-04-for-llm-e181e473a3f4

### Torch
https://pytorch.org/

### Python Virtual Environment Tools
venv
poetry

### llama-cpp-python
In order for llama-cpp-python to use cuda, you must compile it.

Poetry does not seem to offer a formalism for compiling wheels. You can, however, shell in and compile and force-reinstall.

```
poetry shell
```

```
CUDACXX=/home/core/local/cuda-12.2/bin/nvcc NVCC_PREPEND_FLAGS='-ccbin /usr/bin/g++-12' CMAKE_ARGS="-DLLAMA_CUBLAS=on -DCMAKE_CUDA_ARCHITECTURES=all-major -DCMAKE_C_COMPILER=/usr/bin/gcc-12 -DCMAKE_CXX_COMPILER=/usr/bin/g++-12"  FORCE_CMAKE=1 \
pip install llama-cpp-python==0.2.47 --no-cache-dir --force-reinstall --upgrade
```
