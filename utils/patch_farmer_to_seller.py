import json

with open('d:/MP/FarmLink/utils/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

import sys
sys.path.append('d:/MP/FarmLink/utils')
from translations import TRANSLATIONS

for lang, lang_dict in TRANSLATIONS.items():
    for k, v in lang_dict.items():
        if lang == 'en':
            v = v.replace('Farmers', 'Sellers')
            v = v.replace('farmers', 'sellers')
            v = v.replace('Farmer', 'Seller')
            v = v.replace('farmer', 'seller')
            lang_dict[k] = v
        elif lang == 'hi':
            v = v.replace('किसानों', 'विक्रेताओं')
            v = v.replace('किसान', 'विक्रेता')
            lang_dict[k] = v
        elif lang == 'gu':
            v = v.replace('ખેડૂતો', 'વિક્રેતાઓ')
            v = v.replace('ખેડૂત', 'વિક્રેતા')
            lang_dict[k] = v

with open('d:/MP/FarmLink/utils/translations.py', 'w', encoding='utf-8') as f:
    f.write("# FarmLink Multilingual UI Translations\n\nTRANSLATIONS = {\n")
    for lang, lang_dict in TRANSLATIONS.items():
        f.write(f'    "{lang}": {{\n')
        for k, v in lang_dict.items():
            # escape quotes
            v_escaped = v.replace('"', '\\"')
            f.write(f'        "{k}": "{v_escaped}",\n')
        f.write("    },\n")
    f.write("}\n")

print("Done updating translations.py for seller replacement")
