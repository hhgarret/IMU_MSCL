import sys, os
import time
f = os.popen("systemctl status myscript.service")
text = f.read()
print(text)


def get_last_modified_file(folder_path):
    """
    Finds the most recently modified file in a directory.

    Args:
        folder_path (str): The path to the directory to search.

    Returns:
        str: The path to the most recently modified file, or None if the directory is empty or an error occurs.
    """
    try:
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        if not files:
            return None
        
        last_modified_file = max(files, key=os.path.getmtime)
        return last_modified_file
    except FileNotFoundError:
         print(f"Error: Folder not found: {folder_path}")
         return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

lastfile = get_last_modified_file("/media/ncpa/4183-EE9B/UNIFIEDdata/")
print("Last modified file: ", lastfile)
modtime = os.path.getmtime(lastfile)
print("Modified at: ", time.ctime(modtime))
