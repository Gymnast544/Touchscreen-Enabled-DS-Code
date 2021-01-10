original = "openingmenu.dsm"
new = "parsedopeningmenu.dsm"


def parseFile(originalfile, newfile):
    f = open(originalfile, "r")
    g = open(newfile, "w")
    for line in f:
        linesplit = line.split()
        if len(linesplit)>=2 and "LOOP" == line.split()[0]:
            for i in range(int(line.split()[2])):
                g.write(line.split()[1])
        elif "DELAY" in line:
            numframes = int(line.split(" ")[1])
            for i in range(numframes):
                g.write("\n")
        elif "PWR" in line:
            g.write("Z");
        else:
            g.write(line)
    g.close()
    f.close()
    print("Successfully parsed "+originalfile+" destination file is "+newfile)
