import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import requests
from worldtravel.models import Country, Region
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.contrib.gis.geos.error import GEOSException
import json

from django.conf import settings
        
media_root = settings.MEDIA_ROOT


def setGeometry(region_code):
    # Assuming the file name is the country code (e.g., 'AU.json' for Australia)
    country_code = region_code.split('-')[0]
    json_file = os.path.join('static/data', f'{country_code.lower()}.json')
    
    if not os.path.exists(json_file):
        print(f'File {country_code}.json does not exist (it probably hasn''t been added, contributors are welcome!)')
        return None

    try:
        with open(json_file, 'r') as f:
            geojson_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in file for {country_code}: {e}")
        return None

    if 'type' not in geojson_data or geojson_data['type'] != 'FeatureCollection':
        print(f"Invalid GeoJSON structure for {country_code}: missing or incorrect 'type'")
        return None

    if 'features' not in geojson_data or not geojson_data['features']:
        print(f"Invalid GeoJSON structure for {country_code}: missing or empty 'features'")
        return None

    for feature in geojson_data['features']:
        try:
            properties = feature.get('properties', {})
            isocode = properties.get('ISOCODE')
            
            if isocode == region_code:
                geometry = feature['geometry']
                geos_geom = GEOSGeometry(json.dumps(geometry))
                
                if isinstance(geos_geom, Polygon):
                    Region.objects.filter(id=region_code).update(geometry=MultiPolygon([geos_geom]))
                    print(f"Updated geometry for region {region_code}")
                    return MultiPolygon([geos_geom])
                elif isinstance(geos_geom, MultiPolygon):
                    Region.objects.filter(id=region_code).update(geometry=geos_geom)
                    print(f"Updated geometry for region {region_code}")
                    return geos_geom
                else:
                    print(f"Unexpected geometry type for region {region_code}: {type(geos_geom)}")
                    return None

        except (KeyError, ValueError, GEOSException) as e:
            print(f"Error processing region {region_code}: {e}")

    print(f"No matching region found for {region_code}")
    return None

def saveCountryFlag(country_code):
    flags_dir = os.path.join(media_root, 'flags')

    # Check if the flags directory exists, if not, create it
    if not os.path.exists(flags_dir):
        os.makedirs(flags_dir)

    # Check if the flag already exists in the media folder
    flag_path = os.path.join(flags_dir, f'{country_code}.png')
    if os.path.exists(flag_path):
        print(f'Flag for {country_code} already exists')
        return

    res = requests.get(f'https://flagcdn.com/h240/{country_code}.png')
    if res.status_code == 200:
        with open(flag_path, 'wb') as f:
            f.write(res.content)
        print(f'Flag for {country_code} downloaded')
    else:
        print(f'Error downloading flag for {country_code}')

class Command(BaseCommand):
    help = 'Imports the world travel data'

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            help='Force import even if data already exists'
        )

    def handle(self, *args, **options):
        force = options['force']
        
        countries = [
            ('United States', 'us', 'NA'),
            ('Canada', 'ca', 'NA'),
            ('Mexico', 'mx', 'NA'),
            ('Brazil', 'br', 'SA'),
            ('Argentina', 'ar', 'SA'),
            ('United Kingdom', 'gb', 'EU'),
            ('Germany', 'de', 'EU'),
            ('France', 'fr', 'EU'),
            ('Japan', 'jp', 'AS'),
            ('China', 'cn', 'AS'),
            ('India', 'in', 'AS'),
            ('Australia', 'au', 'OC'),
            ('New Zealand', 'nz', 'OC'),
            ('South Africa', 'za', 'AF'),
            ('Egypt', 'eg', 'AF'),
            ('Sweden', 'se', 'EU'),
            ('Ireland', 'ie', 'EU'),
            ('Spain', 'es', 'EU'),
            ('Switzerland', 'ch', 'EU'),
            ('Italy', 'it', 'EU'),
            ('Iceland', 'is', 'EU'),
            ('Czech Republic', 'cz', 'EU'),
            ('Austria', 'at', 'EU'),
            ('Slovakia','sk','EU'),
            ('Liechtenstein','li','EU'),
        ]
        
        regions = [
            ('US-AL', 'Alabama', 'Alabama', 'us'),
            ('US-AK', 'Alaska', 'Alaska', 'us'),
            ('US-AZ', 'Arizona', 'Arizona', 'us'),
            ('US-AR', 'Arkansas', 'Arkansas', 'us'),
            ('US-CA', 'California', 'California', 'us'),
            ('US-CO', 'Colorado', 'Colorado', 'us'),
            ('US-CT', 'Connecticut', 'Connecticut', 'us'),
            ('US-DE', 'Delaware', 'Delaware', 'us'),
            ('US-FL', 'Florida', 'Florida', 'us'),
            ('US-GA', 'Georgia', 'Georgia', 'us'),
            ('US-HI', 'Hawaii', 'Hawaii', 'us'),
            ('US-ID', 'Idaho', 'Idaho', 'us'),
            ('US-IL', 'Illinois', 'Illinois', 'us'),
            ('US-IN', 'Indiana', 'Indiana', 'us'),
            ('US-IA', 'Iowa', 'Iowa', 'us'),
            ('US-KS', 'Kansas', 'Kansas', 'us'),
            ('US-KY', 'Kentucky', 'Kentucky', 'us'),
            ('US-LA', 'Louisiana', 'Louisiana', 'us'),
            ('US-ME', 'Maine', 'Maine', 'us'),
            ('US-MD', 'Maryland', 'Maryland', 'us'),
            ('US-MA', 'Massachusetts', 'Massachusetts', 'us'),
            ('US-MI', 'Michigan', 'Michigan', 'us'),
            ('US-MN', 'Minnesota', 'Minnesota', 'us'),
            ('US-MS', 'Mississippi', 'Mississippi', 'us'),
            ('US-MO', 'Missouri', 'Missouri', 'us'),
            ('US-MT', 'Montana', 'Montana', 'us'),
            ('US-NE', 'Nebraska', 'Nebraska', 'us'),
            ('US-NV', 'Nevada', 'Nevada', 'us'),
            ('US-NH', 'New Hampshire', 'New Hampshire', 'us'),
            ('US-NJ', 'New Jersey', 'New Jersey', 'us'),
            ('US-NM', 'New Mexico', 'New Mexico', 'us'),
            ('US-NY', 'New York', 'New York', 'us'),
            ('US-NC', 'North Carolina', 'North Carolina', 'us'),
            ('US-ND', 'North Dakota', 'North Dakota', 'us'),
            ('US-OH', 'Ohio', 'Ohio', 'us'),
            ('US-OK', 'Oklahoma', 'Oklahoma', 'us'),
            ('US-OR', 'Oregon', 'Oregon', 'us'),
            ('US-PA', 'Pennsylvania', 'Pennsylvania', 'us'),
            ('US-RI', 'Rhode Island', 'Rhode Island', 'us'),
            ('US-SC', 'South Carolina', 'South Carolina', 'us'),
            ('US-SD', 'South Dakota', 'South Dakota', 'us'),
            ('US-TN', 'Tennessee', 'Tennessee', 'us'),
            ('US-TX', 'Texas', 'Texas', 'us'),
            ('US-UT', 'Utah', 'Utah', 'us'),
            ('US-VT', 'Vermont', 'Vermont', 'us'),
            ('US-VA', 'Virginia', 'Virginia', 'us'),
            ('US-WA', 'Washington', 'Washington', 'us'),
            ('US-WV', 'West Virginia', 'West Virginia', 'us'),
            ('US-WI', 'Wisconsin', 'Wisconsin', 'us'),
            ('US-WY', 'Wyoming', 'Wyoming', 'us'),
            ('CA-AB', 'Alberta', 'Alberta', 'ca'),
            ('CA-BC', 'British Columbia', 'British Columbia', 'ca'),
            ('CA-MB', 'Manitoba', 'Manitoba', 'ca'),
            ('CA-NB', 'New Brunswick', 'New Brunswick', 'ca'),
            ('CA-NL', 'Newfoundland and Labrador', 'Newfoundland and Labrador', 'ca'),
            ('CA-NS', 'Nova Scotia', 'Nova Scotia', 'ca'),
            ('CA-ON', 'Ontario', 'Ontario', 'ca'),
            ('CA-PE', 'Prince Edward Island', 'Prince Edward Island', 'ca'),
            ('CA-QC', 'Quebec', 'Quebec', 'ca'),
            ('CA-SK', 'Saskatchewan', 'Saskatchewan', 'ca'),
            ('CA-NT', 'Northwest Territories', 'Northwest Territories', 'ca'),
            ('CA-NU', 'Nunavut', 'Nunavut', 'ca'),
            ('CA-YT', 'Yukon', 'Yukon', 'ca'),
            ('DE-BW', 'Baden-Württemberg', 'Baden-Württemberg', 'de'),
            ('DE-BY', 'Bayern', 'Bavaria', 'de'),
            ('DE-BE', 'Berlin', 'Berlin', 'de'),
            ('DE-BB', 'Brandenburg', 'Brandenburg', 'de'),
            ('DE-HB', 'Bremen', 'Bremen', 'de'),
            ('DE-HH', 'Hamburg', 'Hamburg', 'de'),
            ('DE-HE', 'Hessen', 'Hesse', 'de'),
            ('DE-MV', 'Mecklenburg-Vorpommern', 'Mecklenburg-Western Pomerania', 'de'),
            ('DE-NI', 'Niedersachsen', 'Lower Saxony', 'de'),
            ('DE-NW', 'Nordrhein-Westfalen', 'North Rhine-Westphalia', 'de'),
            ('DE-RP', 'Rheinland-Pfalz', 'Rhineland-Palatinate', 'de'),
            ('DE-SL', 'Saarland', 'Saarland', 'de'),
            ('DE-SN', 'Sachsen', 'Saxony', 'de'),
            ('DE-ST', 'Sachsen-Anhalt', 'Saxony-Anhalt', 'de'),
            ('DE-SH', 'Schleswig-Holstein', 'Schleswig-Holstein', 'de'),
            ('DE-TH', 'Thüringen', 'Thuringia', 'de'),
            ('FR-ARA', 'Auvergne-Rhône-Alpes', 'Auvergne-Rhône-Alpes', 'fr'),
            ('FR-BFC', 'Bourgogne-Franche-Comté', 'Burgundy-Franche-Comté', 'fr'),
            ('FR-BRE', 'Bretagne', 'Brittany', 'fr'),
            ('FR-CVL', 'Centre-Val de Loire', 'Centre-Val de Loire', 'fr'),
            ('FR-GES', 'Grand Est', 'Grand Est', 'fr'),
            ('FR-HDF', 'Hauts-de-France', 'Hauts-de-France', 'fr'),
            ('FR-IDF', 'Île-de-France', 'Île-de-France', 'fr'),
            ('FR-NOR', 'Normandy', 'Normandy', 'fr'),
            ('FR-NAQ', 'Nouvelle-Aquitaine', 'New Aquitaine', 'fr'),
            ('FR-OCC', 'Occitanie', 'Occitania', 'fr'),
            ('FR-PDL', 'Pays de la Loire', 'Pays de la Loire', 'fr'),
            ('FR-PAC', 'Provence-Alpes-Côte d''Azur', 'Provence-Alpes-Côte d''Azur', 'fr'),
            ('FR-COR', 'Corsica', 'Corsica', 'fr'),
            ('FR-MQ', 'Martinique', 'Martinique', 'fr'),
            ('FR-GF', 'French Guiana', 'French Guiana', 'fr'),
            ('FR-RÉ', 'Réunion', 'Réunion', 'fr'),
            ('FR-YT', 'Mayotte', 'Mayotte', 'fr'),
            ('FR-GP', 'Guadeloupe', 'Guadeloupe', 'fr'),
            ('GB-ENG', 'England', 'England', 'gb'),
            ('GB-NIR', 'Northern Ireland', 'Northern Ireland', 'gb'),
            ('GB-SCT', 'Scotland', 'Scotland', 'gb'),
            ('GB-WLS', 'Wales', 'Wales', 'gb'),
            ('AR-C', 'Ciudad Autónoma de Buenos Aires', 'Autonomous City of Buenos Aires', 'ar'),
            ('AR-B', 'Buenos Aires', 'Buenos Aires', 'ar'),
            ('AR-K', 'Catamarca', 'Catamarca', 'ar'),
            ('AR-H', 'Chaco', 'Chaco', 'ar'),
            ('AR-U', 'Chubut', 'Chubut', 'ar'),
            ('AR-W', 'Córdoba', 'Córdoba', 'ar'),
            ('AR-X', 'Corrientes', 'Corrientes', 'ar'),
            ('AR-E', 'Entre Ríos', 'Entre Ríos', 'ar'),
            ('AR-P', 'Formosa', 'Formosa', 'ar'),
            ('AR-Y', 'Jujuy', 'Jujuy', 'ar'),
            ('AR-L', 'La Pampa', 'La Pampa', 'ar'),
            ('AR-F', 'La Rioja', 'La Rioja', 'ar'),
            ('AR-M', 'Mendoza', 'Mendoza', 'ar'),
            ('AR-N', 'Misiones', 'Misiones', 'ar'),
            ('AR-Q', 'Neuquén', 'Neuquén', 'ar'),
            ('AR-R', 'Río Negro', 'Río Negro', 'ar'),
            ('AR-A', 'Salta', 'Salta', 'ar'),
            ('AR-J', 'San Juan', 'San Juan', 'ar'),
            ('AR-D', 'San Luis', 'San Luis', 'ar'),
            ('AR-Z', 'Santa Cruz', 'Santa Cruz', 'ar'),
            ('AR-S', 'Santa Fe', 'Santa Fe', 'ar'),
            ('AR-G', 'Santiago del Estero', 'Santiago del Estero', 'ar'),
            ('AR-V', 'Tierra del Fuego', 'Tierra del Fuego', 'ar'),
            ('AR-T', 'Tucumán', 'Tucumán', 'ar'),
            ('MX-AGU', 'Aguascalientes', 'Aguascalientes', 'mx'),
            ('MX-BCN', 'Baja California', 'Baja California', 'mx'),
            ('MX-BCS', 'Baja California Sur', 'Baja California Sur', 'mx'),
            ('MX-CAM', 'Campeche', 'Campeche', 'mx'),
            ('MX-CHP', 'Chiapas', 'Chiapas', 'mx'),
            ('MX-CHH', 'Chihuahua', 'Chihuahua', 'mx'),
            ('MX-CMX', 'Ciudad de México', 'Mexico City', 'mx'),
            ('MX-COA', 'Coahuila de Zaragoza', 'Coahuila', 'mx'),
            ('MX-COL', 'Colima', 'Colima', 'mx'),
            ('MX-DUR', 'Durango', 'Durango', 'mx'),
            ('MX-GUA', 'Guanajuato', 'Guanajuato', 'mx'),
            ('MX-GRO', 'Guerrero', 'Guerrero', 'mx'),
            ('MX-HID', 'Hidalgo', 'Hidalgo', 'mx'),
            ('MX-JAL', 'Jalisco', 'Jalisco', 'mx'),
            ('MX-MIC', 'Michoacán de Ocampo', 'Michoacán', 'mx'),
            ('MX-MOR', 'Morelos', 'Morelos', 'mx'),
            ('MX-MEX', 'México', 'State of Mexico', 'mx'),
            ('MX-NAY', 'Nayarit', 'Nayarit', 'mx'),
            ('MX-NLE', 'Nuevo León', 'Nuevo León', 'mx'),
            ('MX-OAX', 'Oaxaca', 'Oaxaca', 'mx'),
            ('MX-PUE', 'Puebla', 'Puebla', 'mx'),
            ('MX-QUE', 'Querétaro', 'Querétaro', 'mx'),
            ('MX-ROO', 'Quintana Roo', 'Quintana Roo', 'mx'),
            ('MX-SLP', 'San Luis Potosí', 'San Luis Potosí', 'mx'),
            ('MX-SIN', 'Sinaloa', 'Sinaloa', 'mx'),
            ('MX-SON', 'Sonora', 'Sonora', 'mx'),
            ('MX-TAB', 'Tabasco', 'Tabasco', 'mx'),
            ('MX-TAM', 'Tamaulipas', 'Tamaulipas', 'mx'),
            ('MX-TLA', 'Tlaxcala', 'Tlaxcala', 'mx'),
            ('MX-VER', 'Veracruz de Ignacio de la Llave', 'Veracruz', 'mx'),
            ('MX-YUC', 'Yucatán', 'Yucatán', 'mx'),
            ('MX-ZAC', 'Zacatecas', 'Zacatecas', 'mx'),
            ('JP-01', 'Hokkaido', 'Hokkaido', 'jp'),
            ('JP-02', 'Aomori', 'Aomori', 'jp'),
            ('JP-03', 'Iwate', 'Iwate', 'jp'),
            ('JP-04', 'Miyagi', 'Miyagi', 'jp'),
            ('JP-05', 'Akita', 'Akita', 'jp'),
            ('JP-06', 'Yamagata', 'Yamagata', 'jp'),
                ('JP-07', 'Fukushima', 'Fukushima', 'jp'),
            ('JP-08', 'Ibaraki', 'Ibaraki', 'jp'),
            ('JP-09', 'Tochigi', 'Tochigi', 'jp'),
            ('JP-10', 'Gunma', 'Gunma', 'jp'),
            ('JP-11', 'Saitama', 'Saitama', 'jp'),
            ('JP-12', 'Chiba', 'Chiba', 'jp'),
            ('JP-13', 'Tokyo', 'Tokyo', 'jp'),
            ('JP-14', 'Kanagawa', 'Kanagawa', 'jp'),
            ('JP-15', 'Niigata', 'Niigata', 'jp'),
            ('JP-16', 'Toyama', 'Toyama', 'jp'),
            ('JP-17', 'Ishikawa', 'Ishikawa', 'jp'),
            ('JP-18', 'Fukui', 'Fukui', 'jp'),
            ('JP-19', 'Yamanashi', 'Yamanashi', 'jp'),
            ('JP-20', 'Nagano', 'Nagano', 'jp'),
            ('JP-21', 'Gifu', 'Gifu', 'jp'),
            ('JP-22', 'Shizuoka', 'Shizuoka', 'jp'),
            ('JP-23', 'Aichi', 'Aichi', 'jp'),
            ('JP-24', 'Mie', 'Mie', 'jp'),
            ('JP-25', 'Shiga', 'Shiga', 'jp'),
            ('JP-26', 'Kyoto', 'Kyoto', 'jp'),
            ('JP-27', 'Osaka', 'Osaka', 'jp'),
            ('JP-28', 'Hyogo', 'Hyogo', 'jp'),
            ('JP-29', 'Nara', 'Nara', 'jp'),
            ('JP-30', 'Wakayama', 'Wakayama', 'jp'),
            ('JP-31', 'Tottori', 'Tottori', 'jp'),
            ('JP-32', 'Shimane', 'Shimane', 'jp'),
            ('JP-33', 'Okayama', 'Okayama', 'jp'),
            ('JP-34', 'Hiroshima', 'Hiroshima', 'jp'),
            ('JP-35', 'Yamaguchi', 'Yamaguchi', 'jp'),
            ('JP-36', 'Tokushima', 'Tokushima', 'jp'),
            ('JP-37', 'Kagawa', 'Kagawa', 'jp'),
            ('JP-38', 'Ehime', 'Ehime', 'jp'),
            ('JP-39', 'Kochi', 'Kochi', 'jp'),
            ('JP-40', 'Fukuoka', 'Fukuoka', 'jp'),
            ('JP-41', 'Saga', 'Saga', 'jp'),
            ('JP-42', 'Nagasaki', 'Nagasaki', 'jp'),
            ('JP-43', 'Kumamoto', 'Kumamoto', 'jp'),
            ('JP-44', 'Oita', 'Oita', 'jp'),
            ('JP-45', 'Miyazaki', 'Miyazaki', 'jp'),
            ('JP-46', 'Kagoshima', 'Kagoshima', 'jp'),
            ('JP-47', 'Okinawa', 'Okinawa', 'jp'),
            ('CN-BJ', 'Beijing', 'Beijing', 'cn'),
            ('CN-TJ', 'Tianjin', 'Tianjin', 'cn'),
            ('CN-HE', 'Hebei', 'Hebei', 'cn'),
            ('CN-SX', 'Shanxi', 'Shanxi', 'cn'),
            ('CN-NM', 'Inner Mongolia', 'Inner Mongolia', 'cn'),
            ('CN-LN', 'Liaoning', 'Liaoning', 'cn'),
            ('CN-JL', 'Jilin', 'Jilin', 'cn'),
            ('CN-HL', 'Heilongjiang', 'Heilongjiang', 'cn'),
            ('CN-SH', 'Shanghai', 'Shanghai', 'cn'),
            ('CN-JS', 'Jiangsu', 'Jiangsu', 'cn'),
            ('CN-ZJ', 'Zhejiang', 'Zhejiang', 'cn'),
            ('CN-AH', 'Anhui', 'Anhui', 'cn'),
            ('CN-FJ', 'Fujian', 'Fujian', 'cn'),
            ('CN-JX', 'Jiangxi', 'Jiangxi', 'cn'),
            ('CN-SD', 'Shandong', 'Shandong', 'cn'),
            ('CN-HA', 'Henan', 'Henan', 'cn'),
            ('CN-HB', 'Hubei', 'Hubei', 'cn'),
            ('CN-HN', 'Hunan', 'Hunan', 'cn'),
            ('CN-GD', 'Guangdong', 'Guangdong', 'cn'),
            ('CN-GX', 'Guangxi', 'Guangxi', 'cn'),
            ('CN-HI', 'Hainan', 'Hainan', 'cn'),
            ('CN-CQ', 'Chongqing', 'Chongqing', 'cn'),
            ('CN-SC', 'Sichuan', 'Sichuan', 'cn'),
            ('CN-GZ', 'Guizhou', 'Guizhou', 'cn'),
            ('CN-YN', 'Yunnan', 'Yunnan', 'cn'),
            ('CN-XZ', 'Tibet', 'Tibet', 'cn'),
            ('CN-SA', 'Shaanxi', 'Shaanxi', 'cn'),
            ('CN-GS', 'Gansu', 'Gansu', 'cn'),
            ('CN-QH', 'Qinghai', 'Qinghai', 'cn'),
            ('CN-NX', 'Ningxia', 'Ningxia', 'cn'),
            ('CN-XJ', 'Xinjiang', 'Xinjiang', 'cn'),
            ('IN-AN', 'Andaman and Nicobar Islands', 'Andaman and Nicobar Islands', 'in'),
            ('IN-AP', 'Andhra Pradesh', 'Andhra Pradesh', 'in'),
            ('IN-AR', 'Arunachal Pradesh', 'Arunachal Pradesh', 'in'),
            ('IN-AS', 'Assam', 'Assam', 'in'),
            ('IN-BR', 'Bihar', 'Bihar', 'in'),
            ('IN-CH', 'Chandigarh', 'Chandigarh', 'in'),
            ('IN-CT', 'Chhattisgarh', 'Chhattisgarh', 'in'),
            ('IN-DN', 'Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu', 'in'),
            ('IN-DD', 'Daman and Diu', 'Daman and Diu', 'in'),
            ('IN-DL', 'Delhi', 'Delhi', 'in'),
            ('IN-GA', 'Goa', 'Goa', 'in'),
            ('IN-GJ', 'Gujarat', 'Gujarat', 'in'),
            ('IN-HR', 'Haryana', 'Haryana', 'in'),
            ('IN-HP', 'Himachal Pradesh', 'Himachal Pradesh', 'in'),
            ('IN-JH', 'Jharkhand', 'Jharkhand', 'in'),
            ('IN-KA', 'Karnataka', 'Karnataka', 'in'),
            ('IN-KL', 'Kerala', 'Kerala', 'in'),
            ('IN-LD', 'Lakshadweep', 'Lakshadweep', 'in'),
            ('IN-MP', 'Madhya Pradesh', 'Madhya Pradesh', 'in'),
            ('IN-MH', 'Maharashtra', 'Maharashtra', 'in'),
            ('IN-MN', 'Manipur', 'Manipur', 'in'),
            ('IN-ML', 'Meghalaya', 'Meghalaya', 'in'),
            ('IN-MZ', 'Mizoram', 'Mizoram', 'in'),
            ('IN-NL', 'Nagaland', 'Nagaland', 'in'),
            ('IN-OR', 'Odisha', 'Odisha', 'in'),
            ('IN-PY', 'Puducherry', 'Puducherry', 'in'),
            ('IN-PB', 'Punjab', 'Punjab', 'in'),
            ('IN-RJ', 'Rajasthan', 'Rajasthan', 'in'),
            ('IN-SK', 'Sikkim', 'Sikkim', 'in'),
            ('IN-TN', 'Tamil Nadu', 'Tamil Nadu', 'in'),
            ('IN-TG', 'Telangana', 'Telangana', 'in'),
            ('IN-TR', 'Tripura', 'Tripura', 'in'),
            ('IN-UP', 'Uttar Pradesh', 'Uttar Pradesh', 'in'),
            ('IN-UT', 'Uttarakhand', 'Uttarakhand', 'in'),
            ('IN-WB', 'West Bengal', 'West Bengal', 'in'),
            ('AU-NSW', 'New South Wales', 'New South Wales', 'au'),
            ('AU-VIC', 'Victoria', 'Victoria', 'au'),
            ('AU-QLD', 'Queensland', 'Queensland', 'au'),
            ('AU-SA', 'South Australia', 'South Australia', 'au'),
            ('AU-WA', 'Western Australia', 'Western Australia', 'au'),
            ('AU-TAS', 'Tasmania', 'Tasmania', 'au'),
            ('AU-NT', 'Northern Territory', 'Northern Territory', 'au'),
            ('AU-ACT', 'Australian Capital Territory', 'Australian Capital Territory', 'au'),
            ('NZ-N', 'Northland', 'Northland', 'nz'),
            ('NZ-AUK', 'Auckland', 'Auckland', 'nz'),
            ('NZ-WKO', 'Waikato', 'Waikato', 'nz'),
            ('NZ-BOP', 'Bay of Plenty', 'Bay of Plenty', 'nz'),
            ('NZ-GIS', 'Gisborne', 'Gisborne', 'nz'),
            ('NZ-HKB', 'Hawke''s Bay', 'Hawke''s Bay', 'nz'),
            ('NZ-TKI', 'Taranaki', 'Taranaki', 'nz'),
            ('NZ-MWT', 'Manawatū-Whanganui', 'Manawatū-Whanganui', 'nz'),
            ('NZ-WGN', 'Wellington', 'Wellington', 'nz'),
            ('NZ-TAS', 'Tasman', 'Tasman', 'nz'),
            ('NZ-NEL', 'Nelson', 'Nelson', 'nz'),
            ('NZ-MBH', 'Marlborough', 'Marlborough', 'nz'),
            ('NZ-WTC', 'West Coast', 'West Coast', 'nz'),
            ('NZ-CAN', 'Canterbury', 'Canterbury', 'nz'),
            ('NZ-OTA', 'Otago', 'Otago', 'nz'),
            ('NZ-STL', 'Southland', 'Southland', 'nz'),
            ('ZA-EC', 'Eastern Cape', 'Eastern Cape', 'za'),
            ('ZA-FS', 'Free State', 'Free State', 'za'),
            ('ZA-GP', 'Gauteng', 'Gauteng', 'za'),
            ('ZA-KZN', 'KwaZulu-Natal', 'KwaZulu-Natal', 'za'),
            ('ZA-LP', 'Limpopo', 'Limpopo', 'za'),
            ('ZA-MP', 'Mpumalanga', 'Mpumalanga', 'za'),
            ('ZA-NW', 'North West', 'North West', 'za'),
            ('ZA-NC', 'Northern Cape', 'Northern Cape', 'za'),
            ('ZA-WC', 'Western Cape', 'Western Cape', 'za'),
            ('EG-ALX', 'Alexandria', 'Alexandria', 'eg'),
            ('EG-ASN', 'Aswan', 'Aswan', 'eg'),
            ('EG-ASY', 'Asyut', 'Asyut', 'eg'),
            ('EG-BHR', 'Beheira', 'Beheira', 'eg'),
            ('EG-BNS', 'Beni Suef', 'Beni Suef', 'eg'),
            ('EG-C', 'Cairo', 'Cairo', 'eg'),
            ('EG-DK', 'Dakahlia', 'Dakahlia', 'eg'),
            ('EG-DAM', 'Damietta', 'Damietta', 'eg'),
            ('EG-FYM', 'Faiyum', 'Faiyum', 'eg'),
            ('EG-GH', 'Gharbia', 'Gharbia', 'eg'),
            ('EG-GZ', 'Giza', 'Giza', 'eg'),
            ('EG-IS', 'Ismailia', 'Ismailia', 'eg'),
            ('EG-KB', 'Kafr El Sheikh', 'Kafr El Sheikh', 'eg'),
            ('EG-LX', 'Luxor', 'Luxor', 'eg'),
            ('EG-MN', 'Minya', 'Minya', 'eg'),
            ('EG-MT', 'Matrouh', 'Matrouh', 'eg'),
            ('EG-QH', 'Qalyubia', 'Qalyubia', 'eg'),
            ('EG-KFS', 'Qena', 'Qena', 'eg'),
            ('EG-SHG', 'Sohag', 'Sohag', 'eg'),
            ('EG-SHR', 'Sharqia', 'Sharqia', 'eg'),
            ('EG-SIN', 'South Sinai', 'South Sinai', 'eg'),
            ('EG-SW', 'Suez', 'Suez', 'eg'),
            ('EG-WAD', 'New Valley', 'New Valley', 'eg'),
            ('EG-ASD', 'North Sinai', 'North Sinai', 'eg'),
            ('EG-PTS', 'Port Said', 'Port Said', 'eg'),
            ('EG-SKB', 'Suez', 'Suez', 'eg'),
            ('EG-ESI', 'Ismailia', 'Ismailia', 'eg'),
            ('BR-AC', 'Acre', 'Acre', 'br'),
            ('BR-AL', 'Alagoas', 'Alagoas', 'br'),
            ('BR-AP', 'Amapá', 'Amapá', 'br'),
            ('BR-AM', 'Amazonas', 'Amazonas', 'br'),
            ('BR-BA', 'Bahia', 'Bahia', 'br'),
            ('BR-CE', 'Ceará', 'Ceará', 'br'),
            ('BR-DF', 'Federal District', 'Federal District', 'br'),
            ('BR-ES', 'Espírito Santo', 'Espírito Santo', 'br'),
            ('BR-GO', 'Goiás', 'Goiás', 'br'),
            ('BR-MA', 'Maranhão', 'Maranhão', 'br'),
            ('BR-MT', 'Mato Grosso', 'Mato Grosso', 'br'),
            ('BR-MS', 'Mato Grosso do Sul', 'Mato Grosso do Sul', 'br'),
            ('BR-MG', 'Minas Gerais', 'Minas Gerais', 'br'),
            ('BR-PA', 'Pará', 'Pará', 'br'),
            ('BR-PB', 'Paraíba', 'Paraíba', 'br'),
            ('BR-PR', 'Paraná', 'Paraná', 'br'),
            ('BR-PE', 'Pernambuco', 'Pernambuco', 'br'),
            ('BR-PI', 'Piauí', 'Piauí', 'br'),
            ('BR-RJ', 'Rio de Janeiro', 'Rio de Janeiro', 'br'),
            ('BR-RN', 'Rio Grande do Norte', 'Rio Grande do Norte', 'br'),
            ('BR-RS', 'Rio Grande do Sul', 'Rio Grande do Sul', 'br'),
            ('BR-RO', 'Rondônia', 'Rondônia', 'br'),
            ('BR-RR', 'Roraima', 'Roraima', 'br'),
            ('BR-SC', 'Santa Catarina', 'Santa Catarina', 'br'),
            ('BR-SP', 'São Paulo', 'São Paulo', 'br'),
            ('BR-SE', 'Sergipe', 'Sergipe', 'br'),
            ('BR-TO', 'Tocantins', 'Tocantins', 'br'),
            ('SE-AB', 'Stockholm', 'Stockholm', 'se'),
            ('SE-AC', 'Västerbotten', 'Västerbotten', 'se'),
            ('SE-BD', 'Norrbotten', 'Norrbotten', 'se'),
            ('SE-C', 'Uppsala', 'Uppsala', 'se'),
            ('SE-D', 'Södermanland', 'Södermanland', 'se'),
            ('SE-E', 'Östergötland', 'Östergötland', 'se'),
            ('SE-F', 'Jönköping', 'Jönköping', 'se'),
            ('SE-G', 'Kronoberg', 'Kronoberg', 'se'),
            ('SE-H', 'Kalmar', 'Kalmar', 'se'),
            ('SE-I', 'Gotland', 'Gotland', 'se'),
            ('SE-K', 'Blekinge', 'Blekinge', 'se'),
            ('SE-M', 'Skåne', 'Skåne', 'se'),
            ('SE-N', 'Halland', 'Halland', 'se'),
            ('SE-O', 'Västra Götaland', 'Västra Götaland', 'se'),
            ('SE-S', 'Värmland', 'Värmland', 'se'),
            ('SE-T', 'Örebro', 'Örebro', 'se'),
            ('SE-U', 'Västmanland', 'Västmanland', 'se'),
            ('SE-W', 'Dalarna', 'Dalarna', 'se'),
            ('SE-X', 'Gävleborg', 'Gävleborg', 'se'),
            ('SE-Y', 'Västernorrland', 'Västernorrland', 'se'),
            ('SE-Z', 'Jämtland', 'Jämtland', 'se'),
            ('IE-C', 'Connacht', 'Connacht', 'ie'),
            ('IE-L', 'Leinster', 'Leinster', 'ie'),
            ('IE-M', 'Munster', 'Munster', 'ie'),
            ('IE-U', 'Ulster', 'Ulster', 'ie'),
            ('ES-AN', 'Andalucía', 'Andalusia', 'es'),
            ('ES-AR', 'Aragón', 'Aragon', 'es'),
            ('ES-AS', 'Asturias', 'Asturias', 'es'),
            ('ES-CB', 'Cantabria', 'Cantabria', 'es'),
            ('ES-CL', 'Castilla y León', 'Castile and León', 'es'),
            ('ES-CM', 'Castilla-La Mancha', 'Castilla–La Mancha', 'es'),
            ('ES-CN', 'Canarias', 'Canary Islands', 'es'),
            ('ES-CT', 'Cataluña', 'Catalonia', 'es'),
            ('ES-EX', 'Extremadura', 'Extremadura', 'es'),
            ('ES-GA', 'Galicia', 'Galicia', 'es'),
            ('ES-IB', 'Islas Baleares', 'Balearic Islands', 'es'),
            ('ES-MD', 'Madrid', 'Madrid', 'es'),
            ('ES-MC', 'Murcia', 'Murcia', 'es'),
            ('ES-NC', 'Navarra', 'Navarre', 'es'),
            ('ES-PV', 'País Vasco', 'Basque Country', 'es'),
            ('ES-RI', 'La Rioja', 'La Rioja', 'es'),
            ('ES-VC', 'Comunidad Valenciana', 'Valencian Community', 'es'),
            ('CH-AG', 'Aargau', 'Aargau', 'ch'),
            ('CH-AR', 'Appenzell Ausserrhoden', 'Appenzell Outer Rhodes', 'ch'),
            ('CH-AI', 'Appenzell Innerrhoden', 'Appenzell Inner Rhodes', 'ch'),
            ('CH-BL', 'Basel-Landschaft', 'Basel-Country', 'ch'),
            ('CH-BS', 'Basel-Stadt', 'Basel-City', 'ch'),
            ('CH-BE', 'Bern', 'Bern', 'ch'),
            ('CH-FR', 'Fribourg', 'Fribourg', 'ch'),
            ('CH-GE', 'Genève', 'Geneva', 'ch'),
            ('CH-GL', 'Glarus', 'Glarus', 'ch'),
            ('CH-GR', 'Graubünden', 'Grisons', 'ch'),
            ('CH-JU', 'Jura', 'Jura', 'ch'),
            ('CH-LU', 'Luzern', 'Lucerne', 'ch'),
            ('CH-NE', 'Neuchâtel', 'Neuchâtel', 'ch'),
            ('CH-NW', 'Nidwalden', 'Nidwalden', 'ch'),
            ('CH-OW', 'Obwalden', 'Obwalden', 'ch'),
            ('CH-SH', 'Schaffhausen', 'Schaffhausen', 'ch'),
            ('CH-SZ', 'Schwyz', 'Schwyz', 'ch'),
            ('CH-SO', 'Solothurn', 'Solothurn', 'ch'),
            ('CH-SG', 'St. Gallen', 'St. Gallen', 'ch'),
            ('CH-TG', 'Thurgau', 'Thurgau', 'ch'),
            ('CH-TI', 'Ticino', 'Ticino', 'ch'),
            ('CH-UR', 'Uri', 'Uri', 'ch'),
            ('CH-VS', 'Valais', 'Valais', 'ch'),
            ('CH-VD', 'Vaud', 'Vaud', 'ch'),
            ('CH-ZG', 'Zug', 'Zug', 'ch'),
            ('CH-ZH', 'Zürich', 'Zurich', 'ch'),
            ('IT-65', 'Abruzzo', 'Abruzzo', 'it'),
            ('IT-77', 'Basilicata', 'Basilicata', 'it'),
            ('IT-78', 'Calabria', 'Calabria', 'it'),
            ('IT-72', 'Campania', 'Campania', 'it'),
            ('IT-45', 'Emilia-Romagna', 'Emilia-Romagna', 'it'),
            ('IT-36', 'Friuli Venezia Giulia', 'Friuli-Venezia Giulia', 'it'),
            ('IT-62', 'Lazio', 'Lazio', 'it'),
            ('IT-42', 'Liguria', 'Liguria', 'it'),
            ('IT-25', 'Lombardia', 'Lombardy', 'it'),
            ('IT-57', 'Marche', 'Marche', 'it'),
            ('IT-67', 'Molise', 'Molise', 'it'),
            ('IT-21', 'Piemonte', 'Piedmont', 'it'),
            ('IT-75', 'Puglia', 'Apulia', 'it'),
            ('IT-88', 'Sardegna', 'Sardinia', 'it'),
            ('IT-82', 'Sicilia', 'Sicily', 'it'),
            ('IT-52', 'Toscana', 'Tuscany', 'it'),
            ('IT-32', 'Trentino-Alto Adige', 'Trentino-South Tyrol', 'it'),
            ('IT-55', 'Umbria', 'Umbria', 'it'),
            ('IT-23', 'Valle d''Aosta', 'Aosta Valley', 'it'),
            ('IT-34', 'Veneto', 'Veneto', 'it'),
            ('IS-1', 'Höfuðborgarsvæði', 'Capital Region', 'is'),
            ('IS-2', 'Suðurnes', 'Southern Peninsula', 'is'),
            ('IS-3', 'Vesturland', 'West', 'is'),
            ('IS-4', 'Vestfirðir', 'Westfjords', 'is'),
            ('IS-5', 'Norðurland vestra', 'Northwestern Region', 'is'),
            ('IS-6', 'Norðurland eystra', 'Northeastern Region', 'is'),
            ('IS-7', 'Austurland', 'Eastern Region', 'is'),
            ('IS-8', 'Suðurland', 'Southern Region', 'is'),
            ('CZ-20', 'Středočeský kraj', 'Central Bohemian Region', 'cz'),
            ('CZ-31', 'Jihočeský kraj', 'South Bohemian Region', 'cz'),
            ('CZ-32', 'Plzeňský kraj', 'Plzeň Region', 'cz'),
            ('CZ-41', 'Karlovarský kraj', 'Karlovy Vary Region', 'cz'),
            ('CZ-42', 'Ústecký kraj', 'Ústí nad Labem Region', 'cz'),
            ('CZ-51', 'Liberecký kraj', 'Liberec Region', 'cz'),
            ('CZ-52', 'Královéhradecký kraj', 'Hradec Králové Region', 'cz'),
            ('CZ-53', 'Pardubický kraj', 'Pardubice Region', 'cz'),
            ('CZ-63', 'Kraj Vysočina', 'Vysočina Region', 'cz'),
            ('CZ-64', 'Jihomoravský kraj', 'South Moravian Region', 'cz'),
            ('CZ-71', 'Olomoucký kraj', 'Olomouc Region', 'cz'),
            ('CZ-72', 'Zlínský kraj', 'Zlín Region', 'cz'),
            ('CZ-80', 'Moravskoslezský kraj', 'Moravian-Silesian Region', 'cz'),
            ('AT-1', 'Burgenland', 'Burgenland', 'at'),
            ('AT-2', 'Kärnten', 'Carinthia', 'at'),
            ('AT-3', 'Niederösterreich', 'Lower Austria', 'at'),
            ('AT-4', 'Oberösterreich', 'Upper Austria', 'at'),
            ('AT-5', 'Salzburg', 'Salzburg', 'at'),
            ('AT-6', 'Steiermark', 'Styria', 'at'),
            ('AT-7', 'Tirol', 'Tyrol', 'at'),
            ('AT-8', 'Vorarlberg', 'Vorarlberg', 'at'),
            ('AT-9', 'Wien', 'Vienna', 'at'),
            ('SK-BL', 'Bratislavský kraj', 'Bratislava Region', 'sk'),
            ('SK-TA', 'Trnavský kraj', 'Trnava Region', 'sk'),
            ('SK-TC', 'Trenčiansky kraj', 'Trenčín Region', 'sk'),
            ('SK-NI', 'Nitriansky kraj', 'Nitra Region', 'sk'),
            ('SK-ZI', 'Žilinský kraj', 'Žilina Region', 'sk'),
            ('SK-BC', 'Banskobystrický kraj', 'Banská Bystrica Region', 'sk'),
            ('SK-PV', 'Prešovský Kraj', 'Prešov Region', 'sk'),
            ('SK-KI', 'Košický kraj', 'Košice Region', 'sk'),
            ('LI-01', 'Balzers', 'Balzers', 'li'),
            ('LI-02', 'Eschen', 'Eschen', 'li'),
            ('LI-03', 'Gamprin', 'Gamprin', 'li'),
            ('LI-04', 'Mauren', 'Mauren', 'li'),
            ('LI-05', 'Planken', 'Planken', 'li'),
            ('LI-06', 'Ruggell', 'Ruggell', 'li'),
            ('LI-07', 'Schaan', 'Schaan', 'li'),
            ('LI-08', 'Schellenberg', 'Schellenberg', 'li'),
            ('LI-09', 'Triesen', 'Triesen', 'li'),
            ('LI-10', 'Triesenberg', 'Triesenberg', 'li'),
            ('LI-11', 'Vaduz', 'Vaduz', 'li'),
        ]

        
        if not force and (Country.objects.exists() or Region.objects.exists()):
            self.stdout.write(self.style.WARNING(
                'Countries or regions already exist in the database. Use --force to override.'
            ))
            return

        try:
            with transaction.atomic():
                if force:
                    self.sync_countries(countries)
                    self.sync_regions(regions)
                else:
                    self.insert_countries(countries)
                    self.insert_regions(regions)
                
                self.stdout.write(self.style.SUCCESS('Successfully imported world travel data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {str(e)}'))

    def sync_countries(self, countries):
        country_codes = [code for _, code, _ in countries]
        Country.objects.exclude(country_code__in=country_codes).delete()
        
        for name, country_code, continent in countries:
            country, created = Country.objects.update_or_create(
                country_code=country_code,
                defaults={'name': name, 'continent': continent}
            )
            if created:
                saveCountryFlag(country_code)
                self.stdout.write(f'Inserted {name} into worldtravel countries')
            else:
                saveCountryFlag(country_code)
                self.stdout.write(f'Updated {name} in worldtravel countries')

    def sync_regions(self, regions):
        region_ids = [id for id, _, _, _ in regions]
        Region.objects.exclude(id__in=region_ids).delete()

        for id, name, name_en, country_code in regions:
            country = Country.objects.get(country_code=country_code)
            region, created = Region.objects.update_or_create(
                id=id,
                defaults={'name': name, 'country': country, 'name_en': name_en}
            )
            if created:
                self.stdout.write(f'Inserted {name} into worldtravel regions')
                setGeometry(id)
            else:
                setGeometry(id)
                self.stdout.write(f'Updated {name} in worldtravel regions')

    def insert_countries(self, countries):
        for name, country_code, continent in countries:
            country, created = Country.objects.get_or_create(
                country_code=country_code,
                defaults={'name': name, 'continent': continent}
            )
            if created:
                saveCountryFlag(country_code)
                
                self.stdout.write(f'Inserted {name} into worldtravel countries')
            else:
                saveCountryFlag(country_code)
                self.stdout.write(f'{name} already exists in worldtravel countries')

    def insert_regions(self, regions):
        for id, name, name_en, country_code in regions:
            country = Country.objects.get(country_code=country_code)
            region, created = Region.objects.get_or_create(
                id=id,
                defaults={'name': name, 'country': country, 'name_en': name_en}
            )
            if created:
                self.stdout.write(f'Inserted {name} into worldtravel regions')
                setGeometry(id)
            else:
                setGeometry(id)
                self.stdout.write(f'{name} already exists in worldtravel regions')