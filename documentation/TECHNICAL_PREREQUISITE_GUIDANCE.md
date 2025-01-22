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

### Issues: llama-cpp-python
In order for llama-cpp-python to use cuda, you must compile it.

Poetry does not seem to offer a formalism for compiling wheels. You can, however, shell in and compile and force-reinstall.

```
poetry shell
```

```
CUDACXX=/home/core/local/cuda-12.2/bin/nvcc NVCC_PREPEND_FLAGS='-ccbin /usr/bin/g++-12' CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=all-major -DCMAKE_C_COMPILER=/usr/bin/gcc-12 -DCMAKE_CXX_COMPILER=/usr/bin/g++-12"  FORCE_CMAKE=1 \
pip install llama-cpp-python==0.3.6 --no-cache-dir --force-reinstall --upgrade
```

### Issues: torch
A bug in the current version of torch:

```
ImportError: /home/core/llm/tyrell/.venv/lib/python3.12/site-packages/torch/lib/../../nvidia/cusparse/lib/libcusparse.so.12: undefined symbol: __nvJitLinkComplete_12_4, version libnvJitLink.so.12
```
Requires you to install the nightly build of torch.

```
python -m pip uninstall torch
python -m pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu121

### Avoiding rebuilds constantly

You can reference these built wheels in your poetry.lock file. This will prevent poetry from rebuilding the wheels every time you install.

```
my-package = { file = "path/to/wheel.whl" }
```
