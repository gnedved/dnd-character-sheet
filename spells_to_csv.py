#!python3
from dw_logging import configure_logging, prnt, get_log_file, global_status_log
import DWEmail
import json
import sys, os
import pandas
import pandas.io.json
import csv
import sqlite3



proj_name = 'Demo for logging/exception emails.'
cur_path = os.getcwd()

db = sqlite3.connect(':memory:')

spell_columns = ["name",
                 "level",
                 "casting_time",
                 "school",
                 "concentration",
                 "range",
                 "components",
                 "materials",
                 "duration",
                 "description",
                 "classes",
                 "subclasses",
                 "ritual",
                 "source",
                 "page"
                 ]

configure_logging()

def create_spell_csv(spell_dict_list, file_name):
    # use dictWriter, should work
    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=spell_columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(spell_dict_list)
    # writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    # writer.writerow(spell_columns)


def create_spell_dict(spell_file):

    spell_list = []

    with open(spell_file) as json_file:
        spells = json.load(json_file)

        # get spell data, probably put this in another function?
        for spell in spells['spell']:
            temp_dic = {"name": spell.get('name', '')}
            temp_dic.update({"level": spell.get('level', '')})
            #temp_dic.update({"casting_time": spell.get('time')})

            time_list = spell.get('time', '')
            time_string = ""
            for t, time in enumerate(time_list):
                if t != 0:
                    time_string += " or "
                time_string += str(time.get('number', '')) + " " + time.get('unit', '')

            temp_dic.update({"casting_time": time_string})

            # Get school value
            school = spell.get('school', '')
            if school == 'A':
                school = 'Abjuration'
            elif school == 'C':
                school = 'Conjuration'
            elif school == 'D':
                school = 'Divination'
            elif school == 'E':
                school = 'Enchantment'
            elif school == 'I':
                school = 'Illusion'
            elif school == 'N':
                school = 'Necromancy'
            elif school == 'T':
                school = 'Transmutation'
            elif school == 'V':
                school = 'Evocation'

            temp_dic.update({"school": school})

            # Get duration and concentration values
            duration_list = spell.get('duration', '')
            duration = ""
            concentration = False

            for item in duration_list:
                time_type = item.get('type', '')
                if time_type == 'instant':
                    duration += "instantaneous"
                elif time_type == 'permanent':
                    duration += 'until'
                    for e, ends in enumerate(item.get('ends', '')):
                        if e != 0:
                            duration += " or "
                        duration += f" {ends}ed"
                elif time_type == 'special':
                    duration += "special"
                elif time_type == 'timed':
                    sub_duration = item.get('duration', '')
                    duration_type = sub_duration.get('type', '')
                    duration_amount = sub_duration.get('amount', '')
                    if duration_amount > 0:
                        duration_amount = str(duration_amount) + " "
                    duration_upto = sub_duration.get('upTo', False)
                    if duration_upto:
                        duration_upto = 'up to '
                    else:
                        duration_upto = ""

                    concentration = item.get('concentration', False)
                    duration = f"{duration_upto}{duration_amount}{duration_type}"

            temp_dic.update({"concentration": concentration})
            temp_dic.update({"duration": duration})

            # Get spell range
            range_list = spell.get('range', '')
            spell_range = ""
            if range_list.get('type') == 'special':
                spell_range = "special"
            else:
                spell_distance = range_list.get('distance', '')
                spell_range = f"{spell_distance.get('amount', '')} {spell_distance.get('type', '')}"
            temp_dic.update({"range": spell_range})

            # Get components and materials
            comp_dict = spell.get('components', '')
            components = ""
            if comp_dict.get('v', ''):
                components += 'v'
            if comp_dict.get('s', ''):
                if components != '':
                    components += ", "
                components += 's'
            if comp_dict.get('m', ''):
                if components != '':
                    components += ", "
                components += 'm'
            temp_dic.update({"components": components})
            materials = comp_dict.get('m', '')
            if materials != '':
                materials = f"({materials})"
            temp_dic.update({"materials": materials})

            # Get spell description
            entry_list = spell.get('entries', '')
            description = ""
            for entry in entry_list:
                if isinstance(entry, dict):
                    if entry.get('type') == 'entries':
                        description += entry.get('name', '')
                        for sub_entry in entry.get('entries', ''):
                            #prnt(f"SUB: {sub_entry}")
                            #prnt(f"{spell.get('name', '')}")
                            if isinstance(sub_entry, dict):
                                if sub_entry.get('type') == 'entries':
                                    description += "\n".join(sub_entry.get('entries'))
                                elif sub_entry.get('type') == 'list':
                                    description += "\n".join(sub_entry.get('items'))
                            else:
                                description += sub_entry + "\n"
                    elif entry.get('type') == 'list':
                        description += "\n".join(entry.get('items'))
                else:
                    description += entry + "\n"
            temp_dic.update({"description": description})

            # Get Classes\
            class_dict = spell.get('classes',)
            class_list = class_dict.get('fromClassList', '')
            classes = ""
            #classes = ",".join(class_list).get('name')
            for i, c in enumerate(class_list):
                if i != 0:
                    classes += ","
                tmp_class_name = c.get('name')
                # Artificer has multiple versions, so consolidate all to one class
                classes += ('Artificer' if 'Artificer' in tmp_class_name else tmp_class_name)
            temp_dic.update({"classes": classes})

            # Get Subclasses (PSA, UA, Twitter, Stream)
            subclass_list = class_dict.get('fromSubclass')
            subclasses = ""
            if subclass_list:
                #subclasses = ",".join(subclass_list.get('subclass').get('name'))
                for i, s in enumerate(subclass_list):
                    if i != 0:
                        subclasses += ","

                    # Remove PSA, UA, Twitter and Stream endings on subclasses
                    temp_subclass_name = s.get('subclass').get('name', '')
                    temp_subclass_name = temp_subclass_name.replace('(PSA)', '')
                    temp_subclass_name = temp_subclass_name.replace('(UA)', '')
                    temp_subclass_name = temp_subclass_name.replace('(Twitter)', '')
                    temp_subclass_name = temp_subclass_name.replace('(Stream)', '')
                    temp_subclass_name = temp_subclass_name.replace('v2', '')
                    temp_subclass_name = temp_subclass_name.strip()
                    subclasses += temp_subclass_name
            temp_dic.update({"subclasses": subclasses})

            # Get ritual Flag
            meta_tag = spell.get('meta', '')
            if meta_tag != '':
                temp_dic.update({"ritual": meta_tag.get('ritual', False)})
            else:
                temp_dic.update({"ritual": False})

            temp_dic.update({"source": spell.get('source', '')})
            temp_dic.update({"page": spell.get('page', '')})
            spell_list.append(temp_dic)

        #AFTER LOOP

        #prnt(str(spell_list))
        return spell_list

@global_status_log()
def run(arguments):
    spell_json_file = cur_path + 'spells/spells-phb.json'

    try:
        if len(arguments) > 2:
            prnt("too many arguments provided.")
        else:
            spell_json_file = cur_path + f"\\spells\\{arguments[1]}"
    except Exception as e:
        prnt(f"An Error occurred while executing procedure \n {e}")
    spells = create_spell_dict(spell_file=spell_json_file)
    create_spell_csv(spell_dict_list=spells, file_name=f"{arguments[1].replace('json','csv')}")


if __name__ == '__main__':
    run(sys.argv)