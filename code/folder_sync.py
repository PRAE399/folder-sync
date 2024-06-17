import os, logging, time, shutil
from hashlib import sha256
from argparse import ArgumentParser

# ==== Comments === #
# Both MD5 and SHA256 could be used for this project, depending on the context.
# SHA256 was chosen for being more secure.
# MD50 could be used for a faster hash calculation.


# ==== Functions ==== #
def calculate_file_sha256(file_path):
    """Calculate the file SHA256 hash """
    chunk_size = 4096
    buffer_size = chunk_size * 10
    buffer = b""
    sha_hash = sha256()
    # calculate sha256
    with open(file_path, "rb") as file:
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            
            buffer += data
            if len(buffer) >= buffer_size:
                sha_hash.update(buffer)
                buffer = b"" 

        if buffer: 
            sha_hash.update(buffer)

    return sha_hash.hexdigest()


def get_folder_files(folder):
    """Get the files in a folder"""
    folder_files = {}

    for dirpath, _, filenames in os.walk(folder):
        for filename in filenames:
            source_file_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(source_file_path, folder)
            sha256_checksum = calculate_file_sha256(source_file_path)
            folder_files[relative_path] = sha256_checksum
    
    return folder_files


#sync_files
def sync_files(source, replica):
    """Syncronize files in a folder"""
    # get source and replica folder files
    source_files = get_folder_files(source)
    replica_files = get_folder_files(replica)

    # remove files in replica not in source folder
    for file_relative_path in replica_files:
        if file_relative_path not in source_files:
            os.remove(os.path.join(replica, file_relative_path))
            logging.info(f"Removed: {file_relative_path}")
            print(f"Removed: {file_relative_path}")

    # add files from source to replica
    for relative_path, source_sha256 in source_files.items():
        source_path = os.path.join(source, relative_path)
        replica_path = os.path.join(replica, relative_path)

        if relative_path not in replica_files:
            os.makedirs(os.path.dirname(replica_path), exist_ok=True)
            shutil.copy2(source_path, replica_path)
            logging.info(f"Copied: {relative_path}")
            print(f"Copied: {relative_path}")
        elif source_sha256 != replica_files[relative_path]:
            shutil.copy2(source_path, replica_path)
            logging.info(f"Updated: {relative_path}")
            print(f"Updated: {relative_path}")


def sync_folders(source, replica):
    """Syncronize folders and files between two locations"""
    # sync files
    sync_files(source, replica)

    # remove folders in replica not in source folder
    for root, dirs,_ in os.walk(replica):
        for dir_name in dirs:
            replica_folder = os.path.join(root, dir_name)
            source_folder = os.path.join(source, os.path.relpath(replica_folder, replica))
            if not os.path.exists(source_folder):
                shutil.rmtree(replica_folder)
                logging.info(f"Removed folder: {os.path.relpath(replica_folder, replica)}")
                print(f"Removed folder: {os.path.relpath(replica_folder, replica)}")

    # synchronize folders
    for root, dirs,_ in os.walk(source):
        for dir_name in dirs:
            source_folder = os.path.join(root, dir_name)
            replica_folder = os.path.join(replica, os.path.relpath(source_folder, source))
            if not os.path.exists(replica_folder):
                os.makedirs(replica_folder)
                logging.info(f"Created folder: {os.path.relpath(replica_folder, replica)}")
                print(f"Created folder: {os.path.relpath(replica_folder, replica)}")


def main():
    print("=== Starting File Synchronizer ===")
    # create log file
    parser = ArgumentParser(description="Synchronize two folders.")
    parser.add_argument("source", help="Source folder path")
    parser.add_argument("replica", help="Replica folder path")
    parser.add_argument("interval", type=int, help="Synchronization interval in seconds")
    parser.add_argument("logfile", help="Log file path")

    args = parser.parse_args()

    logging.basicConfig(filename=args.logfile, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # sync folder
    while True:
        try:
            sync_folders(args.source, args.replica)
        except Exception as e:
            logging.error(f"Error during synchronization: {e}")
            print(f"Error during synchronization: {e}")

        time.sleep(args.interval)
    


# ==== Run ==== #
if __name__ == "__main__":
    main()
