from Lauwersoog_scripts.Helper_funcs import add_randome_data
import sqlite3
import os

file_path = os.path.abspath('C:\LDST')

connect = sqlite3.connect(os.path.join(file_path, 'config', 'Database.db'))
add_randome_data(10)