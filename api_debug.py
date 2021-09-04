from Lauwersoog_scripts.Helper_funcs import add_randome_data
import sqlite3


connect = sqlite3.connect('Database.db')
add_randome_data(10)