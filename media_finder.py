import os
import shutil
import time
import math
from datetime import datetime

TIMESTAMP_FORMAT = '%Y%m%d_%H%M%S'


def get_timestamp():
    current_time = time.time()
    timestamp = datetime.fromtimestamp(current_time)
    return timestamp.strftime(TIMESTAMP_FORMAT)


class MediaFile:
    FILE_SIZE_SUFFIX = ['B', 'KB', 'MB', 'GB']
    EXTENSIONS = ['PNG', 'JPG', 'JPEG', 'NEF', 'MOV', 'GIF', 'MP4']

    def __init__(self, abs_path):
        self.abs_path = abs_path
        self.basename = os.path.basename(abs_path)
        self.name, *self.extra_names, self.ext = self.basename.split('.')
        self.is_media = self.ext.upper() in self.EXTENSIONS
        self.is_name_standard = len(self.extra_names) == 0
        self.exists = True

    def delete(self):
        print(f'Removed {self.abs_path}')
        os.remove(self.abs_path)
        self.exists = False

    def move(self, dest_directory):
        print(f'Moved {self.abs_path}')
        new_path = os.path.join(dest_directory, self.basename)
        if (os.path.exists(new_path)):
            new_name = '_'.join([self.name, get_timestamp(), self.ext])
            dest_directory = os.path.join(dest_directory, new_name)
        shutil.move(self.abs_path, dest_directory)
        self.__init__(os.path.join(dest_directory, self.basename))

    def get_human_readable_size(self):
        size = os.path.getsize(self.abs_path)
        idx_suffix = 0
        while size > 1024 and idx_suffix < len(self.FILE_SIZE_SUFFIX):
            size /= 1024
            idx_suffix += 1

        return str(math.round(size, 2)) + self.FILE_SIZE_SUFFIX[idx_suffix]

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return self.name == other.name


class FileIterator:
    def __init__(self, when_file_is_found_fn):
        self.when_file_is_found_fn = when_file_is_found_fn

    def explore(self, directory):
        pass


class FileIteratorDfs(FileIterator):
    def explore(self, directory):
        for single_file in os.listdir(directory):
            abs_name = os.path.join(directory, single_file)
            if os.path.isdir(abs_name):
                self.explore(abs_name)
            else:
                self.when_file_is_found_fn(abs_name)


class Cleaner:
    def __init__(self, verbose=False):
        self.verbose = verbose
        pass

    def extract_files(self, directory_to_clean_from, directory_to_compare_with):
        files_to_clean = []
        files_to_check = []

        def add_file_to(container, filename):
            media_file = MediaFile(filename)
            if media_file.is_media:
                container.append(media_file)
            elif self.verbose:
                print(f'This is not a recognized media extension: {filename}')

        FileIteratorDfs(lambda filename: add_file_to(files_to_clean, filename)).explore(directory_to_clean_from)
        FileIteratorDfs(lambda filename: add_file_to(files_to_check, filename)).explore(directory_to_compare_with)

        files_to_clean.sort()
        files_to_check.sort()

        return (files_to_clean, files_to_check)

    def run(self, directory_to_clean_from, directory_to_compare_with, directory_to_save_all_files):
        files_to_clean, files_to_compare = self.extract_files(directory_to_clean_from, directory_to_compare_with)

        if self.verbose:
            print('Listing all files')
            print(f'files_to_clean_from ({len(files_to_clean)}):')
            for media_file in files_to_clean:
                print(f'{media_file.abs_name}: {media_file.get_human_readable_size()}')

            print(f'files_to_compare_with ({len(files_to_compare)}):')
            for media_file in files_to_compare:
                print(f'{media_file.abs_name}: {media_file.get_human_readable_size()}')

        self.move_and_clean(files_to_clean, files_to_compare, directory_to_save_all_files)

    def move_and_clean(self, files_to_clean, files_to_compare, directory_to_save_all_files):
        n_files_to_clean = len(files_to_clean)
        n_files_to_compare = len(files_to_compare)

        idx_clean = 0
        idx_compare = 0

        while idx_clean < n_files_to_clean and idx_compare < n_files_to_compare:
            if files_to_clean[idx_clean] == files_to_compare[idx_compare]:
                files_to_clean[idx_clean].delete()
                idx_clean += 1
            elif files_to_clean[idx_clean] < files_to_compare[idx_compare]:
                files_to_clean[idx_clean].move(directory_to_save_all_files)
                idx_clean += 1
            else:
                idx_compare += 1

        while idx_clean < n_files_to_clean:
            files_to_clean[idx_clean].move(directory_to_save_all_files)
            idx_clean += 1


if __name__ == '__main__':
    directory_to_clean_from = '/Users/berthin/Pictures/Photos Library.photoslibrary/Masters'
    directory_to_compare_with = '/Users/berthin/fotos Nikon'
    directory_to_save_all_files = '/Users/berthin/photos-recovered'
    vacuum = Cleaner()
    vacuum.run(directory_to_clean_from, directory_to_compare_with, directory_to_save_all_files)
