print("Testing Python environment...")
print("Python version:")
import sys
print(sys.version)

print("\nTesting imports...")
try:
    import numpy
    print("numpy imported successfully")
except ImportError as e:
    print(f"Error importing numpy: {e}")

try:
    from rank_bm25 import BM25Okapi
    print("rank_bm25 imported successfully")
except ImportError as e:
    print(f"Error importing rank_bm25: {e}")

try:
    import re
    print("re imported successfully")
except ImportError as e:
    print(f"Error importing re: {e}")

print("\nTest completed!")
