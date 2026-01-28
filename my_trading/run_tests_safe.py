import sys
import os
import site
import pytest

def main():
    print("running my_trading/run_tests_safe.py...")
    # Get current working directory
    cwd = os.getcwd()
    
    # 1. Force site-packages to be BEFORE the current directory
    # This prevents 'import nautilus_trader' from picking up the uncompiled local folder
    # but still allows 'import my_trading' to work (eventually)
    
    # Get site-packages directories
    site_pkgs = site.getsitepackages()
    
    # Reconstruct sys.path: site_packages + others + cwd
    new_path = []
    
    # Add site packages first
    for p in site_pkgs:
        if p not in new_path:
            new_path.append(p)
            
    # Add existing paths (excluding cwd and site packages)
    for p in sys.path:
        if p != cwd and p not in site_pkgs and p != "":
            new_path.append(p)
            
    # Add CWD last (so we can still find my_trading)
    new_path.append(cwd)
    
    sys.path = new_path
    
    print(f"Modified sys.path order: {sys.path[:3]} ... {sys.path[-1]}")

    # 2. Verify we are importing the INSTALLED nautilus_trader
    try:
        import nautilus_trader
        print(f"Imported nautilus_trader from: {os.path.dirname(nautilus_trader.__file__)}")
    except ImportError as e:
        print(f"Failed to import nautilus_trader: {e}")
        sys.exit(1)

    # 3. Run Pytest
    retcode = pytest.main(["my_trading/tests/test_future_bb.py", "-v"])
    sys.exit(retcode)

if __name__ == "__main__":
    main()
