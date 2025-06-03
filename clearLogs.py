import sys, os, shutil

def clearLogs(*dirsToClear: str) -> None:
    """
    Clears all files within the specified directories.
    Handles cases where directories don't exist.
    """
    for dirpath in dirsToClear:
        if os.path.exists(dirpath):
            if os.path.isdir(dirpath):
                print(f"Clearing directory: {dirpath}")
                for filename in os.listdir(dirpath):
                    filepath = os.path.join(dirpath, filename)
                    try:
                        if os.path.isfile(filepath) or os.path.islink(filepath):
                            os.remove(filepath)
                            print(f"  Removed file: {filepath}")
                        elif os.path.isdir(filepath):
                            # This will remove subdirectories and their contents
                            shutil.rmtree(filepath)
                            print(f"  Removed directory: {filepath}")
                    except OSError as e:
                        print(f"  Error removing {filepath}: {e}")
            else:
                print(f"Warning: Path is not a directory: {dirpath}")
        else:
            print(f"Directory not found: {dirpath}")

if __name__ == "__main__": 
    usageGuide = '''                             USAGE:
    Make sure your current working directory is 'nomad_test' 
    (or the parent of 'logs' and 'screenshots').

    After the script name, type "screenshots" to delete all screenshots, 
    "logs" to delete all logs, or "all" to delete both.'''
    if len(sys.argv) != 2:
        print(usageGuide)
        sys.exit(1) # Exit with an error code

    command = sys.argv[1].lower()

    if command == 'all':
        clearLogs('logs', 'screenshots')
    elif command == 'screenshots':
        clearLogs('screenshots')
    elif command == 'logs':
        clearLogs('logs')
    else:
        print(f"Error: Unknown command '{sys.argv[1]}'.")
        print(usageGuide)
        sys.exit(1) # Exit with an error code