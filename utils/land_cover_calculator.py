def read_land_dictionary(filename):
    with open(filename, 'r') as file:
        lines = file.read().split("\n")
    land_dict = {}
    for line in lines:
        tokens = line.split(" ")

        if len(tokens) <= 1:
            continue
        img_dict = {}
        #QUAD_TILE_CODE
        q_code = tokens[0]
        c = 0

        for t in tokens:
            if c == 0:
                c+=1
                continue
            covs = t.split(":")

            c_id = covs[0]
            c_pixels = int(covs[1])

            if c_id == '0':
                continue
            img_dict[c_id] = c_pixels

            c+=1
        #print(img_dict)
        v = list(img_dict.values())
        k = list(img_dict.keys())

        #print(k[v.index(max(v))])
        #print("******")

        land_dict[q_code] = int(k[v.index(max(v))])

    return land_dict