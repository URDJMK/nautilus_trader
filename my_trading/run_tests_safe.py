import sys
import os
import site
import pytest
import subprocess
import glob

def main():
    print("running my_trading/run_tests_safe.py...")
    # Get current working directory
    cwd = os.getcwd()
    
    # 1. Force site-packages to be BEFORE the current directory
    # This prevents 'import nautilus_trader' from picking up the uncompiled local folder
    # but still allows 'import my_trading' to work (eventually)
    venv_python = sys.executable
    
    # 1. Compile Cython extension to build/lib (Clean Build)
    print("Compiling Cython extension to build/lib...")
    # Use standard build which includes build_py and build_ext
    cmd = [venv_python, "my_trading/setup.py", "build"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Compilation Failed!")
        print(result.stderr)
        sys.exit(1)
        
    print("Compilation Successful.")

    # 2. Add build directory to sys.path so tests can find the compiled modules
    # Find the build/lib directory (it has platform suffix)
    build_lib_dirs = glob.glob("build/lib.*")
    if not build_lib_dirs:
        print("Error: Could not find build/lib directory.")
        sys.exit(1)
        
    build_lib = os.path.abspath(build_lib_dirs[0])
    print(f"Adding build directory to sys.path: {build_lib}")
    
    build_lib = os.path.abspath(build_lib_dirs[0])
    print(f"Adding build directory to sys.path: {build_lib}")
    
    # Prepend build_lib to sys.path
    sys.path.insert(0, build_lib)
    
    # CRITICAL: Remove current working directory from sys.path to prevent 
    # importing uncompiled 'nautilus_trader' from source
    cwd = os.getcwd()
    if cwd in sys.path:
        # sys.path.remove(cwd)
        # print(f"Removed CWD {cwd} from sys.path to avoid shadowing installed packages.")
        pass

    # Verify we are importing the INSTALLED nautilus_trader
    try:
        import nautilus_trader
        print(f"Imported nautilus_trader: {nautilus_trader}")
        if hasattr(nautilus_trader, "__file__") and nautilus_trader.__file__:
             print(f"Location: {os.path.dirname(nautilus_trader.__file__)}")
    except ImportError as e:
        print(f"Failed to import nautilus_trader: {e}")
        # If we fail, it might be because we removed CWD but site-packages wasn't in path?
        # Usually site-packages is there.
    
    # 3. Run Pytest
    import pytest
    # We use --pyargs so pytest imports 'my_trading' to find tests, 
    # ensuring it uses the compiled package in build/lib, not the local source.
    return pytest.main(["--pyargs", "my_trading", "-v"])

if __name__ == "__main__":
    main()
