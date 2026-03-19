import pandas as pd
import re
import streamlit as st
import math
import time
import os

DEPT_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "20": "Corse",
    "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir",
    "29": "Finistère", "30": "Gard", "31": "Haute-Garonne", "32": "Gers",
    "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre",
    "37": "Indre-et-Loire", "38": "Isère", "39": "Jura", "40": "Landes",
    "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique",
    "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère",
    "49": "Maine-et-Loire", "50": "Manche", "51": "Marne", "52": "Haute-Marne",
    "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse", "56": "Morbihan",
    "57": "Moselle", "58": "Nièvre", "59": "Nord", "60": "Oise", "61": "Orne",
    "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin",
    "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire",
    "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie", "75": "Paris",
    "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines",
    "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne",
    "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise",
}

DEPT_CENTROIDS = {
    "01":(46.2,5.2),"02":(49.5,3.6),"03":(46.3,3.1),"04":(44.1,6.2),
    "05":(44.7,6.4),"06":(43.9,7.2),"07":(44.8,4.5),"08":(49.7,4.7),
    "09":(42.9,1.6),"10":(48.3,4.1),"11":(43.1,2.4),"12":(44.3,2.6),
    "13":(43.5,5.4),"14":(49.1,-0.4),"15":(45.0,2.6),"16":(45.7,0.2),
    "17":(45.7,-0.9),"18":(47.1,2.4),"19":(45.4,1.9),"20":(42.0,9.0),
    "21":(47.3,4.8),"22":(48.4,-2.8),"23":(46.0,2.0),"24":(45.1,0.7),
    "25":(47.2,6.4),"26":(44.8,5.0),"27":(49.1,1.2),"28":(48.4,1.4),
    "29":(48.2,-4.0),"30":(44.0,4.2),"31":(43.6,1.4),"32":(43.6,0.6),
    "33":(44.8,-0.6),"34":(43.6,3.5),"35":(48.1,-1.7),"36":(46.8,1.6),
    "37":(47.2,0.7),"38":(45.2,5.7),"39":(46.7,5.5),"40":(43.9,-0.8),
    "41":(47.6,1.3),"42":(45.5,4.2),"43":(45.1,3.9),"44":(47.3,-1.6),
    "45":(47.9,2.1),"46":(44.6,1.7),"47":(44.4,0.6),"48":(44.5,3.5),
    "49":(47.4,-0.6),"50":(49.1,-1.3),"51":(49.0,4.0),"52":(48.0,5.4),
    "53":(48.1,-0.7),"54":(48.7,6.2),"55":(49.0,5.3),"56":(47.8,-2.9),
    "57":(49.0,6.6),"58":(47.1,3.5),"59":(50.5,3.2),"60":(49.4,2.5),
    "61":(48.6,0.1),"62":(50.5,2.6),"63":(45.8,3.1),"64":(43.3,-0.8),
    "65":(43.2,0.1),"66":(42.6,2.8),"67":(48.6,7.7),"68":(47.8,7.3),
    "69":(45.8,4.8),"70":(47.6,6.1),"71":(46.6,4.5),"72":(48.0,0.2),
    "73":(45.5,6.4),"74":(46.0,6.4),"75":(48.9,2.3),"76":(49.7,1.1),
    "77":(48.6,3.0),"78":(48.8,1.8),"79":(46.5,-0.4),"80":(49.9,2.3),
    "81":(43.9,2.1),"82":(44.0,1.3),"83":(43.5,6.2),"84":(44.0,5.1),
    "85":(46.7,-1.4),"86":(46.6,0.3),"87":(45.8,1.3),"88":(48.2,6.4),
    "89":(47.8,3.6),"90":(47.6,6.9),"91":(48.6,2.3),"92":(48.9,2.2),
    "93":(48.9,2.5),"94":(48.8,2.5),"95":(49.1,2.1),
}


def extract_cp(addr):
    if pd.isna(addr):
        return None
    m = re.search(r"\b(\d{5})\b", str(addr))
    return m.group(1) if m else None


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def _extract_city(nom):
    """Extract city/quartier from 'Human Immobilier <City>'."""
    import re as _re
    m = _re.search(r'[Hh][Uu][Mm][Aa][Nn]\s+[Ii]mmobilier\s+(.+)', str(nom), _re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
        raw = _re.sub(r'\s*[-–]\s*(Gestion\s+locative|Transaction|Copropriété).*$', '', raw, flags=_re.IGNORECASE)
        return raw.strip()
    return None

# City-level GPS lookup built from agency name patterns
_CITY_GPS = {
    "Arcachon":(44.658,-1.1685),"Arcachon Centre":(44.658,-1.1685),"Arcachon Aiguillon":(44.658,-1.1685),
    "Andernos":(44.7386,-1.1028),"Arès":(44.7617,-1.1403),"Audenge":(44.6876,-1.0249),
    "Biganos":(44.6587,-0.9756),"Biscarrosse":(44.395,-1.165),"Blanquefort":(44.9115,-0.6405),
    "Bordeaux":(44.8378,-0.5792),"Bordeaux Bacalan":(44.8622,-0.5706),"Bordeaux Bastide":(44.8378,-0.5592),
    "Bordeaux Caudéran":(44.8503,-0.6214),"Bordeaux Chartrons":(44.8528,-0.58),
    "Bordeaux Nansouty":(44.8278,-0.5892),"Bordeaux Ornano":(44.8278,-0.5692),
    "Bordeaux St Genès":(44.8278,-0.5792),"Bordeaux St-Seurin":(44.8478,-0.5992),
    "Bordeaux Tourny":(44.8428,-0.5792),"Bordeaux Alsace-Lorraine":(44.8378,-0.5792),
    "Bordeaux Rive Droite":(44.8378,-0.5592),"Bordeaux St Jean":(44.8278,-0.5492),
    "Bruges":(44.8817,-0.6358),"Carbon Blanc":(44.9003,-0.4919),"Castelnau de Médoc":(45.0338,-0.8122),
    "Cenon":(44.8603,-0.5167),"Cestas":(44.7451,-0.7012),"Claouey":(44.6933,-1.1806),
    "Créon":(44.7745,-0.3434),"Eysines":(44.8886,-0.6708),"Floirac":(44.8433,-0.5083),
    "Gradignan":(44.7753,-0.6118),"Gujan Mestras":(44.6358,-1.0676),"Gujan-Mestras":(44.6358,-1.0676),
    "Gujan Mestras La Hume":(44.6022,-1.0497),"Hourtin":(45.1817,-1.0622),
    "La Brède":(44.6841,-0.5191),"La Teste":(44.6264,-1.1011),"Lacanau":(45.0019,-1.1942),
    "Lacanau Océan":(45.0019,-1.1942),"Langon":(44.555,-0.252),"Langoiran":(44.7267,-0.4028),
    "Latresne":(44.76,-0.46),"Le Bouscat":(44.8619,-0.6053),"Le Canon":(44.6886,-1.225),
    "Le Haillan":(44.8677,-0.6855),"Le Taillan Médoc":(44.9177,-0.6983),"Le Teich":(44.6408,-1.0222),
    "Léognan":(44.7316,-0.5983),"Lesparre":(45.3064,-0.9305),"Libourne":(44.9189,-0.2425),
    "Lormont":(44.8861,-0.5244),"Marcheprime":(44.6903,-0.8897),"Mérignac":(44.8388,-0.6444),
    "Mérignac Centre":(44.8388,-0.6444),"Mérignac Chemin long":(44.8388,-0.6444),
    "Mios":(44.5986,-0.9311),"Pauillac":(45.1989,-0.7494),"Pessac":(44.8064,-0.6306),
    "Pessac Alouette":(44.8064,-0.6306),"Pessac Centre":(44.8064,-0.6306),
    "Sanguinet":(44.4836,-1.0783),"Soulac-sur-Mer":(45.5042,-1.1289),
    "St André de Cubzac":(45.0008,-0.4481),"St Jean d'Illac":(44.8256,-0.7611),
    "St Loubès":(44.9211,-0.4022),"St Médard en Jalles":(44.8981,-0.7297),
    "Talence":(44.8003,-0.59),"Vayres":(44.93,-0.33),"Villenave d'Ornon":(44.7822,-0.5625),
    "Ambarès":(44.9267,-0.4794),"Artigues-près-Bordeaux":(44.8528,-0.48),"Bazas":(44.4317,-0.2136),
    "Branne":(44.8261,-0.1906),"Cadillac":(44.6358,-0.3206),"Canéjan":(44.7686,-0.6647),
    "Castillon La Bataille":(44.8531,-0.0453),"Coutras":(45.0406,-0.1284),
    "Capbreton":(43.6419,-1.4453),"Dax":(43.71,-1.0528),"Hagetmau":(43.6581,-0.5922),
    "Labouheyre":(44.2133,-0.9228),"Labenne":(43.5981,-1.4492),"Léon":(43.8792,-1.3122),
    "Mimizan":(44.2006,-1.2317),"Mont-de-Marsan":(43.8905,-0.5003),"Morcenx la nouvelle":(44.0375,-0.8881),
    "Peyrehorade":(43.5494,-1.1072),"Roquefort":(44.0194,-0.3269),"Soustons":(43.7533,-1.3258),
    "St Paul les Dax":(43.7281,-1.0494),"St Sever":(43.7578,-0.5706),
    "St Vincent de Tyrosse":(43.6617,-1.3294),"Tartas":(43.8336,-0.8086),
    "Tarnos":(43.5453,-1.4597),"Vieux Boucau":(43.7981,-1.3997),"Castets":(43.8767,-1.1494),
    "Parentis-en-Born":(44.3486,-1.0825),
    "Anglet":(43.4894,-1.5194),"Artix":(43.4489,-0.6181),"Bayonne":(43.4929,-1.4748),
    "Bayonne Foch":(43.4929,-1.4748),"Bayonne les Halles":(43.4929,-1.4748),
    "Bayonne St Esprit":(43.5006,-1.4719),"Biarritz":(43.4832,-1.5586),
    "Biarritz Centre":(43.4832,-1.5586),"Lescar":(43.3478,-0.4297),
    "Orthez":(43.4867,-0.7714),"Pau":(43.2951,-0.3708),"Pau Centre":(43.2951,-0.3708),
    "Pau Croix du Prince":(43.2951,-0.3708),"Salies de Béarn":(43.4725,-0.9328),
    "Soumoulou":(43.3531,-0.3531),"Saint Jean de Luz":(43.3875,-1.6606),
    "Bagnères-de-Bigorre":(43.065,0.1489),"Lourdes":(43.095,-0.0483),
    "Rabastens de Bigorre":(43.3842,0.11),"Tarbes":(43.2328,0.0781),
    "Séméac":(43.25,0.0833),"Semeac":(43.25,0.0833),"Luz-Saint-Sauveur":(42.8706,-0.0044),
    "Aigrefeuille-d'Aunis":(46.1261,-0.9394),"Aytré":(46.1278,-1.1111),
    "Châtelaillon-Plage":(46.0764,-1.085),"Cognac":(45.6942,-0.3292),
    "Fouras":(45.9814,-1.0883),"Jonzac":(45.4422,-0.4317),"La Flotte en Ré":(46.1917,-1.3225),
    "La Rochelle":(46.1591,-1.152),"La Rochelle Marché":(46.1591,-1.152),
    "La Rochelle Tasdon":(46.1491,-1.162),"La Rochelle Vieux Port":(46.1591,-1.152),
    "La Rochelle la Genette":(46.1591,-1.152),"La Tremblade":(45.7739,-1.1408),
    "Marans":(46.3072,-0.9992),"Marennes":(45.8211,-1.1089),"Matha":(45.8681,-0.3131),
    "Meschers sur Gironde":(45.5558,-0.9528),"Mirambeau":(45.3756,-0.5658),
    "Montendre":(45.2847,-0.4175),"Montguyon":(45.2106,-0.1853),"Nieul-sur-Mer":(46.2103,-1.1867),
    "Pons":(45.5794,-0.5497),"Pont-l'Abbé-d'Arnoult":(45.7944,-0.8758),
    "Puilboreau":(46.1794,-1.1122),"Rochefort":(45.9381,-0.9589),"Royan":(45.6228,-1.0253),
    "Royan Grande Conche":(45.6228,-1.0253),"Royan Port":(45.6228,-1.0253),
    "Saintes":(45.7458,-0.6319),"Saintes Rive Droite":(45.7458,-0.6319),
    "Saintes Rive Gauche":(45.7458,-0.6319),"Saujon":(45.6786,-0.9281),
    "St Denis d'Oléron":(46.0253,-1.3664),"St Georges de didonne":(45.6003,-1.0069),
    "St Jean d'Angély":(45.9475,-0.5194),"St Pierre d'Oléron":(45.9486,-1.3153),
    "Le Château d'Oléron":(45.8928,-1.1978),"Surgères":(46.1036,-0.7522),
    "Tonnay Charente":(45.9464,-0.8978),"Vaux sur Mer":(45.6428,-1.0594),
    "Angoulême":(45.6489,0.1583),"Angoulême Bussatte":(45.6489,0.1583),
    "Angoulême Hôtel de ville":(45.6489,0.1583),"Angoulême St Cybard":(45.6489,0.1583),
    "Barbezieux St Hilaire":(45.4742,-0.1558),"Châteauneuf sur Charente":(45.5975,0.0503),
    "Cognac St Jacques":(45.6942,-0.3292),"Cognac Victor Hugo":(45.6942,-0.3292),
    "Confolens":(46.0156,0.6711),"Jarnac":(45.6814,-0.1742),"La Couronne":(45.5981,0.0694),
    "La Rochefoucauld":(45.7356,0.3775),"Montbron":(45.6742,0.4978),"Rouillac":(45.7844,-0.07),
    "Ruelle Sur Touvre":(45.6806,0.2239),"Ruffec":(46.0211,0.1886),"Soyaux":(45.6383,0.1875),
    "Bergerac":(44.85,0.4814),"Brantôme":(45.365,0.6486),"Brive La Gaillarde":(45.1583,1.5317),
    "Brive-La-Gaillarde":(45.1583,1.5317),"Lalinde":(44.8333,0.7344),"Le Bugue":(44.92,0.9281),
    "Montignac sur Vézère":(45.0644,1.1617),"Montpon Ménestérol":(45.0072,0.1617),
    "Mussidan":(45.0331,0.3675),"Nontron":(45.5244,0.6658),"Objat":(45.2706,1.4056),
    "Périgueux":(45.1847,0.7208),"Périgueux St Georges":(45.1847,0.7208),
    "Périgueux Wilson":(45.1847,0.7208),"Prigonrieux":(44.8672,0.5317),"Ribérac":(45.2442,0.3392),
    "Sarlat la Canéda":(44.8897,1.2169),"Souillac":(44.89,1.4733),"St Astier":(45.1464,0.5233),
    "Terrasson":(45.1358,1.3019),"Thiviers":(45.4175,0.9119),"Trélissac":(45.2014,0.7631),
    "Vergt":(45.0294,0.7244),"Excideuil":(45.3283,1.0011),"Le Lardin St Lazare":(45.1317,1.2831),
    "Montmoreau":(45.4006,0.1231),"Audierne":(48.0253,-4.5369),"Benodet":(47.875,-4.1122),
    "Brest":(48.3904,-4.4861),"Brest Bellevue":(48.3904,-4.4861),"Brest Centre":(48.3904,-4.4861),
    "Brest Lambézellec":(48.4053,-4.5156),"Brest Recouvrance":(48.3953,-4.5061),
    "Brest St Marc":(48.3754,-4.5261),"Carhaix-Plouguer":(48.275,-3.5756),
    "Châteaulin":(48.1922,-4.0867),"Châteauneuf du Faou":(48.1906,-3.8228),
    "Concarneau":(47.8733,-3.9178),"Crozon":(48.2422,-4.4983),"Douarnenez":(48.0944,-4.33),
    "Fouesnant":(47.8939,-4.0122),"Gouesnou":(48.4422,-4.4656),"Guipavas":(48.4281,-4.3989),
    "Guilvinec":(47.7961,-4.2869),"Landerneau":(48.4528,-4.2497),"Landivisiau":(48.5122,-4.0658),
    "Lannilis":(48.5325,-4.5158),"Le Faouët":(48.0264,-3.4953),"Le Relecq Kerhuon":(48.4194,-4.41),
    "Lesneven":(48.5736,-4.3272),"Lorient":(47.7486,-3.37),"Moëlan sur Mer":(47.8061,-3.6358),
    "Morlaix":(48.5775,-3.8294),"Ploemeur":(47.7303,-3.4325),"Plestin-les-Grèves":(48.6608,-3.6378),
    "Plouarzel":(48.4197,-4.7575),"Ploudalmézeau":(48.5322,-4.6572),"Ploudalmezeau":(48.5322,-4.6572),
    "Plouescat":(48.6719,-4.1722),"Plouzané":(48.3819,-4.6192),"Pont-l'Abbé":(47.8681,-4.2203),
    "Quimper":(47.9969,-4.0994),"Quimper Centre":(47.9969,-4.0994),"Quimper Nord":(47.9969,-4.0994),
    "Quimperlé":(47.8714,-3.5497),"Rosporden":(47.9264,-3.8358),"St Martin des Champs":(48.6028,-3.8336),
    "St Pol de Léon":(48.6839,-3.9839),"St Renan":(48.4333,-4.6278),"Tregunc":(47.8547,-3.8564),
    "Bouguenais":(47.1714,-1.6047),"Coueron":(47.2117,-1.7275),"Coueron Bourg":(47.2117,-1.7275),
    "Coueron La Chabossière":(47.2117,-1.7275),"Malville":(47.38,-1.9025),"Nantes":(47.2184,-1.5536),
    "Orvault":(47.2733,-1.6228),"Rezé":(47.1583,-1.5569),"Saint-Herblain":(47.2481,-1.5997),
    "Saint-Herblain Bourg":(47.2481,-1.5997),"Saint-Herblain Châtaigniers":(47.2481,-1.5997),
    "St Philbert de Grand Lieu":(47.0333,-1.6417),"Vertou":(47.1683,-1.4694),
    "Aucamville":(43.6786,1.4317),"Balma":(43.6103,1.4994),"Blagnac":(43.7083,1.39),
    "Castanet Tolosan":(43.52,1.5033),"Cazères":(43.2092,1.0814),"Colomiers":(43.615,1.335),
    "Cornebarrieu":(43.6608,1.3322),"Cugnaux":(43.5347,1.3483),"Fonsorbes":(43.5292,1.2742),
    "Fronton":(43.8544,1.4183),"Grenade":(43.7722,1.2953),"L'Isle Jourdain":(43.6136,1.0825),
    "Labège":(43.5683,1.5019),"Léguevin":(43.5975,1.2333),"Montastruc la Conseillère":(43.7025,1.555),
    "Montréjeau":(43.0906,0.5728),"Muret":(43.4639,1.3261),"Nailloux":(43.3544,1.6297),
    "Pechbonnieu":(43.7,1.5153),"Pinsaguel":(43.5044,1.4231),"Plaisance du Touch":(43.5636,1.2914),
    "Ramonville":(43.5492,1.4797),"Revel":(43.4556,2.0064),"Rieumes":(43.4072,1.1222),
    "Saint Gaudens":(43.1075,0.7231),"Saverdun":(43.2342,1.5739),"Seysses":(43.4936,1.3108),
    "St Jory":(43.7419,1.3717),"St Lys":(43.5214,1.2197),"St Orens de Gameville":(43.5628,1.5197),
    "Tournefeuille":(43.5814,1.3333),"Toulouse":(43.6047,1.4442),"Toulouse Arcole":(43.6047,1.4442),
    "Toulouse Bonnefoy":(43.5997,1.4742),"Toulouse Croix Daurade":(43.6397,1.4442),
    "Toulouse Croix de Pierre":(43.5897,1.4342),"Toulouse Demoiselles":(43.5897,1.4542),
    "Toulouse Guilhemery":(43.5997,1.4842),"Toulouse Lardenne":(43.5997,1.3742),
    "Toulouse les Carmes":(43.5947,1.4442),"Toulouse Minimes":(43.6247,1.4442),
    "Toulouse Monconseil":(43.6047,1.4242),"Toulouse Palais de Justice":(43.6047,1.4442),
    "Toulouse St Agne":(43.5747,1.4542),"Toulouse St Cyprien":(43.5997,1.4142),
    "Verdun sur Garonne":(43.865,1.2344),"Verfeil":(43.6408,1.6008),
    "Villefranche de Lauragais":(43.3967,1.7236),"Villemur sur Tarn":(43.8667,1.5033),
    "Auterive":(43.3536,1.4756),"Carbonne":(43.2978,1.2281),"Lanta":(43.5528,1.6517),
    "Venerque":(43.44,1.4642),"Salies-du-Salat":(43.1022,0.9569),"Labastide-Saint-Pierre":(43.9958,1.3283),
    "Agde":(43.3108,3.4753),"Balaruc-les-Bains":(43.4475,3.6825),"Béziers":(43.3442,3.2153),
    "Béziers Clémenceau":(43.3442,3.2153),"Béziers les Halles":(43.3442,3.2153),
    "Cazouls lès Beziers":(43.4108,3.0753),"Castelnau le Lez":(43.6383,3.9122),
    "Castelnau-le-Lez":(43.6383,3.9122),"Clermont l'Hérault":(43.6278,3.4325),
    "Frontignan":(43.4483,3.7553),"Gigean":(43.5053,3.7294),"Gignac":(43.6514,3.5572),
    "Jacou":(43.6639,3.9483),"Juvignac":(43.6175,3.8058),"La Grande Motte":(43.5611,4.0814),
    "Le Crès":(43.6453,3.9397),"Lunel":(43.6742,4.1344),"Marseillan":(43.3578,3.5325),
    "Mauguio":(43.6114,4.0089),"Mèze":(43.425,3.6044),"Montpellier":(43.6119,3.8772),
    "Montpellier Antigone":(43.6069,3.8972),"Montpellier Arceaux":(43.6119,3.8572),
    "Montpellier Chamberte":(43.6219,3.8772),"Montpellier Clémenceau":(43.6119,3.8772),
    "Montpellier Facultés":(43.6319,3.8572),"Montpellier Lepic":(43.6119,3.8672),
    "Montpellier Port Marianne":(43.5969,3.9072),"Montpellier Préfecture":(43.6119,3.8772),
    "Palavas les flots":(43.53,3.9261),"Pézenas":(43.4628,3.4225),"Roujan":(43.5028,3.3094),
    "Sète":(43.4028,3.6967),"St-Gély-du-Fesc":(43.6981,3.8344),"St Jean de Vedas":(43.5803,3.8178),
    "Valras Plage":(43.2428,3.2981),"Villeneuve-lès-Maguelone":(43.5178,3.8578),
    "Amboise":(47.4133,0.9833),"Ballan":(47.3683,0.6133),"Bléré":(47.3194,0.9886),
    "Chambray les Tours":(47.3483,0.72),"Chinon":(47.1675,0.2408),"Cinq Mars la Pile":(47.3506,0.4672),
    "Fondettes":(47.4081,0.5719),"Joué les Tours":(47.3508,0.6606),"La Riche":(47.3853,0.6603),
    "Loches":(47.1275,1.0017),"Montbazon":(47.2881,0.7119),"Montlouis sur Loire":(47.3911,0.8203),
    "Montrichard":(47.3414,1.1836),"Saint-Cyr-sur-Loire":(47.4039,0.6594),
    "Ste Maure de Touraine":(47.1053,0.6197),"St Avertin":(47.3683,0.7333),
    "Tours":(47.39,0.6892),"Tours Grammont":(47.38,0.7092),"Tours Halles":(47.39,0.6892),
    "Tours Jaurès":(47.39,0.6892),"Tours Les Halles":(47.39,0.6892),
    "Tours Monconseil":(47.4,0.6792),"Tours Velpeau":(47.39,0.6792),
    "Agen":(44.2006,0.6167),"Aire sur l'Adour":(43.6981,-0.2664),"Casteljaloux":(44.3128,0.09),
    "Castelsarrasin":(44.0367,1.1058),"Caussade":(44.1583,1.5319),"Duras":(44.6753,0.1806),
    "Fumel":(44.4983,1.0656),"Marmande":(44.5006,0.1658),"Marmande Centre":(44.5006,0.1658),
    "Marmande Libération":(44.5006,0.1658),"Miramont de guyenne":(44.6033,0.3631),
    "Moissac":(44.1058,1.085),"Monflanquin":(44.53,0.7681),"Monsempron-Libos":(44.4947,0.9489),
    "Nérac":(44.1375,0.3378),"Ste Foy la Grande":(44.8386,0.22),"Tonneins":(44.3875,0.3042),
    "Valence d'Agen":(44.1083,0.8944),"Villeneuve sur Lot":(44.4086,0.7047),
    "Argentat":(45.0936,1.9356),"Beaulieu sur Dordogne":(44.9778,1.8361),
    "Malemort-sur-Corrèze":(45.1617,1.5542),"Martel":(44.9367,1.6131),
    "Meyssac":(45.0533,1.6736),"Pompadour":(45.3967,1.4133),"St Céré":(44.8625,1.8936),
    "Tulle":(45.2678,1.7717),"Ussel":(45.5472,2.3133),"Uzerche":(45.425,1.5608),
    "Ussac":(45.19,1.5208),"Capdenac Gare":(44.5706,2.0814),"Decazeville":(44.5614,2.2556),
    "Figeac":(44.6083,2.0333),"Rodez":(44.3508,2.5744),"Villefranche de Rouergue":(44.3508,2.0367),
    "Cahors":(44.4483,1.4425),"Gourdon":(44.7378,1.3833),"Gramat":(44.7742,1.7256),
    "Lalbenque":(44.3403,1.5428),"Prayssac":(44.4847,1.2614),
    "Auch":(43.6481,0.5847),"Auch Basse Ville":(43.6481,0.5847),"Auch Haute Ville":(43.6481,0.5847),
    "Condom":(43.9581,0.3708),"Eauze":(43.8583,0.1006),"Fleurance":(43.8519,0.6608),
    "Gimont":(43.6319,0.8744),"Mirande":(43.5178,0.4033),"Nogaro":(43.7653,-0.0358),
    "Samatan":(43.4908,0.9289),"Beaumont de Lomagne":(43.8836,0.9942),
    "Montauban":(44.0175,1.3525),"Montauban Centre":(44.0175,1.3525),
    "Montauban Villenouvelle":(44.0375,1.3725),"Albi":(43.9294,2.1481),
    "Castres":(43.6067,2.2417),"Gaillac":(43.9017,1.8964),"Graulhet":(43.7644,2.0011),
    "Lavaur":(43.6986,1.8206),"St Sulpice la Pointe":(43.7717,1.6881),
    "Foix":(42.9644,1.6078),"Lavelanet":(42.9367,1.8542),"Mirepoix":(43.0878,1.8736),
    "Pamiers":(43.1172,1.6081),"Saverdun":(43.2342,1.5739),"St Girons":(42.9853,1.1458),
    "Bron":(45.7408,4.9189),"Caluire et Cuire":(45.7969,4.8522),"Chassieu":(45.7239,4.9661),
    "Decines Charpieu":(45.77,4.9611),"Oullins":(45.7125,4.8056),"Saint-Priest":(45.6958,4.9211),
    "Sathonay-Camp":(45.8308,4.8964),"Villeurbanne":(45.7667,4.8789),
    "Villeurbanne Grand Clément":(45.7767,4.8889),"Villeurbanne Gratte-Ciel":(45.7767,4.8989),
    "Lyon":(45.7676,4.8344),"Lyon 3 Villette":(45.7576,4.8544),"Lyon 3 Préfecture":(45.7576,4.8544),
    "Lyon 4 Croix Rousse":(45.7776,4.8244),"Lyon 5 - St Just":(45.7476,4.8144),
    "Lyon 6 - Brotteaux":(45.7676,4.8544),"Lyon 7 Gerland":(45.7276,4.8444),
    "Lyon 7 Saxe":(45.7376,4.8444),"Lyon 8 Moulin À Vent":(45.7176,4.8644),
    "Lyon 9 Vaise":(45.7776,4.8044),"Lanester":(47.765,-3.3394),
    "Ploemeur":(47.7303,-3.4325),"Pontivy":(48.0672,-2.9772),"Quéven":(47.7564,-3.4214),
    "Vannes":(47.6578,-2.7608),"Begard":(48.6081,-3.2978),"Lannion":(48.7317,-3.4586),
    "Rennes":(48.1147,-1.6794),"Angers":(47.4739,-0.5514),
    "Fontenay le comte":(46.4669,-0.8053),"Le Poiré sur Vie":(46.7617,-1.5044),
    "Les Sables-d'Olonne":(46.4978,-1.7836),"La Roche sur Yon":(46.6706,-1.4264),
    "Chauray":(46.3817,-0.3867),"Melle":(46.2242,-0.1422),"Niort":(46.3228,-0.4572),
    "St Maixent l'Ecole":(46.4097,-0.2119),"Mauzé sur le Mignon":(46.1942,-0.6706),
    "Aixe sur Vienne":(45.7986,1.1353),"Bellac":(46.1194,1.0453),"Couzeix":(45.8797,1.2428),
    "Isle":(45.6936,1.2117),"Limoges":(45.8347,1.2611),"Limoges Carnot":(45.8347,1.2611),
    "Limoges Mairie":(45.8347,1.2611),"Limoges Sablard":(45.8347,1.2611),
    "Rochechouart":(45.82,0.8181),"St Junien":(45.8878,0.9019),"St Yrieix la Perche":(45.5139,1.2089),
    "Aigurande":(46.435,1.8253),"Argenton sur Creuse":(46.5897,1.515),
    "Bourganeuf":(45.9522,1.7528),"Châteaumeillant":(46.5636,2.1989),
    "Guéret":(46.1636,1.8708),"La Châtre":(46.5806,1.9903),"La Souterraine":(46.2372,1.4878),
    "Montluçon":(46.3406,2.6019),"Buzançais":(46.8947,1.4178),"Châteauroux":(46.8131,1.6917),
    "Issoudun":(46.9481,1.9908),"Mehun-sur-Yèvre":(47.1442,2.2197),
    "Bourges":(47.0825,2.3975),"Saint-Amand Montrond":(46.7236,2.505),
    "Saint-Florent-sur-Cher":(47.0025,2.2514),"Vierzon":(47.2225,2.0694),"Lignières":(46.7519,2.1694),
    "Blois":(47.5833,1.3369),"Blois Centre":(47.5833,1.3369),"Blois Vienne":(47.5833,1.3369),
    "Contres":(47.4131,1.4297),"Montrichard":(47.3414,1.1836),"Onzain":(47.5081,1.1819),
    "Romorantin-Lanthenay":(47.3597,1.7442),"Salbris":(47.4258,2.0514),"St Aignan":(47.2683,1.3731),
    "Achères":(48.9572,2.0625),"Argenteuil":(48.9472,2.2475),"Aubergenville":(48.9706,1.8414),
    "Bois d'Arcy":(48.7928,2.0433),"Beynes":(48.8461,1.8769),"Ecquevilly":(48.9906,1.8975),
    "La Garenne-Colombes":(48.9072,2.2453),"Les Clayes-sous-Bois":(48.8028,1.9942),
    "Maisons Laffitte":(48.9483,2.1483),"Maule":(48.9153,1.7317),"Meulan":(49.0039,1.9056),
    "Orgeval":(48.9819,1.9828),"Poissy":(48.9289,2.0456),"Saint-Cyr-l'École":(48.8019,2.065),
    "Septeuil":(48.8614,1.66),"Villiers Saint Frederic":(48.8136,1.9114),
    "Cergy":(49.0361,2.0756),"Colombes":(48.9231,2.2539),"Eaubonne":(48.99,2.2806),
    "L'isle Adam":(49.1028,2.2181),"Magny en Vexin":(49.1564,1.7864),"Marines":(49.15,1.9817),
    "Méry sur Oise":(49.0606,2.1839),"Pontoise":(49.0536,2.1006),"Sannois":(48.9744,2.2617),
    "Soisy sous Montmorency":(48.9881,2.3006),"St Leu la Forêt":(49.0228,2.2414),
    "Taverny":(49.0283,2.2261),"Vauréal":(49.0333,2.0625),
    "Bezons":(48.9303,2.2133),"Bois-Colombes":(48.9211,2.2681),
    "Clichy":(48.9039,2.305),"Clichy Mairie":(48.9039,2.305),"Clichy République":(48.9039,2.305),
    "Domérat":(46.3578,2.5597),"Domerat":(46.3578,2.5597),
    "Aubigny Les Clouzeaux":(46.6806,-1.4344),"St Amand Montrond":(46.7236,2.505),
    "Le Passage d'Agen":(44.2011,0.6233),"St-Pierre-du-Mont":(43.8867,-0.5281),
    "St Augustin":(44.8478,-0.6192),"Pomarez":(43.6528,-0.6894),
    "Maurs":(44.71,2.1994),"Domérat":(46.3578,2.5597),
}


def fallback_coords(cp, dept, nom):
    """Get GPS coords: try city name first, then dept centroid."""
    # 1. Try name-based geocoding
    city = _extract_city(nom)
    if city:
        parts = city.split()
        for n in range(len(parts), 0, -1):
            candidate = " ".join(parts[:n])
            if candidate in _CITY_GPS:
                lat, lon = _CITY_GPS[candidate]
                return lat, lon, False  # False = precise
        # Partial match
        city_lower = city.lower()
        for key, coords in _CITY_GPS.items():
            if city_lower.startswith(key.lower()) and len(key) >= 4:
                return coords[0], coords[1], False

    # 2. Dept centroid fallback
    import hashlib
    if dept and dept in DEPT_CENTROIDS:
        base_lat, base_lon = DEPT_CENTROIDS[dept]
        h = int(hashlib.md5(str(cp or "").encode()).hexdigest()[:8], 16)
        lat_j = ((h % 1000) - 500) / 1000 * 0.12
        lon_j = ((h // 1000 % 1000) - 500) / 1000 * 0.12
        return round(base_lat + lat_j, 5), round(base_lon + lon_j, 5), True
    return None, None, True


def geocode_nominatim_batch(addresses: tuple) -> dict:
    """
    Geocode a batch of addresses via Nominatim.
    Called only on Streamlit Cloud (has internet access).
    Returns dict {address: (lat, lon)}.
    """
    import requests
    HEADERS = {"User-Agent": "PartooSEODashboard/2.0"}
    results = {}
    for addr in addresses:
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": addr, "format": "json", "limit": 1, "countrycodes": "fr"},
                headers=HEADERS, timeout=6,
            )
            data = r.json()
            if data:
                results[addr] = (float(data[0]["lat"]), float(data[0]["lon"]))
            else:
                results[addr] = (None, None)
        except:
            results[addr] = (None, None)
        time.sleep(1.05)
    return results


def load_coords_csv(coords_path="coords.csv") -> dict:
    """Load pre-geocoded coords from CSV. Returns {address: (lat, lon)}."""
    if not os.path.exists(coords_path):
        return {}
    try:
        df = pd.read_csv(coords_path, encoding="utf-8")
        result = {}
        for _, row in df.iterrows():
            if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                result[str(row["adresse"])] = (float(row["lat"]), float(row["lon"]))
        return result
    except Exception as e:
        return {}


@st.cache_data(show_spinner="Chargement des données…")
def load_excel(file_bytes: bytes, periode: str, coords_csv_bytes: bytes = b"") -> dict:
    import io, tempfile

    xl = pd.ExcelFile(io.BytesIO(file_bytes))

    df_gen = pd.read_excel(xl, sheet_name="Statistiques générales")
    df_gen["periode"] = periode

    df_det = pd.read_excel(xl, sheet_name="Statistiques détaillées")
    df_det["cp"] = df_det["Adresse"].apply(extract_cp)
    df_det["dept"] = df_det["cp"].apply(lambda x: x[:2] if isinstance(x, str) else None)
    df_det["Notation"] = pd.to_numeric(df_det["Notation"], errors="coerce")

    # Load coords lookup
    coords_lookup = {}
    if coords_csv_bytes:
        try:
            df_coords = pd.read_csv(io.BytesIO(coords_csv_bytes), encoding="utf-8")
            for _, row in df_coords.iterrows():
                if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                    coords_lookup[str(row["adresse"]).strip()] = (float(row["lat"]), float(row["lon"]))
        except:
            pass
    else:
        coords_lookup = load_coords_csv()

    def get_coords(addr, cp, dept, nom):
        key = str(addr).strip() if addr else ""
        if key in coords_lookup:
            return coords_lookup[key][0], coords_lookup[key][1], False  # False = precise
        return fallback_coords(cp, dept, nom)

    # Human reference
    df_human = df_det[df_det["Concurrents"].isna()].copy()
    ref = (
        df_human.groupby("Business Id")
        .agg(nom=("Nom de l'établissement", "first"), adresse=("Adresse", "first"),
             cp=("cp", "first"), dept=("dept", "first"))
        .reset_index()
    )
    ref["dept_label"] = ref["dept"].map(DEPT_NAMES)

    ref["lat"] = None
    ref["lon"] = None
    ref["approx"] = True
    for idx, row in ref.iterrows():
        lat, lon, approx = get_coords(row["adresse"], row["cp"], row["dept"], row["nom"])
        ref.at[idx, "lat"] = lat
        ref.at[idx, "lon"] = lon
        ref.at[idx, "approx"] = approx

    precise_pct = int((~ref["approx"]).sum() / max(len(ref), 1) * 100)

    # Classées
    df_cl = pd.read_excel(xl, sheet_name="Établissements classés")
    df_cl = df_cl.merge(ref[["Business Id", "cp", "dept", "dept_label", "lat", "lon", "approx"]], on="Business Id", how="left")
    df_cl["Notation"] = pd.to_numeric(df_cl["Notation"], errors="coerce")
    df_cl["periode"] = periode
    df_cl["statut"] = df_cl["Position"].apply(
        lambda x: "Top 3" if x <= 3 else ("Top 5" if x <= 5 else ("Top 10" if x <= 10 else "Hors Top 10"))
    )

    # Non classées
    df_nc = pd.read_excel(xl, sheet_name="Établissements non classés")
    df_nc = df_nc.merge(ref[["Business Id", "cp", "dept", "dept_label", "lat", "lon", "approx"]], on="Business Id", how="left")
    df_nc["periode"] = periode

    # Competitors
    df_conc = df_det[df_det["Concurrents"].notna()].copy()
    conc_agg = (
        df_conc.groupby(["Nom de l'établissement", "Concurrents", "Adresse"])
        .agg(cp=("cp", "first"), dept=("dept", "first"),
             pos_moy=("Position", "mean"), pos_min=("Position", "min"),
             notation=("Notation", "mean"), reviews=("reviews", "mean"),
             mots=("Mot-clé", lambda x: list(x.unique())))
        .reset_index()
    )
    conc_agg["lat"] = None
    conc_agg["lon"] = None
    conc_agg["approx"] = True
    for idx, row in conc_agg.iterrows():
        lat, lon, approx = get_coords(row["Adresse"], row["cp"], row["dept"], row["Nom de l'établissement"])
        conc_agg.at[idx, "lat"] = lat
        conc_agg.at[idx, "lon"] = lon
        conc_agg.at[idx, "approx"] = approx
    conc_agg.rename(columns={"Nom de l'établissement": "nom", "Concurrents": "reseau", "Adresse": "adresse"}, inplace=True)

    return {
        "generales": df_gen,
        "classees": df_cl,
        "non_classees": df_nc,
        "ref": ref,
        "concurrents_geo": conc_agg,
        "_df_det": df_det,
        "periode": periode,
        "mots_cles": sorted(df_cl["Mot-clé"].unique().tolist()),
        "depts": sorted(ref["dept"].dropna().unique().tolist()),
        "human_names": sorted(ref["nom"].unique().tolist()),
        "precise_pct": precise_pct,
        "coords_loaded": bool(coords_lookup),
    }


def merge_datasets(datasets: list) -> dict:
    if len(datasets) == 1:
        return datasets[0]
    return {
        "generales": pd.concat([d["generales"] for d in datasets], ignore_index=True),
        "classees": pd.concat([d["classees"] for d in datasets], ignore_index=True),
        "non_classees": pd.concat([d["non_classees"] for d in datasets], ignore_index=True),
        "ref": datasets[-1]["ref"],
        "concurrents_geo": datasets[-1]["concurrents_geo"],
        "periode": " | ".join(d["periode"] for d in datasets),
        "mots_cles": datasets[-1]["mots_cles"],
        "depts": datasets[-1]["depts"],
        "human_names": datasets[-1]["human_names"],
        "precise_pct": datasets[-1].get("precise_pct", 0),
        "coords_loaded": datasets[-1].get("coords_loaded", False),
    }


def apply_filters(data: dict, sel_mots, sel_depts, sel_agences) -> dict:
    cl = data["classees"].copy()
    nc = data["non_classees"].copy()
    cl = cl[cl["Mot-clé"].isin(sel_mots)]
    nc = nc[nc["Mot-clé"].isin(sel_mots)]
    if sel_depts:
        cl = cl[cl["dept"].isin(sel_depts)]
        nc = nc[nc["dept"].isin(sel_depts)]
    if sel_agences:
        cl = cl[cl["Nom de l'établissement"].isin(sel_agences)]
        nc = nc[nc["Nom de l'établissement"].isin(sel_agences)]
    return {"classees": cl, "non_classees": nc}


def seo_score(pos_moy, nb_couverts, total_mots, notation):
    pos_s = max(0, (20 - pos_moy) / 20 * 50) if pos_moy else 0
    cov_s = (nb_couverts / max(total_mots, 1)) * 30
    note_s = max(0, (notation - 3.5) / 1.5 * 20) if notation and not pd.isna(notation) else 0
    return int(min(100, pos_s + cov_s + note_s))


def get_priorite(pos_moy, nb_manquants, notation):
    score = 0
    if pos_moy is None:
        score += 3
    elif pos_moy > 10:
        score += 3
    elif pos_moy > 5:
        score += 2
    else:
        score += 1
    score += min(3, nb_manquants)
    if notation and not pd.isna(notation) and notation < 4.0:
        score += 1
    if score >= 5:
        return "🔴 Urgent"
    elif score >= 3:
        return "🟡 Important"
    return "🟢 Opportunité"


def get_competitors_in_radius(agency_lat, agency_lon, conc_df, radius_km=5):
    if agency_lat is None or agency_lon is None:
        return pd.DataFrame()
    result = []
    for _, row in conc_df.iterrows():
        if row["lat"] is None or row["lon"] is None:
            continue
        try:
            dist = haversine_km(float(agency_lat), float(agency_lon), float(row["lat"]), float(row["lon"]))
            if dist <= radius_km:
                result.append({**row.to_dict(), "distance_km": round(dist, 2)})
        except:
            continue
    if not result:
        return pd.DataFrame()
    return pd.DataFrame(result).sort_values("pos_moy")
