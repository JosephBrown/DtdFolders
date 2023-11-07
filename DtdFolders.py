import argparse, os, os.path
import shutil
from datetime import datetime

"""
Nextcloud is a nice place to store images.  10,000 images in one folder will bring its performance down to its knees, or knock it flat out.
300-500 files in any given folder degrades its performance somewhat for files at the bottom of the list(s).

This script reorganizes directory structures based on file creation time(ctime), modified (mtime), or last access time (atime).

move image/file stream into file system folders organized by date(d) grouping scheme
using either timestamp ctime, atime or mtime

folder structure depth is specified according to dated granularity of -hd (hierachy depth <month> default)

XXXXCurrently copies from one folder and creates revised directory structure elsewhere.
Next version may re-arrange a tree (folder structure) in place, if src and dest paths are the same.
"""

hierachy_depths = ['year', 'month', 'day', 'hour', 'minute', 'second']
timestamps = ['atime', 'ctime', 'mtime']

class main(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--source_tree",
                            dest="src",
                            default="/mnt/Images",
                            )
              
        parser.add_argument("-d", "--destination_tree",
                            dest="dest",
                            default="/mnt/test",
                            help="/destination/file/path",
                            )
        
        parser.add_argument("-hd", "--hierachy_depth",
                            dest="depth",
                            choices=hierachy_depths,
                            default="month",
                            help="depth of dest_tree structure"
                            )
        
        parser.add_argument("-t", "--timestamp_type",
                            dest="timestamp",
                            default='ctime',
                            choices=timestamps,
                            help="atime = access, ctime = creation, mtime = last modified date",
                            )
        
        parser.add_argument('-o', '--only_test',
                            dest="test",
                            default=False,
                            action='store_true', 
                            help="Doesn't copy files or make dirs, only reports resulting folder scheme max file count")
        
        self.operation='copy'
        self.folders_count = {}
        args = parser.parse_args()    
        self.src_tree = args.src
        self.dest_tree = args.dest
        if self.src_tree == self.dest_tree:
            self.operation='move'
        self.depth = args.depth
        self.depth_index = hierachy_depths.index(self.depth)
        self.timestamp = args.timestamp
        self.testing = args.test

        self.src_listing = {}

    def load_src_list(self, src_tree=None):
        if src_tree is None:
            src_tree = self.src_tree
        for root, dirs, files in os.walk(src_tree):
            self.src_listing[root]=files
            for folder in dirs:
                self.load_src_list(folder)

    def iterate_src(self, src_tree=None):
        """
        Find each file in source directory yeild: full path and stat.
        """
        if src_tree is None:
            src_tree = self.src_tree
        for filename in os.listdir(src_tree):
            fullpath = os.path.join( self.src_tree, filename )
            stat = os.stat(fullpath)
            if os.path.isdir(fullpath):
                self.iterate_src( fullpath )
            yield [fullpath, stat ]

    def iterate_src(self, src_tree=None):
        """
        traverse src_listing
        """
        for folder, files in self.src_listing.items():
            for name in files:
                fullpath = os.path.join(folder, name)
                stat = os.stat(fullpath)
                yield [fullpath, stat ]

    def mkdir(self, path):
        parent = os.path.dirname( path )
        if not os.path.isdir( parent ):
            self.mkdir( parent )
        os.mkdir( path )
    
    def operate(self, fullpath, stat):
        if self.timestamp == 'ctime':
            ts = datetime.fromtimestamp( stat.st_ctime )
        elif self.timestamp == 'atime':
            ts = datetime.fromtimestamp( stat.st_atime )
        elif self.timestamp == 'mtime':
            ts = datetime.fromtimestamp( stat.st_mtime )
        # newpath = f"{ts.year:04d}/{ts.month:02d}/..."
        yr_format = "{:04d}"
        dt_format = "{:02d}"
        fmt_arry = [yr_format,] + [ dt_format, ] * self.depth_index
        np_format = '/'.join( fmt_arry )
        newpath= np_format.format( ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second )
        newbasepath = os.path.join( self.dest_tree, newpath )
        if not newbasepath in self.folders_count:
            self.folders_count[newbasepath] = 1
        else:
            self.folders_count[newbasepath] += 1
        newfullpath = os.path.join( newbasepath, os.path.basename( fullpath ))
        if not self.testing:
            if self.operation == "copy":
                if not os.path.isdir( newbasepath ):
                    self.mkdir( newbasepath )
                shutil.copy2( fullpath, newfullpath )
            elif self.operation == "move":
                os.renames( fullpath, newfullpath)
        return newbasepath
    
    def relocate_files(self):
        count = 0
        for fullpath, stat in self.iterate_src():
            dstfldr = self.operate( fullpath, stat )
            count +=1
            print( f"Processing folder: {dstfldr} total files: {count}  ", end='\r' )
        max_size = max(self.folders_count.values())
        print('\r\n  Max size folder(s):')
        for k, v in self.folders_count.items():
            if v == max_size:
                print(f"  {v} files in: {k}")

if __name__=='__main__':
    m = main()
    m.load_src_list()
    m.relocate_files()
