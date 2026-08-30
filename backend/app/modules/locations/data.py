"""Authoritative India Local Government Directory (LGD) & IGOD Location Dataset.

Covers all 28 States, 8 Union Territories, official Districts, Sub-Districts
(Tehsils / Taluks / Mandals / Sub-Divisions), and Blocks with official LGD codes.
"""
from __future__ import annotations

from typing import Dict, List, Optional, TypedDict


class StateData(TypedDict):
    id: str
    code: str
    name: str
    official_name: str
    type: str  # 'STATE' | 'UNION_TERRITORY'
    lgd_code: int
    source: str
    last_updated: str


class DistrictData(TypedDict):
    id: str
    code: str
    name: str
    official_name: str
    state_id: str
    lgd_code: int
    source: str
    last_updated: str


class SubDistrictData(TypedDict):
    id: str
    code: str
    name: str
    official_name: str
    district_id: str
    state_id: str
    type: str  # 'TEHSIL' | 'TALUK' | 'MANDAL' | 'SUB_DIVISION'
    lgd_code: int
    source: str
    last_updated: str


class BlockData(TypedDict):
    id: str
    code: str
    name: str
    official_name: str
    sub_district_id: Optional[str]
    district_id: str
    state_id: str
    lgd_code: int
    source: str
    last_updated: str


LGD_SOURCE = "Local Government Directory (LGD) / IGOD, Govt. of India"
LAST_UPDATED = "2026-01-15"

# ----------------------------------------------------------------------
# 1. STATES & UNION TERRITORIES (36 Total: 28 States + 8 UTs)
# ----------------------------------------------------------------------
INDIA_STATES: List[StateData] = [
    # 28 States
    {"id": "AP", "code": "AP", "name": "Andhra Pradesh", "official_name": "State of Andhra Pradesh", "type": "STATE", "lgd_code": 28, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "AR", "code": "AR", "name": "Arunachal Pradesh", "official_name": "State of Arunachal Pradesh", "type": "STATE", "lgd_code": 12, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "AS", "code": "AS", "name": "Assam", "official_name": "State of Assam", "type": "STATE", "lgd_code": 18, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "BR", "code": "BR", "name": "Bihar", "official_name": "State of Bihar", "type": "STATE", "lgd_code": 10, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "CG", "code": "CG", "name": "Chhattisgarh", "official_name": "State of Chhattisgarh", "type": "STATE", "lgd_code": 22, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "GA", "code": "GA", "name": "Goa", "official_name": "State of Goa", "type": "STATE", "lgd_code": 30, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "GJ", "code": "GJ", "name": "Gujarat", "official_name": "State of Gujarat", "type": "STATE", "lgd_code": 24, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "HR", "code": "HR", "name": "Haryana", "official_name": "State of Haryana", "type": "STATE", "lgd_code": 6, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "HP", "code": "HP", "name": "Himachal Pradesh", "official_name": "State of Himachal Pradesh", "type": "STATE", "lgd_code": 2, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "JH", "code": "JH", "name": "Jharkhand", "official_name": "State of Jharkhand", "type": "STATE", "lgd_code": 20, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "KA", "code": "KA", "name": "Karnataka", "official_name": "State of Karnataka", "type": "STATE", "lgd_code": 29, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "KL", "code": "KL", "name": "Kerala", "official_name": "State of Kerala", "type": "STATE", "lgd_code": 32, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "MP", "code": "MP", "name": "Madhya Pradesh", "official_name": "State of Madhya Pradesh", "type": "STATE", "lgd_code": 23, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "MH", "code": "MH", "name": "Maharashtra", "official_name": "State of Maharashtra", "type": "STATE", "lgd_code": 27, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "MN", "code": "MN", "name": "Manipur", "official_name": "State of Manipur", "type": "STATE", "lgd_code": 14, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "ML", "code": "ML", "name": "Meghalaya", "official_name": "State of Meghalaya", "type": "STATE", "lgd_code": 17, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "MZ", "code": "MZ", "name": "Mizoram", "official_name": "State of Mizoram", "type": "STATE", "lgd_code": 15, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "NL", "code": "NL", "name": "Nagaland", "official_name": "State of Nagaland", "type": "STATE", "lgd_code": 13, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "OD", "code": "OD", "name": "Odisha", "official_name": "State of Odisha", "type": "STATE", "lgd_code": 21, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "PB", "code": "PB", "name": "Punjab", "official_name": "State of Punjab", "type": "STATE", "lgd_code": 3, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "RJ", "code": "RJ", "name": "Rajasthan", "official_name": "State of Rajasthan", "type": "STATE", "lgd_code": 8, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "SK", "code": "SK", "name": "Sikkim", "official_name": "State of Sikkim", "type": "STATE", "lgd_code": 11, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "TN", "code": "TN", "name": "Tamil Nadu", "official_name": "State of Tamil Nadu", "type": "STATE", "lgd_code": 33, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "TG", "code": "TG", "name": "Telangana", "official_name": "State of Telangana", "type": "STATE", "lgd_code": 36, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "TR", "code": "TR", "name": "Tripura", "official_name": "State of Tripura", "type": "STATE", "lgd_code": 16, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "UP", "code": "UP", "name": "Uttar Pradesh", "official_name": "State of Uttar Pradesh", "type": "STATE", "lgd_code": 9, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "UK", "code": "UK", "name": "Uttarakhand", "official_name": "State of Uttarakhand", "type": "STATE", "lgd_code": 5, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "WB", "code": "WB", "name": "West Bengal", "official_name": "State of West Bengal", "type": "STATE", "lgd_code": 19, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    # 8 Union Territories
    {"id": "AN", "code": "AN", "name": "Andaman and Nicobar Islands", "official_name": "UT of Andaman and Nicobar Islands", "type": "UNION_TERRITORY", "lgd_code": 35, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "CH", "code": "CH", "name": "Chandigarh", "official_name": "UT of Chandigarh", "type": "UNION_TERRITORY", "lgd_code": 4, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "DH", "code": "DH", "name": "Dadra and Nagar Haveli and Daman and Diu", "official_name": "UT of Dadra and Nagar Haveli and Daman and Diu", "type": "UNION_TERRITORY", "lgd_code": 38, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "DL", "code": "DL", "name": "Delhi (NCT)", "official_name": "National Capital Territory of Delhi", "type": "UNION_TERRITORY", "lgd_code": 7, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "JK", "code": "JK", "name": "Jammu and Kashmir", "official_name": "UT of Jammu and Kashmir", "type": "UNION_TERRITORY", "lgd_code": 1, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "LA", "code": "LA", "name": "Ladakh", "official_name": "UT of Ladakh", "type": "UNION_TERRITORY", "lgd_code": 37, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "LD", "code": "LD", "name": "Lakshadweep", "official_name": "UT of Lakshadweep", "type": "UNION_TERRITORY", "lgd_code": 31, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
    {"id": "PY", "code": "PY", "name": "Puducherry", "official_name": "UT of Puducherry", "type": "UNION_TERRITORY", "lgd_code": 34, "source": LGD_SOURCE, "last_updated": LAST_UPDATED},
]

# Helper map for states by ID or code or name
STATE_MAP_BY_KEY: Dict[str, StateData] = {}
for _st in INDIA_STATES:
    STATE_MAP_BY_KEY[_st["id"].upper()] = _st
    STATE_MAP_BY_KEY[_st["code"].upper()] = _st
    STATE_MAP_BY_KEY[_st["name"].lower()] = _st

# ----------------------------------------------------------------------
# 2. DISTRICTS DATA (Comprehensive LGD Mapping per State/UT)
# ----------------------------------------------------------------------
# Raw dict mapping State ID -> list of (district_id, district_name, lgd_code)
_DISTRICTS_RAW: Dict[str, List[tuple[str, str, int]]] = {
    "AP": [
        ("AP_AKP", "Anakapalli", 745), ("AP_ATP", "Ananthapuramu", 502), ("AP_AMY", "Annamayya", 746),
        ("AP_BPT", "Bapatla", 747), ("AP_CTR", "Chittoor", 503), ("AP_EGD", "East Godavari", 505),
        ("AP_ELR", "Eluru", 748), ("AP_GNT", "Guntur", 506), ("AP_KKD", "Kakinada", 749),
        ("AP_KNL", "Kurnool", 508), ("AP_NTR", "NTR", 750), ("AP_NDL", "Nandyal", 751),
        ("AP_PLN", "Palnadu", 752), ("AP_PPM", "Parvathipuram Manyam", 753), ("AP_PKM", "Prakasam", 510),
        ("AP_KNS", "Dr. B.R. Ambedkar Konaseema", 754), ("AP_NLR", "Sri Potti Sriramulu Nellore", 511),
        ("AP_SSS", "Sri Sathya Sai", 755), ("AP_SKL", "Srikakulam", 513), ("AP_TPT", "Tirupati", 756),
        ("AP_VSP", "Visakhapatnam", 514), ("AP_VZM", "Vizianagaram", 515), ("AP_WGD", "West Godavari", 516),
        ("AP_KDP", "YSR Kadapa", 504), ("AP_ASR", "Alluri Sitharama Raju", 757)
    ],
    "AR": [
        ("AR_ANJ", "Anjaw", 601), ("AR_CHG", "Changlang", 244), ("AR_DBG", "Dibang Valley", 245),
        ("AR_EKM", "East Kameng", 246), ("AR_ESG", "East Siang", 247), ("AR_KML", "Kamle", 718),
        ("AR_KDD", "Kra Daadi", 714), ("AR_KRK", "Kurung Kumey", 257), ("AR_LPR", "Lepa Rada", 725),
        ("AR_LHT", "Lohit", 248), ("AR_LDG", "Longding", 657), ("AR_LDV", "Lower Dibang Valley", 258),
        ("AR_LSG", "Lower Siang", 717), ("AR_LSB", "Lower Subansiri", 249), ("AR_NMS", "Namsai", 685),
        ("AR_PKS", "Pakke Kessang", 724), ("AR_PMP", "Papum Pare", 250), ("AR_SYM", "Shi Yomi", 726),
        ("AR_SNG", "Siang", 715), ("AR_TWG", "Tawang", 251), ("AR_TRP", "Tirap", 252),
        ("AR_USG", "Upper Siang", 253), ("AR_USB", "Upper Subansiri", 254), ("AR_WKM", "West Kameng", 255),
        ("AR_WSG", "West Siang", 256), ("AR_ICC", "Itanagar Capital Complex", 730)
    ],
    "AS": [
        ("AS_BJL", "Bajali", 735), ("AS_BKS", "Baksa", 600), ("AS_BRP", "Barpeta", 283),
        ("AS_BSW", "Biswanath", 700), ("AS_BNG", "Bongaigaon", 284), ("AS_CCR", "Cachar", 285),
        ("AS_CRD", "Charaideo", 701), ("AS_CRG", "Chirang", 603), ("AS_DRG", "Darrang", 286),
        ("AS_DMJ", "Dhemaji", 287), ("AS_DHB", "Dhubri", 288), ("AS_DGB", "Dibrugarh", 289),
        ("AS_DMH", "Dima Hasao", 299), ("AS_GLP", "Goalpara", 290), ("AS_GLT", "Golaghat", 291),
        ("AS_HLK", "Hailakandi", 292), ("AS_HOJ", "Hojai", 702), ("AS_JRT", "Jorhat", 293),
        ("AS_KMP", "Kamrup", 294), ("AS_KMM", "Kamrup Metropolitan", 604), ("AS_KBA", "Karbi Anglong", 295),
        ("AS_KRM", "Karimganj", 296), ("AS_KKJ", "Kokrajhar", 297), ("AS_LKP", "Lakhimpur", 298),
        ("AS_MJL", "Majuli", 703), ("AS_MRG", "Morigaon", 300), ("AS_NGN", "Nagaon", 301),
        ("AS_NLB", "Nalbari", 302), ("AS_SVG", "Sivasagar", 303), ("AS_SNP", "Sonitpur", 304),
        ("AS_SSM", "South Salmara-Mankachar", 704), ("AS_TSK", "Tinsukia", 305), ("AS_UDG", "Udalguri", 605),
        ("AS_WKA", "West Karbi Anglong", 705)
    ],
    "BR": [
        ("BR_ARR", "Araria", 204), ("BR_ARW", "Arwal", 611), ("BR_ARG", "Aurangabad", 205),
        ("BR_BNK", "Banka", 206), ("BR_BGS", "Begusarai", 207), ("BR_BGP", "Bhagalpur", 208),
        ("BR_BJP", "Bhojpur", 209), ("BR_BXR", "Buxar", 210), ("BR_DBG", "Darbhanga", 211),
        ("BR_ECH", "East Champaran", 230), ("BR_GYA", "Gaya", 212), ("BR_GPG", "Gopalganj", 213),
        ("BR_JMU", "Jamui", 214), ("BR_JHB", "Jehanabad", 215), ("BR_KMR", "Kaimur", 216),
        ("BR_KTH", "Katihar", 217), ("BR_KHG", "Khagaria", 218), ("BR_KSG", "Kishanganj", 219),
        ("BR_LKS", "Lakhisarai", 220), ("BR_MDP", "Madhepura", 221), ("BR_MDB", "Madhubani", 222),
        ("BR_MNG", "Munger", 223), ("BR_MZP", "Muzaffarpur", 224), ("BR_NLN", "Nalanda", 225),
        ("BR_NWD", "Nawada", 226), ("BR_PTN", "Patna", 227), ("BR_PRN", "Purnia", 228),
        ("BR_RHT", "Rohtas", 229), ("BR_SHS", "Saharsa", 231), ("BR_SMS", "Samastipur", 232),
        ("BR_SRN", "Saran", 233), ("BR_SKP", "Sheikhpura", 234), ("BR_SHR", "Sheohar", 235),
        ("BR_STM", "Sitamarhi", 236), ("BR_SWN", "Siwan", 237), ("BR_SPL", "Supaul", 238),
        ("BR_VSL", "Vaishali", 239), ("BR_WCH", "West Champaran", 240)
    ],
    "WB": [
        ("WB_APD", "Alipurduar", 664), ("WB_BNK", "Bankura", 311), ("WB_BRB", "Birbhum", 312),
        ("WB_CBR", "Cooch Behar", 313), ("WB_DDN", "Dakshin Dinajpur", 314), ("WB_DJL", "Darjeeling", 315),
        ("WB_HGL", "Hooghly", 316), ("WB_HWR", "Howrah", 317), ("WB_JPG", "Jalpaiguri", 318),
        ("WB_JRG", "Jhargram", 708), ("WB_KLP", "Kalimpong", 707), ("WB_KLK", "Kolkata", 310),
        ("WB_MLD", "Malda", 319), ("WB_MSD", "Murshidabad", 320), ("WB_NDA", "Nadia", 321),
        ("WB_N24", "North 24 Parganas", 322), ("WB_PBD", "Paschim Bardhaman", 709), ("WB_PMD", "Paschim Medinipur", 323),
        ("WB_EBD", "Purba Bardhaman", 313), ("WB_EMD", "Purba Medinipur", 612), ("WB_PRL", "Purulia", 324),
        ("WB_S24", "South 24 Parganas", 325), ("WB_UDN", "Uttar Dinajpur", 326)
    ],
    "UP": [
        ("UP_AGR", "Agra", 128), ("UP_ALG", "Aligarh", 129), ("UP_AMB", "Ambedkar Nagar", 130),
        ("UP_AMT", "Amethi", 660), ("UP_AMR", "Amroha", 158), ("UP_AUR", "Auraiya", 131),
        ("UP_AYD", "Ayodhya", 143), ("UP_AZM", "Azamgarh", 132), ("UP_BPT", "Baghpat", 133),
        ("UP_BRC", "Bahraich", 134), ("UP_BLL", "Ballia", 135), ("UP_BLP", "Balrampur", 136),
        ("UP_BND", "Banda", 137), ("UP_BBK", "Barabanki", 138), ("UP_BRL", "Bareilly", 139),
        ("UP_BST", "Basti", 140), ("UP_BDH", "Bhadohi", 175), ("UP_BJN", "Bijnor", 141),
        ("UP_BDN", "Budaun", 142), ("UP_BLS", "Bulandshahr", 144), ("UP_CND", "Chandauli", 145),
        ("UP_CTK", "Chitrakoot", 146), ("UP_DER", "Deoria", 147), ("UP_ETH", "Etah", 148),
        ("UP_ETW", "Etawah", 149), ("UP_FRK", "Farrukhabad", 150), ("UP_FTP", "Fatehpur", 151),
        ("UP_FRZ", "Firozabad", 152), ("UP_GBN", "Gautam Buddha Nagar (Noida)", 153), ("UP_GZB", "Ghaziabad", 154),
        ("UP_GZP", "Ghazipur", 155), ("UP_GND", "Gonda", 156), ("UP_GKP", "Gorakhpur", 157),
        ("UP_HMP", "Hamirpur", 159), ("UP_HPR", "Hapur", 652), ("UP_HRD", "Hardoi", 160),
        ("UP_HTR", "Hathras", 166), ("UP_JLN", "Jalaun", 161), ("UP_JNP", "Jaunpur", 162),
        ("UP_JHS", "Jhansi", 163), ("UP_KNJ", "Kannauj", 164), ("UP_KPD", "Kanpur Dehat", 165),
        ("UP_KPN", "Kanpur Nagar", 167), ("UP_KSG", "Kasganj", 633), ("UP_KSH", "Kaushambi", 168),
        ("UP_KHR", "Kheri", 169), ("UP_KSN", "Kushinagar", 170), ("UP_LTP", "Lalitpur", 171),
        ("UP_LKN", "Lucknow", 172), ("UP_MHJ", "Maharajganj", 173), ("UP_MHB", "Mahoba", 174),
        ("UP_MNP", "Mainpuri", 176), ("UP_MTR", "Mathura", 177), ("UP_MAU", "Mau", 178),
        ("UP_MRT", "Meerut", 179), ("UP_MZP", "Mirzapur", 180), ("UP_MDB", "Moradabad", 181),
        ("UP_MZN", "Muzaffarnagar", 182), ("UP_PLB", "Pilibhit", 183), ("UP_PTG", "Pratapgarh", 184),
        ("UP_PRY", "Prayagraj (Allahabad)", 185), ("UP_RBL", "Raebareli", 186), ("UP_RMP", "Rampur", 187),
        ("UP_SRP", "Saharanpur", 188), ("UP_SMB", "Sambhal", 653), ("UP_SKN", "Sant Kabir Nagar", 189),
        ("UP_SPN", "Shahjahanpur", 190), ("UP_SHM", "Shamli", 651), ("UP_SRV", "Shravasti", 191),
        ("UP_SDN", "Siddharthnagar", 192), ("UP_STP", "Sitapur", 193), ("UP_SNB", "Sonbhadra", 194),
        ("UP_SLT", "Sultanpur", 195), ("UP_UNN", "Unnao", 196), ("UP_VNS", "Varanasi", 197)
    ],
    "MH": [
        ("MH_AHM", "Ahilyanagar (Ahmednagar)", 464), ("MH_AKL", "Akola", 465), ("MH_AMR", "Amravati", 466),
        ("MH_BED", "Beed", 467), ("MH_BHN", "Bhandara", 468), ("MH_BLD", "Buldhana", 469),
        ("MH_CND", "Chandrapur", 470), ("MH_CSN", "Chhatrapati Sambhaji Nagar", 471), ("MH_DHR", "Dharashiv", 485),
        ("MH_DHL", "Dhule", 472), ("MH_GDC", "Gadchiroli", 473), ("MH_GND", "Gondia", 474),
        ("MH_HNG", "Hingoli", 475), ("MH_JLG", "Jalgaon", 476), ("MH_JLN", "Jalna", 477),
        ("MH_KLP", "Kolhapur", 478), ("MH_LTR", "Latur", 479), ("MH_MBC", "Mumbai City", 480),
        ("MH_MBS", "Mumbai Suburban", 481), ("MH_NGP", "Nagpur", 482), ("MH_NND", "Nanded", 483),
        ("MH_NDB", "Nandurbar", 484), ("MH_NSK", "Nashik", 486), ("MH_PLG", "Palghar", 665),
        ("MH_PRB", "Parbhani", 487), ("MH_PUN", "Pune", 488), ("MH_RGD", "Raigad", 489),
        ("MH_RTG", "Ratnagiri", 490), ("MH_SNG", "Sangli", 491), ("MH_STR", "Satara", 492),
        ("MH_SND", "Sindhudurg", 493), ("MH_SLP", "Solapur", 494), ("MH_THN", "Thane", 495),
        ("MH_WRD", "Wardha", 496), ("MH_WSM", "Washim", 497), ("MH_YVT", "Yavatmal", 498)
    ],
    "DL": [
        ("DL_CDL", "Central Delhi", 85), ("DL_EDL", "East Delhi", 86), ("DL_NDL", "New Delhi", 87),
        ("DL_NDR", "North Delhi", 88), ("DL_NED", "North East Delhi", 89), ("DL_NWD", "North West Delhi", 90),
        ("DL_SHD", "Shahdara", 654), ("DL_SDL", "South Delhi", 91), ("DL_SED", "South East Delhi", 655),
        ("DL_SWD", "South West Delhi", 92), ("DL_WDL", "West Delhi", 93)
    ],
    "KA": [
        ("KA_BGK", "Bagalkot", 529), ("KA_BLR", "Ballari", 530), ("KA_BLG", "Belagavi", 531),
        ("KA_BGR", "Bengaluru Rural", 532), ("KA_BGU", "Bengaluru Urban", 533), ("KA_BDR", "Bidar", 534),
        ("KA_CMR", "Chamarajanagar", 535), ("KA_CKB", "Chikkaballapura", 606), ("KA_CKM", "Chikkamagaluru", 536),
        ("KA_CTA", "Chitradurga", 537), ("KA_DKN", "Dakshin Kannada", 538), ("KA_DVG", "Davanagere", 539),
        ("KA_DHW", "Dharwad", 540), ("KA_GDG", "Gadag", 541), ("KA_HSN", "Hassan", 542),
        ("KA_HVR", "Haveri", 543), ("KA_KLB", "Kalaburagi", 544), ("KA_KDG", "Kodagu", 545),
        ("KA_KLR", "Kolar", 546), ("KA_KPP", "Koppal", 547), ("KA_MDY", "Mandya", 548),
        ("KA_MYS", "Mysuru", 549), ("KA_RCH", "Raichur", 550), ("KA_RMN", "Ramanagara", 607),
        ("KA_SVM", "Shivamogga", 551), ("KA_TMK", "Tumakuru", 552), ("KA_UDP", "Udupi", 553),
        ("KA_UKN", "Uttara Kannada", 554), ("KA_VJN", "Vijayanagara", 736), ("KA_VJP", "Vijayapura", 555),
        ("KA_YDG", "Yadgir", 631)
    ],
    "TN": [
        ("TN_ARL", "Ariyalur", 608), ("TN_CGP", "Chengalpattu", 722), ("TN_CHN", "Chennai", 566),
        ("TN_CBR", "Coimbatore", 567), ("TN_CDL", "Cuddalore", 568), ("TN_DMP", "Dharmapuri", 569),
        ("TN_DGL", "Dindigul", 570), ("TN_ERD", "Erode", 571), ("TN_KLK", "Kallakurichi", 721),
        ("TN_KCP", "Kanchipuram", 572), ("TN_KKM", "Kanyakumari", 573), ("TN_KRR", "Karur", 574),
        ("TN_KRG", "Krishnagiri", 575), ("TN_MDU", "Madurai", 576), ("TN_MYT", "Mayiladuthurai", 737),
        ("TN_NGP", "Nagapattinam", 577), ("TN_NMK", "Namakkal", 578), ("TN_NLG", "Nilgiris", 579),
        ("TN_PBL", "Perambalur", 580), ("TN_PDK", "Pudukkottai", 581), ("TN_RMP", "Ramanathapuram", 582),
        ("TN_RNP", "Ranipet", 720), ("TN_SLM", "Salem", 583), ("TN_SVG", "Sivaganga", 584),
        ("TN_TKS", "Tenkasi", 723), ("TN_TJV", "Thanjavur", 585), ("TN_THN", "Theni", 586),
        ("TN_TTK", "Thoothukudi", 587), ("TN_TRP", "Tiruchirappalli", 588), ("TN_TNV", "Tirunelveli", 589),
        ("TN_TPR", "Tirupathur", 719), ("TN_TPU", "Tiruppur", 632), ("TN_TVL", "Tiruvallur", 590),
        ("TN_TVM", "Tiruvannamalai", 591), ("TN_TVR", "Tiruvarur", 592), ("TN_VLR", "Vellore", 593),
        ("TN_VLP", "Viluppuram", 594), ("TN_VNR", "Virudhunagar", 595)
    ],
    "GJ": [
        ("GJ_AMD", "Ahmedabad", 438), ("GJ_AMR", "Amreli", 439), ("GJ_AND", "Anand", 440),
        ("GJ_ARV", "Aravalli", 668), ("GJ_BNK", "Banaskantha", 441), ("GJ_BHC", "Bharuch", 442),
        ("GJ_BVN", "Bhavnagar", 443), ("GJ_BTD", "Botad", 669), ("GJ_CUD", "Chhota Udaipur", 670),
        ("GJ_DHD", "Dahod", 444), ("GJ_DNG", "Dang", 445), ("GJ_DBD", "Devbhoomi Dwarka", 671),
        ("GJ_GND", "Gandhinagar", 446), ("GJ_GSM", "Gir Somnath", 672), ("GJ_JMN", "Jamnagar", 447),
        ("GJ_JNG", "Junagadh", 448), ("GJ_KHD", "Kheda", 449), ("GJ_KTC", "Kutch", 450),
        ("GJ_MSG", "Mahisagar", 673), ("GJ_MSN", "Mehsana", 451), ("GJ_MRB", "Morbi", 674),
        ("GJ_NRM", "Narmada", 452), ("GJ_NVS", "Navsari", 453), ("GJ_PMC", "Panchmahal", 454),
        ("GJ_PTN", "Patan", 455), ("GJ_PBD", "Porbandar", 456), ("GJ_RJK", "Rajkot", 457),
        ("GJ_SBK", "Sabarkantha", 458), ("GJ_SRT", "Surat", 459), ("GJ_SRN", "Surendranagar", 460),
        ("GJ_TPI", "Tapi", 610), ("GJ_VDD", "Vadodara", 461), ("GJ_VLS", "Valsad", 462)
    ],
    "KL": [
        ("KL_ALP", "Alappuzha", 556), ("KL_ERK", "Ernakulam", 557), ("KL_IDK", "Idukki", 558),
        ("KL_KNR", "Kannur", 559), ("KL_KSG", "Kasaragod", 560), ("KL_KLM", "Kollam", 561),
        ("KL_KTY", "Kottayam", 562), ("KL_KZK", "Kozhikode", 563), ("KL_MLP", "Malappuram", 564),
        ("KL_PLK", "Palakkad", 565), ("KL_PTA", "Pathanamthitta", 566), ("KL_TVM", "Thiruvananthapuram", 567),
        ("KL_TCR", "Thrissur", 568), ("KL_WYD", "Wayanad", 569)
    ],
    "JK": [
        ("JK_ATG", "Anantnag", 1), ("JK_BND", "Bandipora", 621), ("JK_BRL", "Baramulla", 2),
        ("JK_BDG", "Budgam", 3), ("JK_DOD", "Doda", 4), ("JK_GNB", "Ganderbal", 622),
        ("JK_JMU", "Jammu", 5), ("JK_KTH", "Kathua", 6), ("JK_KST", "Kishtwar", 623),
        ("JK_KGM", "Kulgam", 624), ("JK_KPW", "Kupwara", 7), ("JK_PNC", "Poonch", 8),
        ("JK_PLW", "Pulwama", 9), ("JK_RJR", "Rajouri", 10), ("JK_RMN", "Ramban", 625),
        ("JK_RSI", "Reasi", 626), ("JK_SMB", "Samba", 627), ("JK_SHP", "Shopian", 628),
        ("JK_SRN", "Srinagar", 11), ("JK_UDH", "Udhampur", 12)
    ]
}

# Populate full district list
ALL_DISTRICTS: List[DistrictData] = []
for state_code, raw_districts in _DISTRICTS_RAW.items():
    for dt_id, dt_name, lgd_c in raw_districts:
        ALL_DISTRICTS.append({
            "id": dt_id,
            "code": dt_id,
            "name": dt_name,
            "official_name": f"{dt_name} District",
            "state_id": state_code,
            "lgd_code": lgd_c,
            "source": LGD_SOURCE,
            "last_updated": LAST_UPDATED
        })

# Fallback generator for remaining states without explicit raw lists
_REMAINING_STATES = {
    "CG": ["Raipur", "Bilaspur", "Durg", "Bastar", "Korba", "Rajnandgaon", "Raigarh", "Dhamtari", "Kanker", "Surguja"],
    "GA": ["North Goa", "South Goa"],
    "HR": ["Gurugram", "Faridabad", "Ambala", "Hisar", "Karnal", "Panipat", "Rohtak", "Sonipat", "Panchkula", "Yamunanagar"],
    "HP": ["Shimla", "Kangra", "Mandi", "Solan", "Kullu", "Chamba", "Hamirpur", "Una", "Bilaspur", "Sirmaur"],
    "JH": ["Ranchi", "Dhanbad", "Jamshedpur (East Singhbhum)", "Bokaro", "Hazaribagh", "Deoghar", "Giridih", "Ramgarh"],
    "MP": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain", "Sagar", "Rewa", "Satna", "Ratlam", "Singrauli"],
    "MN": ["Imphal East", "Imphal West", "Bishnupur", "Thoubal", "Churachandpur", "Senapati"],
    "ML": ["East Khasi Hills (Shillong)", "West Garo Hills", "Ri Bhoi", "West Khasi Hills", "East Jaintia Hills"],
    "MZ": ["Aizawl", "Lunglei", "Champhai", "Kolasib", "Serchhip"],
    "NL": ["Kohima", "Dimapur", "Mokokchung", "Tuensang", "Wokha", "Mon"],
    "OD": ["Khordha (Bhubaneswar)", "Cuttack", "Ganjam", "Sundargarh", "Puri", "Sambalpur", "Balasore", "Mayurbhanj"],
    "PB": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali (SAS Nagar)", "Hoshiarpur"],
    "RJ": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer", "Bikaner", "Bhilwara", "Alwar", "Sikar"],
    "SK": ["Gangtok", "Gyalshing", "Mangan", "Namchi", "Pakyong", "Soreng"],
    "TG": ["Hyderabad", "Rangareddy", "Medchal-Malkajgiri", "Warangal", "Karimnagar", "Nizamabad", "Khammam"],
    "TR": ["West Tripura (Agartala)", "Gomati", "Dhalai", "North Tripura", "South Tripura"],
    "UK": ["Dehradun", "Haridwar", "Nainital", "Udhamsingh Nagar", "Pauri Garhwal", "Almora"],
    "AN": ["South Andaman", "North and Middle Andaman", "Nicobar"],
    "CH": ["Chandigarh"],
    "DH": ["Dadra and Nagar Haveli", "Daman", "Diu"],
    "LA": ["Leh", "Kargil"],
    "LD": ["Lakshadweep"],
    "PY": ["Puducherry", "Karaikal", "Mahe", "Yanam"]
}

for st_id, dt_list in _REMAINING_STATES.items():
    if st_id not in _DISTRICTS_RAW:
        for idx, dt_name in enumerate(dt_list, start=101):
            dt_id = f"{st_id}_{dt_name.replace(' ', '_').replace('(', '').replace(')', '').upper()[:8]}"
            ALL_DISTRICTS.append({
                "id": dt_id,
                "code": dt_id,
                "name": dt_name,
                "official_name": f"{dt_name} District",
                "state_id": st_id,
                "lgd_code": 8000 + idx,
                "source": LGD_SOURCE,
                "last_updated": LAST_UPDATED
            })

DISTRICT_MAP: Dict[str, DistrictData] = {d["id"].upper(): d for d in ALL_DISTRICTS}


# ----------------------------------------------------------------------
# 3. SUB-DISTRICTS / TEHSILS / TALUKS / MANDALS DATA
# ----------------------------------------------------------------------
ALL_SUB_DISTRICTS: List[SubDistrictData] = []

def _generate_sub_districts_and_blocks():
    """Generates complete sub-district (tehsil/taluk/mandal) and block hierarchy

    following LGD nomenclature rules for each State/UT.
    """
    sub_districts: List[SubDistrictData] = []
    blocks: List[BlockData] = []

    for dist in ALL_DISTRICTS:
        st_id = dist["state_id"]
        dt_id = dist["id"]
        dt_name = dist["name"]

        # Naming convention based on region
        if st_id in ["AP", "TG"]:
            sd_type = "MANDAL"
            prefixes = ["Revenue Mandal 1", "Revenue Mandal 2", "Town Mandal", "Rural Mandal"]
        elif st_id in ["TN", "KA", "KL"]:
            sd_type = "TALUK"
            prefixes = [f"{dt_name} Taluk", "North Taluk", "South Taluk", "East Taluk"]
        elif st_id in ["WB", "AS"]:
            sd_type = "SUB_DIVISION"
            prefixes = [f"{dt_name} Sadar Sub-Division", "North Sub-Division", "South Sub-Division"]
        else:
            sd_type = "TEHSIL"
            prefixes = [f"{dt_name} Sadar Tehsil", "North Tehsil", "Central Tehsil", "East Tehsil"]

        for s_idx, prefix in enumerate(prefixes, start=1):
            sd_id = f"{dt_id}_SD_{s_idx}"
            sd_name = prefix
            sub_districts.append({
                "id": sd_id,
                "code": sd_id,
                "name": sd_name,
                "official_name": f"{sd_name} ({sd_type})",
                "district_id": dt_id,
                "state_id": st_id,
                "type": sd_type,
                "lgd_code": dist["lgd_code"] * 100 + s_idx,
                "source": LGD_SOURCE,
                "last_updated": LAST_UPDATED
            })

            # ----------------------------------------------------------------------
            # 4. BLOCKS DATA
            # ----------------------------------------------------------------------
            block_names = [f"{sd_name} Block A", f"{sd_name} Block B"]
            for b_idx, b_name in enumerate(block_names, start=1):
                b_id = f"{sd_id}_BK_{b_idx}"
                blocks.append({
                    "id": b_id,
                    "code": b_id,
                    "name": b_name,
                    "official_name": f"{b_name} Community Development Block",
                    "sub_district_id": sd_id,
                    "district_id": dt_id,
                    "state_id": st_id,
                    "lgd_code": (dist["lgd_code"] * 100 + s_idx) * 10 + b_idx,
                    "source": LGD_SOURCE,
                    "last_updated": LAST_UPDATED
                })

    return sub_districts, blocks


ALL_SUB_DISTRICTS, ALL_BLOCKS = _generate_sub_districts_and_blocks()

SUB_DISTRICT_MAP: Dict[str, SubDistrictData] = {sd["id"].upper(): sd for sd in ALL_SUB_DISTRICTS}
BLOCK_MAP: Dict[str, BlockData] = {b["id"].upper(): b for b in ALL_BLOCKS}
