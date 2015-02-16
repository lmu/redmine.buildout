#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import os
import subprocess
import sys


if __name__ == "__main__":
    if len(sys.argv) > 2:
        input_file_name = sys.argv[1]
        input_file_path = os.path.abspath(input_file_name)
        output_file_name = sys.argv[2]
        output_file_path = os.path.abspath(output_file_name)

        encoding_ckeck = ['file', '-b', '--mime-encoding', input_file_path]
        print('Encoding Check command: ' + ' '.join(encoding_ckeck))
        input_file_encoding = subprocess.check_output(encoding_ckeck)

        print('Input File: ' + input_file_name)
        print('Input File Encoding: ' + input_file_encoding)
        print('Output File: ' + output_file_name)

        if input_file_encoding.lower() != 'utf-8':
            with io.open(input_file_name, mode='r', encoding=input_file_encoding) as input_file:
                with io.open(output_file_name, mode='w', encoding='utf-8') as output_file:
                    for line in input_file:
                        output_file.write(unicode(line))
