import os
import csv

def extract_files_to_csv(directory_path, csv_filename):
    """
    Extracts a list of files from the specified directory and writes them into a CSV file.

    Parameters:
        directory_path (str): The path to the directory.
        csv_filename (str): The name of the CSV file to write.
    """
    # List all entries in the directory
    entries = os.listdir(directory_path)
    
    # Filter out directories, keep only files
    files_only = [entry for entry in entries if os.path.isfile(os.path.join(directory_path, entry))]
    
    # Write the list of files to a CSV file
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Optionally, write a header
        csvwriter.writerow(['Filename'])
        for filename in files_only:
            csvwriter.writerow([f'{filename.replace(".mp3","")},'])

# Example usage
if __name__ == '__main__':
    directory = "./mp3"  # Replace with your directory path
    csv_output = './file_list.csv'          # The CSV file to write

    extract_files_to_csv(directory, csv_output)
    print(f"File list extracted to {csv_output}")