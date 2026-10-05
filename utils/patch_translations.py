import json

gu_missing = {
    'add_product_desc': 'એક નવું કૃષિ ઉત્પાદન ઉમેરો.',
    'order_receipt': 'ઓર્ડર રસીદ',
    'accepted_deal': 'સ્વીકારેલ સોદો',
    'footer_register': 'રજીસ્ટર',
    'contact_us': 'સંપર્ક કરો',
    'total_amount_paid': 'ચૂકવેલ કુલ રકમ:',
    'footer_about_desc': 'ફાર્મલિંક એક સ્થાનિક ખેડૂત બજાર છે જે ખેડૂતોને સીધા ખરીદદારો સાથે જોડે છે, જેથી ખેડૂતોને યોગ્ય કિંમત મળે અને ખરીદદારો વચ્ચેના દલાલો વિના તાજા કૃષિ ઉત્પાદનો ખરીદી શકે.',
    'my_products_desc': 'તમારી ઉત્પાદન સૂચિ જુઓ અને સંચાલિત કરો.',
    'order_ref_id': 'ઓર્ડર સંદર્ભ ID:',
    'agreed_current_offer': 'સંમત/વર્તમાન પ્રસ્તાવ',
    'no_bargaining_sessions_found': 'કોઈ ભાવતાલ સત્રો મળ્યા નથી.',
    'total_products': 'કુલ ઉત્પાદનો',
    'coming_soon_favourites': 'આ સુવિધા ટૂંક સમયમાં આવી રહી છે! તમે પછીથી સરળ ઍક્સેસ માટે તમારી મનપસંદ સૂચિઓને બુકમાર્ક કરી શકશો.',
    'edit_buyer_profile': 'ખરીદનાર પ્રોફાઇલ સંપાદિત કરો',
    'all_rights_reserved': 'તમામ હકો આરક્ષિત છે.',
    'product_label': 'ઉત્પાદન:',
    'edit_product': 'ઉત્પાદન સંપાદિત કરો',
    'welcome_seller': 'સ્વાગત છે, વિક્રેતા!',
    'browse_more_products': 'વધુ ઉત્પાદનો જુઓ',
    'footer_login': 'લોગિન',
    'product_views': 'ઉત્પાદન દૃશ્યો',
    'manage_products_desc': 'તમારા ઉત્પાદનોનું સંચાલન કરો અને સીધા ખરીદદારો સાથે જોડાઓ.',
    'seller': 'વિક્રેતા',
    'footer_search_products': 'ઉત્પાદનો શોધો',
    'active_products': 'સક્રિય ઉત્પાદનો',
    'buyer_contacts': 'ખરીદનાર સંપર્કો',
    'quantity_label': 'જથ્થો:',
    'developed_using': 'પાયથોન (ફ્લાસ્ક), માયએસક્યુએલ, એચટીએમએલ, સીએસએસ, બુટસ્ટ્રેપ અને જાવાસ્ક્રિપ્ટનો ઉપયોગ કરીને વિકસાવવામાં આવ્યું છે.',
    'agreed_unit_price': 'સંમત એકમ કિંમત:',
    'my_favourites': 'મારા મનપસંદ',
    'browse_marketplace': 'બજાર જુઓ',
    'quick_links': 'ઝડપી લિંક્સ',
    'go_to_dashboard': 'ડેશબોર્ડ પર જાઓ',
    'order_success_desc': 'તમારી ખરીદી માટે આભાર. તમારો ઓર્ડર સફળતાપૂર્વક મૂકવામાં આવ્યો છે. વિક્રેતાને જાણ કરવામાં આવી છે અને રવાનગીની વિગતો માટે ટૂંક સમયમાં તમારો સંપર્ક કરશે.',
    'current_product_image': 'વર્તમાન ઉત્પાદન છબી'
}

with open('d:/MP/FarmLink/utils/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Instead of parsing, we can just append to the 'gu' dictionary in the file.
# The 'gu' dictionary ends with 'no_notifications': '...'
# We'll just replace the end of 'gu' dictionary.
# Let's import the actual dictionary and rewrite the file properly to maintain formatting.

import sys
sys.path.append('d:/MP/FarmLink/utils')
from translations import TRANSLATIONS

for k, v in gu_missing.items():
    TRANSLATIONS['gu'][k] = v

# Ensure the keys are in the same order as 'en'
ordered_gu = {k: TRANSLATIONS['gu'].get(k, TRANSLATIONS['en'][k]) for k in TRANSLATIONS['en']}
TRANSLATIONS['gu'] = ordered_gu

# Re-write the file
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

print("Done updating translations.py")
