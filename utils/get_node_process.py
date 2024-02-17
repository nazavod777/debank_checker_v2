import subprocess

node_process = subprocess.Popen(args=['node', 'js/main.js'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                universal_newlines=True, )
