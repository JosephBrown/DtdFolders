import argparse, os, os.path, shutil
from datetime import datetime

"""
move image stream to file system folders organized by date(d) grouping scheme
using either timestamp ctime, atime or mtime
folder structure depth is specified according to dated granularity of -hd (hierachy depth <month> default)

Currently copies from one folder and creates revised directory structure elsewhere.
Future version may re-arrange a trees (folder structure) in place, by moving files around vs copying.
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
                            help="/destination/file/path (should be different than source path)",
                            )
        
        parser.add_argument("-hd", "--hierachy_depth",
                            dest="depth",
                            choices=hierachy_depths,
                            default="month",
                            help="depth of dest_tree structure"
                            )
        
        parser.add_argument("-t", "--timestamp",
                            dest="timestamp",
                            default='ctime',
                            choices=timestamps,
                            help="atime = access, ctime = creation, mtime = last modified date",
                            )
        
        parser.add_argument('-o', '--test_only',
                            dest="test",
                            default=False,
                            action='store_true', 
                            help="doesn't actually copy files or make dirs")
        
        args = parser.parse_args()    
        self.src_tree = args.src
        self.dest_tree = args.dest
        self.depth = args.depth
        self.depth_index = hierachy_depths.index(self.depth)
        self.timestamp = args.timestamp
        self.folders_count = {}
        self.testing = args.test

    def iterate_src(self, src_tree=""):
        """
        Find each file in source directory yeild: full path and stat.
        """
        if src_tree == "":
            src_tree = self.src_tree

        for filename in os.listdir(src_tree):
            fullpath = os.path.join( self.src_tree, filename )
            stat = os.stat(fullpath)
            
            if os.path.isdir(fullpath):
                self.iterate_src( fullpath )

            yield [fullpath, stat ]

    def mkdir(self, path):
        parent = os.path.dirname( path )
        if not os.path.isdir( parent ):
            self.mkdir( parent )
        os.mkdir( path )
    
    def copy_to_dst(self, fullpath, stat):
        if self.timestamp == 'ctime':
            ts = datetime.fromtimestamp( stat.st_ctime )
        elif self.timestamp == 'atime':
            ts = datetime.fromtimestamp( stat.st_atime )
        elif self.timestamp == 'mtime':
            ts = datetime.fromtimestamp( stat.st_mtime )
        year, month, day = ts.year, ts.month, ts.day 
        # newpath = "{:04d}/{:02d}".format( ts.year, ts.month )
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
        if not self.testing:
            if not os.path.isdir( newbasepath ):
                self.mkdir( newbasepath )
            newfullpath = os.path.join( newbasepath, os.path.basename( fullpath ))
            if self.copy:
                shutil.copyfile( fullpath, newfullpath)
            else:
                os.rename( fullpath, newfullpath)
                old_dirname = os.path.dirname(fullpath)
        return newbasepath
    
    def relocate_files(self):
        count = 0
        for fullpath, stat in self.iterate_src():
            dstfldr = self.copy_to_dst( fullpath, stat )
            count +=1
            # basename = os.path.basename(fullpath)
            
            print( "folder: {} count: {}  ".format(dstfldr, count), end='\r' )
        max_size = max(self.folders_count.values())
        print('\n  max folder size:', max_size)
        for k, v in self.folders_count.items():
            if v == max_size:
                print(k)

if __name__=='__main__':
    m = main()
    m.relocate_files()
