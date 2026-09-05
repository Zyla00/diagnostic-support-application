import importlib

def check_package(name):
    try:
        return importlib.import_module(name)
    except ImportError:
        print(f"❌ {name} not installed")
        return None

# Check TensorFlow
tf = check_package("tensorflow")
if tf:
    print(f"✅ TensorFlow version: {tf.__version__}")
    print("CUDA Available:", tf.test.is_built_with_cuda())
    print("GPU Devices:", tf.config.list_physical_devices("GPU"))

# Check PyTorch
torch = check_package("torch")
if torch:
    print(f"\n✅ PyTorch version: {torch.__version__}")
    print("CUDA Available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print(f"Device count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.get_device_name(0)}")

# Check JAX
jax = check_package("jax")
if jax:
    print(f"\n✅ JAX version: {jax.__version__}")
    print("JAX Devices:", jax.devices())

# Check GPUtil (optional)
gputil = check_package("GPUtil")
if gputil:
    print("\n✅ GPUtil output:")
    for gpu in gputil.getGPUs():
        print(f" - {gpu.name}: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB")

# Extra: Use tabulate if available
tabulate = check_package("tabulate")
if tabulate and torch and torch.cuda.is_available():
    from tabulate import tabulate
    data = [[
        i,
        torch.cuda.get_device_name(i),
        f"{torch.cuda.memory_allocated(i) / 1024**2:.1f} MB",
        f"{torch.cuda.memory_reserved(i) / 1024**2:.1f} MB"
    ] for i in range(torch.cuda.device_count())]
    print("\n📊 GPU Memory Usage (PyTorch):")
    print(tabulate(data, headers=["ID", "Name", "Allocated", "Reserved"]))

from bitsandbytes.nn import Linear8bitLt
import torch

x = torch.randn(1, 4).cuda()
layer = Linear8bitLt(4, 4).cuda()
y = layer(x)
print("✅ bitsandbytes works with CUDA!")
