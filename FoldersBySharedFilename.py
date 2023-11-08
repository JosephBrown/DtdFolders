import argparse, os, os.path
import shutil
from datetime import datetime
import difflib
"""
Nextcloud is a nice place to store images.

10,000 images in one folder will bring its performance down to its knees, or knock it out pretty good.
300-500 files in any given folder degrades its performance somewhat for files at the bottom of the list(s).

Nextcloud generates thumbnail images on the fly and does so for all image files in a given folder. 
It doesn't appear to manage a cache of generated thumbnails, as some image managers do, opting 
instead to generate them on the fly as needed. Folders containing over 300 images can impact its performance. 

If you have groups of files similarly named, this script can relocate those files to folders sharing similar names.

It does it in a multi phase set of comparisons.

Fist sorting all filnames and comparing them for similarity and generates a list of possible folder names.

Second it then compares each filename to the list to find the best match found for each file, 
which is kinda redudant yet seems to work well.
"""

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
        
        parser.add_argument("-c", "--cut_off",
                            dest="cutoff",
                            default="0.4",
                            type='float',
                            help="fuzzy match 0.4 default, values are between 0-1 where 0.01 is super fuzzy and 0.99 virtually exact matchs only.",
                            )
        
        parser.add_argument("-m", "--min_folder_length",
                            dest="minlen",
                            default='4',
                            type='int',
                            help="Minimum folder name length.",
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
        self.testing = args.test
        self.minlen = args.minlen
        self.cutoff = args.cutoff

        self.src_listing = {}

    def load_src_list(self, src_tree=None):
        if src_tree is None:
            src_tree = self.src_tree
        for root, dirs, files in os.walk(src_tree):
            self.src_listing[root]=files
            for folder in dirs:
                self.load_src_list(folder)

    def single_list(self):
        self.filelist = []
        for k, v in self.src_listing.items():
            self.filelist += v
        self.filelist.sort()

    def find_matches(self):
        self.match_list = []
        for x in range(1, len(self.filelist)):
            fname1 = os.path.splitext(self.filelist[x-1])[0]
            fname2 = os.path.splitext(self.filelist[x])[0]
            match = difflib.SequenceMatcher(
                None, fname1, fname2,autojunk=False
                ).find_longest_match(0,len(fname1),0,len(fname2))
            if match and match.size:
                ms = fname1[match.a:match.a + match.size]
                while ms and ms[-1] in "0123456789!@#$%^&*()-=_+[]{};:'\"\\/":
                    ms = ms[:-1]
                if len(ms) >= self.minlen and ms not in self.match_list:
                    self.match_list.append(ms)
        mc = count = 0
        used_matches = {}
        for fname in self.filelist:
            mtch = difflib.get_close_matches(fname, self.match_list, n=4, cutoff=0.4)
            if not mtch:
                count += 1
                print(fname)
            else:
                print(fname, mtch)
                mc += 1
                if mtch[0] not in used_matches:
                    used_matches[mtch[0]] = 1
                else:
                    used_matches[mtch[0]] += 1
        print('unused matches', [i for i in self.match_list if i not in used_matches])              
        print(mc, count)
    def return_match(self, filename):
        mtch = difflib.get_close_matches(filename, self.match_list, n=4, cutoff=self.cutoff)
        if mtch:
            return mtch[0]
        
    def mkdir(self, path):
        parent = os.path.dirname( path )
        if not os.path.isdir( parent ):
            self.mkdir( parent )
        os.mkdir( path )
    
    def operate(self, fullpath):
        filename = os.path.basename(fullpath)
        dirname = self.return_match(filename)
        if dirname is None:
            newbasepath = self.dest_tree
        else:
            newbasepath = os.path.join(self.dest_tree, dirname)
        if not newbasepath in self.folders_count:
            self.folders_count[newbasepath] = 1
        else:
            self.folders_count[newbasepath] += 1
        newfullpath = os.path.join(newbasepath, filename)
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
        for folder, files in self.src_listing.items():
            for filename in files:
                fullpath = os.path.join(folder,filename)
                dstfldr = self.operate( fullpath )
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
    m.single_list()
    m.find_matches()
    m.relocate_files()
