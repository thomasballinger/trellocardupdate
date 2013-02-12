import tempfile
import subprocess
import os

# mostly from
# http://stackoverflow.com/questions/13168083/python-raw-input-replacement-that-uses-a-configurable-text-editor/13168243#13168243

def edit(data=''):
    fdes = -1
    path = None
    fp = None
    try:
        fdes, path = tempfile.mkstemp(suffix='.txt', text=True)
        fp = os.fdopen(fdes, 'w+')
        fdes = -1
        fp.write(data)
        fp.close()
        fp = None
#TODO understand why making sure fp gets cleaned up is a good idea - what's not good enough about close?

#TODO reach inside .gitconfig for people that don't set these like they should
        editor = (os.environ.get('VISUAL') or
                  os.environ.get('EDITOR') or
                  'nano')
        subprocess.check_call([editor, path])

        fp = open(path, 'r')
        return fp.read()
    finally:
        if fp is not None:
            fp.close()
        elif fdes >= 0:
            os.close(fdes)
        if path is not None:
            try:
                os.unlink(path)
            except OSError:
                pass
