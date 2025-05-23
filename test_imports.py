def test_imports():
    print("Testing imports...\n")
    
    def check_import(module_name, import_path=None, attr=None):
        try:
            if import_path:
                # Handle from ... import ... style imports
                parts = import_path.split('.')
                module = __import__(parts[0])
                for part in parts[1:]:
                    module = getattr(module, part)
                print(f"✓ {import_path}")
                return True
            else:
                # Handle regular imports
                module = __import__(module_name)
                version = getattr(module, attr, 'version not found') if attr else 'imported successfully'
                print(f"✓ {module_name} {version}")
                return True
        except ImportError as e:
            print(f"✗ {import_path or module_name}: {e}")
            return False
    
    # Test core packages
    check_import("crewai", attr="__version__")
    check_import("langchain", attr="__version__")
    check_import("langchain_community.llms", "langchain_community.llms.OpenAI")
    
    # Test Google Cloud packages
    try:
        from google.cloud import bigquery
        print("✓ google.cloud.bigquery")
    except (ImportError, ModuleNotFoundError) as e:
        print(f"✗ google.cloud.bigquery: {e}")
    
    try:
        import google.auth
        print("✓ google.auth")
    except (ImportError, ModuleNotFoundError) as e:
        print(f"✗ google.auth: {e}")
    
    # Test other packages
    check_import("playwright.sync_api", "playwright.sync_api.sync_playwright")
    check_import("bs4", "bs4.BeautifulSoup")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_imports()
