

f = open("testTAS.txt", "r")
g = open("testTAS.dsm", "w")
for line in f:
    if "DELAY" in line:
        numframes = int(line.split(" ")[1])
        for i in range(numframes):
            g.write("\n")
    else:
        g.write(line)
g.close()
f.close()
