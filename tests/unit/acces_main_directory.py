import os
import pkgutil
import importlib
import sys

# Get the absolute path of the src directory
src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src')

# Add the src directory to the system path
sys.path.append(src_dir)

# Import all modules in the src directory
for (module_loader, name, ispkg) in pkgutil.iter_modules([src_dir]):
    importlib.import_module(name)