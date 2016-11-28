from client import find_by_filename

def example_search_for_passwords():
    # List of filenames to look for
    filenames = [
        'vault',  # Password vaults
        'pass',   # password files
        'factor', # 2 Factor Codes
        'auth',   # Auth files
        'keychain'# Keychains
    ]

    paths = []
    for filename in filenames:
        paths += find_by_filename(filename)
    return paths

if __name__=="__main__":
    print(example_search_for_passwords())