"""
Service de détection de landmarks pour améliorer la précision de la détection de pays
"""
from transformers import CLIPProcessor, CLIPModel
from PIL import Image, ImageFile, ImageOps
from io import BytesIO
import torch
import logging

logger = logging.getLogger(__name__)
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Mapping landmarks → pays (200+ monuments touristiques mondiaux)
LANDMARKS_BY_COUNTRY = {
    "France": [
        "Eiffel Tower", "Arc de Triomphe", "Louvre Museum", "Notre-Dame Cathedral",
        "Sacré-Cœur", "Versailles Palace", "Mont Saint-Michel", "Champs-Élysées",
        "Moulin Rouge", "Palace of Versailles", "Pont Alexandre III", "Panthéon Paris",
        "Musée d'Orsay", "Palais Garnier", "Sainte-Chapelle", "Conciergerie",
        "Château de Chambord", "Pont du Gard", "Carcassonne medieval city",
        "Côte d'Azur", "French Riviera", "Cannes", "Nice Promenade",
        "Strasbourg Cathedral", "Lyon Old Town"
    ],
    "Italy": [
        "Colosseum", "Leaning Tower of Pisa", "Venice canals", "Trevi Fountain",
        "Vatican", "Duomo di Milano", "Ponte Vecchio", "St. Peter's Basilica",
        "Sistine Chapel", "Roman Forum", "Pantheon Rome", "Piazza San Marco",
        "Rialto Bridge", "Grand Canal Venice", "Florence Cathedral", "Uffizi Gallery",
        "Pompeii ruins", "Mount Vesuvius", "Amalfi Coast", "Cinque Terre",
        "Lake Como", "Dolomites mountains", "Verona Arena", "Piazza del Campo Siena",
        "Milan Cathedral", "Bologna towers", "Trulli houses Alberobello"
    ],
    "Spain": [
        "Sagrada Familia", "Alhambra", "Park Güell", "Plaza Mayor Madrid",
        "Mezquita Cordoba", "Seville Cathedral", "Giralda tower", "Casa Batlló",
        "La Pedrera", "Prado Museum", "Royal Palace Madrid", "Guggenheim Bilbao",
        "Santiago de Compostela Cathedral", "Alcázar of Seville", "Toledo Cathedral",
        "Montserrat monastery", "Ronda bridge", "Segovia Aqueduct", "Plaza de España",
        "Las Ramblas Barcelona", "Camp Nou stadium", "Ibiza beaches"
    ],
    "United Kingdom": [
        "Big Ben", "Tower Bridge", "Buckingham Palace", "Stonehenge",
        "Edinburgh Castle", "London Eye", "Westminster Abbey", "Tower of London",
        "British Museum", "St Paul's Cathedral", "Windsor Castle", "Trafalgar Square",
        "Piccadilly Circus", "Houses of Parliament", "Kensington Palace",
        "Giant's Causeway", "Loch Ness", "Scottish Highlands", "Cambridge University",
        "Oxford University", "Canterbury Cathedral", "Bath Roman Baths", "Hadrian's Wall"
    ],
    "United States": [
        "Statue of Liberty", "Golden Gate Bridge", "Empire State Building",
        "White House", "Hollywood Sign", "Mount Rushmore", "Grand Canyon",
        "Niagara Falls", "Times Square", "Brooklyn Bridge", "Central Park",
        "Las Vegas Strip", "Space Needle Seattle", "Gateway Arch St Louis",
        "Alcatraz Island", "Monument Valley", "Yellowstone geysers", "Yosemite",
        "Disney World Castle", "Miami Beach", "French Quarter New Orleans",
        "Liberty Bell Philadelphia", "Alamo San Antonio", "Boston Harbor"
    ],
    "Egypt": [
        "Pyramids of Giza", "Sphinx", "Abu Simbel", "Karnak Temple",
        "Valley of the Kings", "Luxor Temple", "Egyptian Museum Cairo",
        "Khan el-Khalili bazaar", "Philae Temple", "Aswan Dam", "Nile River",
        "Colossi of Memnon", "Hatshepsut Temple", "Edfu Temple", "Kom Ombo Temple"
    ],
    "China": [
        "Great Wall of China", "Forbidden City", "Terracotta Army",
        "Shanghai skyline", "Temple of Heaven", "Summer Palace Beijing",
        "Bund Shanghai", "Oriental Pearl Tower", "Li River Guilin",
        "Potala Palace Tibet", "West Lake Hangzhou", "Zhangjiajie mountains",
        "Giant Panda sanctuaries", "Longmen Grottoes", "Leshan Giant Buddha",
        "Hong Kong skyline", "Victoria Harbour", "Macau casinos"
    ],
    "India": [
        "Taj Mahal", "Red Fort", "Gateway of India", "Hawa Mahal",
        "Amber Fort Jaipur", "Golden Temple Amritsar", "Qutub Minar",
        "India Gate Delhi", "Lotus Temple", "Humayun's Tomb", "Akshardham Temple",
        "Mysore Palace", "Meenakshi Temple", "Hampi ruins", "Ajanta Caves",
        "Ellora Caves", "Kerala backwaters", "Ganges River Varanasi", "Jain temples"
    ],
    "Greece": [
        "Parthenon", "Acropolis", "Santorini white buildings", "Mykonos windmills",
        "Meteora monasteries", "Delphi ruins", "Olympia archaeological site",
        "Knossos Palace Crete", "Rhodes Old Town", "Thessaloniki White Tower",
        "Corinth Canal", "Zakynthos Navagio Beach", "Mount Olympus", "Corfu Old Town"
    ],
    "Germany": [
        "Brandenburg Gate", "Neuschwanstein Castle", "Cologne Cathedral",
        "Berlin Wall", "Reichstag Berlin", "Marienplatz Munich", "Heidelberg Castle",
        "Rothenburg ob der Tauber", "Black Forest", "Rhine Valley castles",
        "Dresden Frauenkirche", "Checkpoint Charlie", "Oktoberfest Munich",
        "Hamburg Speicherstadt", "Miniatur Wunderland"
    ],
    "Brazil": [
        "Christ the Redeemer", "Sugarloaf Mountain", "Iguazu Falls",
        "Copacabana Beach", "Ipanema Beach", "Amazon Rainforest", "Carnival Rio",
        "São Paulo skyline", "Pelourinho Salvador", "Fernando de Noronha",
        "Pantanal wetlands", "Lençóis Maranhenses sand dunes"
    ],
    "Australia": [
        "Sydney Opera House", "Sydney Harbour Bridge", "Uluru",
        "Great Barrier Reef", "Twelve Apostles", "Bondi Beach", "Melbourne skyline",
        "Blue Mountains", "Kakadu National Park", "Fraser Island", "Whitsunday Islands",
        "Tasmania wilderness", "Perth beaches", "Daintree Rainforest"
    ],
    "Japan": [
        "Mount Fuji", "Tokyo Tower", "Fushimi Inari Shrine", "Shibuya Crossing",
        "Senso-ji Temple Tokyo", "Kinkaku-ji Golden Pavilion", "Osaka Castle",
        "Hiroshima Peace Memorial", "Miyajima Torii Gate", "Nara deer park",
        "Kyoto bamboo forest", "Tokyo Skytree", "Himeji Castle", "Nikko shrines",
        "Hakone hot springs", "Takayama old town", "Sapporo Snow Festival"
    ],
    "Netherlands": [
        "Amsterdam canals", "windmills Kinderdijk", "tulip fields Keukenhof",
        "Anne Frank House", "Van Gogh Museum", "Rijksmuseum", "Dam Square",
        "Zaanse Schans windmills", "Rotterdam modern architecture", "Delft pottery",
        "Giethoorn village", "Markthal Rotterdam", "Cube houses"
    ],
    "Russia": [
        "Saint Basil's Cathedral", "Kremlin", "Red Square Moscow",
        "Hermitage Museum", "Church of the Savior on Blood", "Peterhof Palace",
        "Trans-Siberian Railway", "Lake Baikal", "Moscow Metro stations",
        "Bolshoi Theatre", "Catherine Palace", "Kazan Kremlin"
    ],
    "United Arab Emirates": [
        "Burj Khalifa", "Burj Al Arab", "Sheikh Zayed Mosque",
        "Dubai Marina", "Palm Jumeirah", "Dubai Mall", "Dubai Fountain",
        "Louvre Abu Dhabi", "Ferrari World", "Atlantis Hotel", "Jumeirah Mosque"
    ],
    "Turkey": [
        "Hagia Sophia", "Blue Mosque Istanbul", "Cappadocia hot air balloons",
        "Pamukkale travertines", "Ephesus ruins", "Topkapi Palace", "Grand Bazaar",
        "Bosphorus Bridge", "Troy ruins", "Mount Nemrut statues", "Sumela Monastery"
    ],
    "Thailand": [
        "Grand Palace Bangkok", "Wat Arun", "Wat Pho reclining Buddha",
        "Phi Phi Islands", "Maya Bay", "Phuket beaches", "Chiang Mai temples",
        "Ayutthaya ruins", "Floating markets", "James Bond Island", "Railay Beach"
    ],
    "Mexico": [
        "Chichen Itza", "Teotihuacan pyramids", "Tulum ruins", "Frida Kahlo Museum",
        "Palacio de Bellas Artes", "Chapultepec Castle", "Zócalo Mexico City",
        "Xcaret Park", "Cenotes Yucatan", "Copper Canyon", "Guanajuato colored houses"
    ],
    "Peru": [
        "Machu Picchu", "Rainbow Mountain", "Nazca Lines", "Sacred Valley",
        "Lake Titicaca", "Cusco Plaza de Armas", "Sacsayhuaman", "Colca Canyon",
        "Amazon rainforest Peru", "Huacachina oasis"
    ],
    "Canada": [
        "CN Tower Toronto", "Niagara Falls Canada", "Banff National Park",
        "Lake Louise", "Old Quebec", "Parliament Hill Ottawa", "Vancouver skyline",
        "Stanley Park", "Jasper National Park", "Moraine Lake", "Rocky Mountains"
    ],
    "Switzerland": [
        "Matterhorn", "Jungfraujoch", "Chapel Bridge Lucerne", "Chillon Castle",
        "Rhine Falls", "Zermatt village", "Lake Geneva", "Interlaken", "Swiss Alps"
    ],
    "Portugal": [
        "Belém Tower", "Jerónimos Monastery", "Pena Palace Sintra", "Porto Ribeira",
        "São Jorge Castle", "Benagil Cave", "Douro Valley", "Cabo da Roca",
        "Algarve cliffs", "Tram 28 Lisbon"
    ],
    "Austria": [
        "Schönbrunn Palace", "St. Stephen's Cathedral Vienna", "Hofburg Palace",
        "Salzburg Old Town", "Hallstatt village", "Belvedere Palace", "Vienna State Opera"
    ],
    "Morocco": [
        "Jemaa el-Fnaa Marrakech", "Hassan II Mosque", "Chefchaouen blue city",
        "Ait Benhaddou", "Fes medina", "Sahara Desert dunes", "Majorelle Garden"
    ],
    "Argentina": [
        "Iguazu Falls Argentina", "Perito Moreno Glacier", "Obelisco Buenos Aires",
        "Casa Rosada", "Ushuaia", "Patagonia", "La Boca neighborhood"
    ],
    "South Africa": [
        "Table Mountain", "Robben Island", "Kruger National Park", "Cape of Good Hope",
        "Victoria & Alfred Waterfront", "Blyde River Canyon", "Garden Route"
    ],
    "Iceland": [
        "Blue Lagoon", "Gullfoss waterfall", "Geysir", "Jökulsárlón glacier lagoon",
        "Hallgrímskirkja church", "Northern Lights Iceland", "Black sand beaches Vik"
    ],
    "Norway": [
        "Geirangerfjord", "Preikestolen cliff", "Tromsø northern lights",
        "Bergen Bryggen", "Lofoten Islands", "Trolltunga", "Atlantic Ocean Road"
    ],
    "Sweden": [
        "Vasa Museum", "Stockholm Old Town", "Ice Hotel Kiruna", "Göta Canal",
        "Abisko National Park", "Drottningholm Palace"
    ],
    "New Zealand": [
        "Milford Sound", "Hobbiton movie set", "Mount Cook", "Sky Tower Auckland",
        "Waitomo Glowworm Caves", "Queenstown", "Tongariro Crossing", "Fox Glacier"
    ],
    "Singapore": [
        "Marina Bay Sands", "Gardens by the Bay", "Merlion statue", "Sentosa Island",
        "Supertree Grove", "Clarke Quay", "Singapore Flyer"
    ],
    "Vietnam": [
        "Ha Long Bay", "Hoi An Ancient Town", "Cu Chi Tunnels", "Mekong Delta",
        "Hue Imperial City", "Sapa rice terraces", "One Pillar Pagoda Hanoi"
    ],
    "Indonesia": [
        "Borobudur Temple", "Prambanan Temple", "Bali rice terraces", "Tanah Lot",
        "Mount Bromo", "Komodo dragons", "Ubud monkey forest", "Uluwatu Temple"
    ],
    "Malaysia": [
        "Petronas Towers", "Batu Caves", "George Town Penang", "Langkawi",
        "Mount Kinabalu", "Malacca Dutch Square"
    ],
    "South Korea": [
        "Gyeongbokgung Palace", "N Seoul Tower", "Bukchon Hanok Village",
        "Jeju Island", "DMZ Korea", "Lotte World Tower", "Busan beaches"
    ],
    "Jordan": [
        "Petra", "Wadi Rum desert", "Dead Sea", "Jerash ruins", "Amman Citadel"
    ],
    "Israel": [
        "Western Wall Jerusalem", "Dome of the Rock", "Masada fortress",
        "Tel Aviv beaches", "Dead Sea Israel", "Bahai Gardens Haifa"
    ],
    "Croatia": [
        "Dubrovnik Old Town", "Plitvice Lakes", "Diocletian's Palace Split",
        "Hvar Island", "Zagreb Upper Town", "Krka waterfalls"
    ],
    "Czech Republic": [
        "Prague Castle", "Charles Bridge", "Old Town Square Prague",
        "Astronomical Clock", "Karlštejn Castle", "Český Krumlov"
    ],
    "Poland": [
        "Auschwitz-Birkenau", "Wawel Castle Krakow", "Warsaw Old Town",
        "Wieliczka Salt Mine", "Malbork Castle", "Tatra Mountains"
    ],
    "Hungary": [
        "Hungarian Parliament", "Buda Castle", "Fisherman's Bastion",
        "Széchenyi Thermal Bath", "Chain Bridge Budapest", "Matthias Church"
    ],
    "Ireland": [
        "Cliffs of Moher", "Trinity College Dublin", "Giant's Causeway Ireland",
        "Ring of Kerry", "Blarney Castle", "Guinness Storehouse", "Temple Bar Dublin"
    ],
    "Belgium": [
        "Grand Place Brussels", "Atomium", "Manneken Pis", "Bruges canals",
        "Ghent Castle", "Antwerp Cathedral", "Brussels Town Hall"
    ],
}

def detect_landmark_country(image_bytes: bytes, model=None, processor=None) -> dict:
    """
    Détecte un landmark dans l'image et retourne le pays associé
    
    Returns:
        dict: {
            'country': str,
            'landmark': str,
            'confidence': float,
            'method': 'landmark'
        } ou None si aucun landmark détecté avec confiance > seuil
    """
    try:
        # Charger le modèle si pas fourni
        if model is None or processor is None:
            from ai_services.clip_service import _get_model_and_processor
            model, processor = _get_model_and_processor()
        
        # Préparer l'image (supporte bytes ou BytesIO)
        try:
            # Normaliser le buffer
            if hasattr(image_bytes, "read"):
                buffer = image_bytes
                try:
                    buffer.seek(0)
                except Exception:
                    pass
            else:
                buffer = BytesIO(image_bytes)
            
            # Première tentative
            image = Image.open(buffer)
            image = ImageOps.exif_transpose(image)
            image.load()
            image = image.convert("RGB")
        except Exception as e:
            # Deuxième tentative avec ré-ouverture
            try:
                raw = image_bytes.getvalue() if hasattr(image_bytes, "getvalue") else image_bytes
                buffer2 = BytesIO(raw)
                image = Image.open(buffer2)
                image = ImageOps.exif_transpose(image)
                image.load()
                image = image.convert("RGB")
            except Exception as e2:
                size_info = len(raw) if isinstance(raw, (bytes, bytearray)) else 'unknown'
                logger.error(f"Impossible de charger l'image: {e2} (taille={size_info})")
                return None
        
        # Créer la liste de tous les landmarks
        all_landmarks = []
        landmark_to_country = {}
        
        for country, landmarks in LANDMARKS_BY_COUNTRY.items():
            for landmark in landmarks:
                all_landmarks.append(landmark)
                landmark_to_country[landmark] = country
        
        # Encoder l'image
        image_inputs = processor(images=[image], return_tensors="pt")
        image_inputs = {k: v.to("cuda" if torch.cuda.is_available() else "cpu") 
                       for k, v in image_inputs.items()}
        
        # Tester les landmarks par batch de 20 pour performance
        best_landmark = None
        best_score = 0.0
        
        batch_size = 20
        for i in range(0, len(all_landmarks), batch_size):
            batch_landmarks = all_landmarks[i:i+batch_size]
            prompts = [f"a photo of {landmark}" for landmark in batch_landmarks]
            
            with torch.no_grad():
                # Encoder les textes
                text_inputs = processor(text=prompts, return_tensors="pt", padding=True, truncation=True)
                text_inputs = {k: v.to("cuda" if torch.cuda.is_available() else "cpu") 
                              for k, v in text_inputs.items()}
                
                # Obtenir les features
                image_features = model.get_image_features(**image_inputs)
                text_features = model.get_text_features(**text_inputs)
                
                # Normaliser
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                # Calculer similarités
                similarities = (image_features @ text_features.T)[0]
                
                # Trouver le meilleur dans ce batch
                batch_best_idx = similarities.argmax().item()
                batch_best_score = similarities[batch_best_idx].item()
                
                if batch_best_score > best_score:
                    best_score = batch_best_score
                    best_landmark = batch_landmarks[batch_best_idx]
        
        # Seuil de confiance pour landmark (ajusté pour être un peu plus tolérant)
        logger.debug(f"Best landmark candidate: {best_landmark} with score={best_score:.4f}")
        if best_score > 0.22:
            country = landmark_to_country[best_landmark]
            logger.info(f"Landmark détecté: {best_landmark} ({country}) - confiance: {best_score:.4f}")
            
            return {
                'country': country,
                'landmark': best_landmark,
                'confidence': float(best_score),
                'method': 'landmark'
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Erreur lors de la détection de landmark: {e}")
        return None
