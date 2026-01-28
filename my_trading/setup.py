from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
import numpy
import os
import glob

def find_extensions(directory="my_trading"):
    """
    Recursively find all .pyx files in the directory and return a list of Extensions.
    Example: my_trading/indicators/foo.pyx -> my_trading.indicators.foo
    """
    extensions = []
    
    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".pyx"):
                # "my_trading/indicators/foo.pyx"
                abs_path = os.path.join(root, file)
                
                # "my_trading.indicators.foo"
                rel_path = os.path.relpath(abs_path, start=".")
                module_name = rel_path.replace(os.sep, ".")[:-4]  # remove .pyx
                
                print(f"Found Cython extension: {module_name}")
                
                ext = Extension(
                    name=module_name,
                    sources=[abs_path],
                    include_dirs=[numpy.get_include(), "."],
                    define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
                )
                extensions.append(ext)
                
    return extensions

# Find/Register all extensions automatically
if __name__ == "__main__":
    extensions = find_extensions("my_trading")

    setup(
        name="my_trading",
        version="0.1.0",
        packages=find_packages(include=["my_trading", "my_trading.*"]),
        # Use 'build/src' for intermediate files (.cpp, .html)
        # The .so files will go to build/lib via command line args (or default build behavior)
        ext_modules=cythonize(
            extensions,
            compiler_directives={
                "language_level": "3",
                "boundscheck": False,
                "wraparound": False,
                "initializedcheck": False,
                "nonecheck": False,
                "cdivision": True,
            },
            annotate=True,   # Generates HTML
            nthreads=4,      
            build_dir="build/src", # Output .cpp and .html here
        ),
        zip_safe=False,
    )
