import sys
assert len(sys.argv) == 2,f"{sys.argv[0]} must have parameter <input_file (csv)>"
assert str(sys.argv[1]).endswith(".csv"),"Input file must have .csv format"

inputfile = open(sys.argv[1],"r+")
lines = inputfile.read().split("\n")
inputfile.close()

outputfile = open(sys.argv[1],"w+")
for line in lines:
    line = line.replace(",",".")
    line = line.replace(";", ",")
    outputfile.write(line+"\n")

outputfile.close()
print("Done!")
