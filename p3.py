import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import copy
import json


# we expected the node to contain the following items:
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons"]

# basic street name mapping:
mapping= { "St": "Street",
            "St.": "Street",
            "Rd":"Road",
            "Rd.":"Road",
            "Ave":"Avenue",
            "Blvd":"Boulevard",
            "Dr":"Drive",
            "Drv":"Drive",
            "Dv":"Drive",
            "Crt":"Court",
            "Ct":"Court",
            "Pl":"Place",
            "Sq":"Square",
            "La":"Lane",
            "Trl":"Trail",
            "Pkwy":"Parkway",
            "Pky":"Parkway",
            "Pwy":"Parkway",
            "Cmn":"Common",
            "Comm":"Common"
            }

# second mapping:
direction={ "S": "South",
            "N": "North",
            "E":"East",
            "W":"West",
            "St.":"Saint",
            "Ste":"Suite"
            }

# regular expression:
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
lower = re.compile(r'^([a-z]).*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
addr2 = re.compile(r'^\w+:\w+$')
addr3 = re.compile(r'^\w+(:\w+){2,}')

# create a new array to contain this following items:
CREATED = ["version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
# initialization of variate
    node = {}
    creat = {}
    node_nd = []
    tmp = {}
    tmp_relation={}
    tmp_array=[]

# find the following items(node/way/relation), and make the root node to standardizing
    if element.tag == "node" or element.tag == "way" or element.tag == "relation":
        for key in element.attrib.keys():
            if key in CREATED:
                creat[key] = element.attrib[key]
            elif key in ["lat", "lon"]:
                pos = []
                pos.append(float(element.attrib["lat"]))
                pos.append(float(element.attrib["lon"]))
                node["pos"] = pos
            else:
                node[key] = element.attrib[key]
                node["type_root"] = element.tag
        node["created"] = creat

        # iterate to find child:
        for elem in element.iter():
            if elem.tag == "tag":
                if problemchars.search(elem.attrib["k"]):
                    pass
                # if the item have the schema(addr:street) and the value be separated by 1 colon:
                elif addr2.match(elem.attrib["k"]):
                    if elem.attrib["k"].split(":")[0]  not in ["addr","tiger","source"]:
                        node[elem.attrib["k"]] = elem.attrib["v"]
                    elif elem.attrib["k"].split(":")[0]  in ["addr","tiger","source"]:
                        if elem.attrib["k"].split(":")[0] not in tmp.keys():
                            tmp[elem.attrib["k"].split(":")[0]] = {}


                        # deal with the "addr:street" and use the mapping value to change over-abbreviated names
                        if elem.attrib["k"] == "addr:street":
                            m = street_type_re.search(elem.attrib["v"])
                            changewords = mapping.keys()
                            if m:
                                m_ab = m.group()
                                if m_ab in changewords:
                                    name_full = mapping.get(m_ab)
                                    name_last = elem.attrib["v"][:m.start()] + name_full
                                    name_tmp = name_last.split(sep=" ")

                                    # use the direction value to change over-abbreviated names
                                    for num, i in enumerate(name_tmp):
                                        if i in direction.keys():
                                            name_tmp[num] = direction[i]
                                    name = " ".join(name_tmp)

                                else:
                                    name_tmp = elem.attrib["v"].split(sep=" ")
                                    for num, i in enumerate(name_tmp):
                                        if i in direction.keys():
                                            name_tmp[num] = direction[i]
                                    name = " ".join(name_tmp)

                            tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":")[1]] = copy.deepcopy(
                                name)

                        # deal with the "addr:postcode" , making the value just to contain five digits.
                        elif elem.attrib["k"] == "addr:postcode":
                            if re.match(r'^[0-9]+$', elem.attrib["v"]):
                                tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":")[1]] = elem.attrib[
                                    "v"]
                            elif re.match(r'^([0-9]+)-[0-9]+$', elem.attrib["v"]):
                                tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":")[1]] = re.match(
                                    r'^([0-9]+)-[0-9]+$', elem.attrib["v"]).group(1)
                            elif re.match(r'^[a-z]+([0-9]+)$', elem.attrib["v"]):
                                tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":")[1]] = re.match(
                                    r'^[a-z]+([0-9]+)$', elem.attrib["v"]).group(1)
                            elif re.match(r'.*([0-9]{5,5}).*', elem.attrib["v"]):
                                tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":")[1]] = re.match(
                                    r'.*([0-9]{5,5}).*', elem.attrib["v"]).group(1)
                            elif problemchars.search(elem.attrib["v"]):
                                pass

                        # deal with the "addr:housenumber" , making the value just to contain digit, hyphen and alphabet
                        elif elem.attrib["k"] == "addr:housenumber":
                            if re.match(r'^.*?([0-9-]+[a-zA-Z]?).*$', elem.attrib["v"]):
                                tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":")[1]] = re.match(r'^.*?([0-9-]+[a-zA-Z]?).*$', elem.attrib["v"]).group(1)
                            elif problemchars.search(elem.attrib["v"]):
                                pass
                            else:
                                tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":")[1]] = elem.attrib["v"]


                        else:
                            tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":")[1]] = elem.attrib["v"]


                # if the item have the schema(addr:street) and the value be separated by 2 colon:
                elif addr3.match(elem.attrib["k"]):
                    if elem.attrib["k"].split(":")[0]  not in ["addr","tiger","source"]:
                        node[elem.attrib["k"]] = elem.attrib["v"]
                    elif elem.attrib["k"].split(":")[0] in tmp.keys() and elem.attrib["k"].split(":")[0]  in ["addr","tiger","source"]:
                        tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":",maxsplit=1)[1]]= elem.attrib["v"]
                    else:
                        tmp[elem.attrib["k"].split(":")[0]] = {}
                        tmp[elem.attrib["k"].split(":")[0]][elem.attrib["k"].split(":",maxsplit=1)[1]] = elem.attrib["v"]

                # deal with the tag attribution : "source"
                elif elem.attrib["k"]=="source":
                    if "source" not in tmp.keys():
                        tmp["source"]={}
                    else:
                        pass

                    # "bing" should equal to "Bing", the extra information should be ignored in source ("http://www.census.gov/geo/www/tiger/")
                    if lower.match(elem.attrib["v"]):
                        tmp["source"]["position"]=elem.attrib["v"].replace(lower.match(elem.attrib["v"]).group(1), lower.match(elem.attrib["v"]).group(1).upper(), 1)
                    elif re.search(" \(http:.*", elem.attrib["v"]):
                        tmp["source"]["position"] = elem.attrib["v"].replace(re.search(" \(http:.*", elem.attrib["v"]).group(), "")
                    else:
                        tmp["source"]["position"] = elem.attrib["v"]

                # if the name have over-abbreviated value, we need to change it to fullname.
                elif elem.attrib["k"] == "name":
                    name_tmp = elem.attrib["v"].split(sep=" ")
                    for num, i in enumerate(name_tmp):
                        if i in direction.keys():
                            name_tmp[num] = direction[i]
                    name = " ".join(name_tmp)
                    node[elem.attrib["k"]] = name

                # if there have inconsistent Phone number, we need to transfer it to specific format("216-361-9160").
                elif elem.attrib["k"] == "phone":
                    if re.match(r'^[+0-9(-]{,3}([0-9]{3,3}).*([0-9]{3,3}).*([0-9]{4,4})$', elem.attrib["v"]):
                        node[elem.attrib["k"]] = "-".join(re.match(r'^[+0-9(-]{,3}([0-9]{3,3}).*([0-9]{3,3}).*([0-9]{4,4})$', elem.attrib["v"]).groups())
                    else:
                        node[elem.attrib["k"]] = elem.attrib["v"]

                else:
                    node[elem.attrib["k"]] = elem.attrib["v"]

            if elem.tag == "nd":
                node_nd.append(elem.attrib["ref"])
                # print(node_nd)

            if elem.tag == "member":
                for j in elem.attrib.keys():
                    tmp_relation[j]=elem.attrib[j]
                tmp_array.append(tmp_relation)


        if node_nd:
            node["node_refs"] = node_nd
            # print(node_nd)

        if tmp_relation:
            node["member"] = tmp_array

        if tmp:
            for i in tmp:
                node[i] = tmp[i]


        return node
    else:
        return None

# process document and save it to .json format
def process_map(file_in, pretty=False):
    file_out = "{0}.json".format(file_in)
    data = []
    nl={}
    with codecs.open(file_out, "w") as fo:
        fo.write("[\n")
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                while nl:
                    if pretty:
                        fo.write(json.dumps(nl, indent=2) + ",\n")
                        break
                    else:
                        fo.write(json.dumps(nl) + ",\n")
                        break
                nl=copy.deepcopy(el)
        fo.write(json.dumps(nl) + "\n" + "]")
    return data


def test():
    data = process_map('test.osm', False)
    #pprint.pprint(data)


if __name__ == "__main__":
    test()