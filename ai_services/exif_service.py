from PIL import Image, ExifTags
from io import BytesIO
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

def extract_gps(image_bytes):
    """
    Extrait les coordonnées GPS depuis les métadonnées EXIF d'une image
    
    Args:
        image_bytes: Bytes de l'image
        
    Returns:
        tuple: (latitude, longitude) en degrés décimaux ou (None, None) si non trouvé
    """
    try:
        image = Image.open(BytesIO(image_bytes))
        
        if not hasattr(image, '_getexif') or image._getexif() is None:
            return None, None
            
        exif = {ExifTags.TAGS[k]: v for k, v in image._getexif().items() 
               if k in ExifTags.TAGS and isinstance(k, int)}
        
        if 'GPSInfo' not in exif:
            return None, None
            
        gps_info = exif['GPSInfo']
        
        # Extraction de la latitude
        lat_data = gps_info.get(2, None)
        lat_ref = gps_info.get(1, 'N')
        
        # Extraction de la longitude
        lon_data = gps_info.get(4, None)
        lon_ref = gps_info.get(3, 'E')
        
        if not all([lat_data, lon_data]):
            return None, None
            
        # Conversion des coordonnées DMS en degrés décimaux
        def dms_to_decimal(dms, ref):
            degrees = dms[0][0] / dms[0][1]
            minutes = dms[1][0] / dms[1][1] / 60.0
            seconds = dms[2][0] / dms[2][1] / 3600.0
            result = degrees + minutes + seconds
            if ref in ['S', 'W']:
                result = -result
            return result
            
        lat = dms_to_decimal(lat_data, lat_ref)
        lon = dms_to_decimal(lon_data, lon_ref)
        
        return lat, lon
        
    except Exception as e:
        print(f"Erreur lors de l'extraction GPS: {e}")
        return None, None

def reverse_geocode(lat, lng, max_retries=3):
    """
    Effectue un reverse geocoding pour obtenir le pays à partir de coordonnées GPS
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        max_retries (int): Nombre de tentatives en cas d'échec
        
    Returns:
        dict: {'country_code': str, 'country_name': str} ou None en cas d'échec
    """
    geolocator = Nominatim(user_agent="socialite")
    
    for attempt in range(max_retries):
        try:
            location = geolocator.reverse((lat, lng), language="en", exactly_one=True)
            if location and 'address' in location.raw:
                address = location.raw['address']
                return {
                    'country_code': address.get('country_code', '').upper(),
                    'country_name': address.get('country', '')
                }
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt == max_retries - 1:
                print(f"Échec du géocodage après {max_retries} tentatives: {e}")
                return None
            time.sleep(1)  # Attente avant une nouvelle tentative
            
    return None
