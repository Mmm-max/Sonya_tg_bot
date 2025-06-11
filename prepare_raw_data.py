import re

with open("text.txt", "r") as file, open("data_2.json", "w") as output_file:
    output_file.write("[\n")
    for line in file.readlines():
        if line:
            line.strip()
            if line