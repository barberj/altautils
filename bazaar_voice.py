# bazaar_voice
import os
import subprocess

location = r'//greco/ALTA/Translation/62500/62835/1-UGC/14 - Merged Translations/'
def convert_unicode_to_native():
    """
    Turn the unicode files back to the native character set
    """

    files = os.listdir(location)
    for unicodefile in files:
        native = 'native%s' % unicodefile
        infile = os.path.join(location,unicodefile)
        outfile = os.path.join(location,native)
        subprocess.call(["native2ascii.exe","-encoding","utf8","-reverse",infile, outfile])
