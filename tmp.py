import os, json
d = {
    11:[11,12,21]
}
with open('tmp', 'w+') as fout:
    json.dump(d, fout)