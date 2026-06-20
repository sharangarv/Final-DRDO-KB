"""
Seeds the Laboratory table with all known DRDO labs.
Run once:  python manage.py shell -c "from crawler.seed_labs import seed; seed()"
Or via:    python manage.py seed_labs
"""

DRDO_LABS = [
    # (acronym, name, city, state, cluster)
    ("ARDE",   "Armament Research and Development Establishment",            "Pune",       "Maharashtra", "Armaments & Combat Engineering"),
    ("CAIR",   "Centre for Artificial Intelligence and Robotics",            "Bangalore",  "Karnataka",   "Electronics & Communication Systems"),
    ("CEMILAC","Centre for Military Airworthiness and Certification",        "Bangalore",  "Karnataka",   "Aeronautical Systems"),
    ("CFEES",  "Centre for Fire Explosive and Environment Safety",           "Delhi",      "Delhi",       "Armaments & Combat Engineering"),
    ("CHESS",  "Centre for High Energy Systems and Sciences",                "Hyderabad",  "Telangana",   "Armaments & Combat Engineering"),
    ("CLAWS",  "Centre for Land Warfare Studies",                            "Delhi",      "Delhi",       "Other"),
    ("CMERI",  "Central Mechanical Engineering Research Institute",          "Durgapur",   "West Bengal", "Other"),
    ("DEAL",   "Defence Electronics Application Laboratory",                 "Dehradun",   "Uttarakhand", "Electronics & Communication Systems"),
    ("DEBEL",  "Defence Bioengineering and Electromedical Laboratory",       "Bangalore",  "Karnataka",   "Life Sciences"),
    ("DFRL",   "Defence Food Research Laboratory",                           "Mysuru",     "Karnataka",   "Life Sciences"),
    ("DIP",    "Defence Institute of Physiology and Allied Sciences",        "Delhi",      "Delhi",       "Life Sciences"),
    ("DIPR",   "Defence Institute of Psychological Research",                "Delhi",      "Delhi",       "Life Sciences"),
    ("DIBER",  "Defence Institute of Bio-Energy Research",                   "Haldwani",   "Uttarakhand", "Life Sciences"),
    ("DMSRDE", "Defence Materials and Stores Research and Development Establishment","Kanpur","Uttar Pradesh","Materials, Explosives & Propellants"),
    ("DRDL",   "Defence Research and Development Laboratory",                "Hyderabad",  "Telangana",   "Missiles & Strategic Systems"),
    ("DRDO HQ","DRDO Headquarters",                                          "Delhi",      "Delhi",       "Headquarters"),
    ("DRDE",   "Defence Research and Development Establishment",             "Gwalior",    "Madhya Pradesh","NBC Protection"),
    ("DTRL",   "Defence Technology and Research Lab",                        "Delhi",      "Delhi",       "Other"),
    ("DYSL",   "DRDO Young Scientists Laboratory",                           "Mumbai",     "Maharashtra", "Other"),
    ("GTRE",   "Gas Turbine Research Establishment",                         "Bangalore",  "Karnataka",   "Aeronautical Systems"),
    ("HEMRL",  "High Energy Materials Research Laboratory",                  "Pune",       "Maharashtra", "Materials, Explosives & Propellants"),
    ("INMAS",  "Institute of Nuclear Medicine and Allied Sciences",          "Delhi",      "Delhi",       "Life Sciences"),
    ("IRDE",   "Instruments Research and Development Establishment",         "Dehradun",   "Uttarakhand", "Electronics & Communication Systems"),
    ("ITR",    "Integrated Test Range",                                      "Chandipur",  "Odisha",      "Missiles & Strategic Systems"),
    ("LRDE",   "Electronics and Radar Development Establishment",            "Bangalore",  "Karnataka",   "Electronics & Communication Systems"),
    ("MTRDC",  "Microwave Tube Research and Development Centre",             "Bangalore",  "Karnataka",   "Electronics & Communication Systems"),
    ("NAL",    "National Aerospace Laboratories",                            "Bangalore",  "Karnataka",   "Aeronautical Systems"),
    ("NMRL",   "Naval Materials Research Laboratory",                        "Ambernath",  "Maharashtra", "Naval Systems & Materials"),
    ("NPO",    "Naval Physical and Oceanographic Laboratory",                "Kochi",      "Kerala",      "Naval Systems & Materials"),
    ("NSTL",   "Naval Science and Technological Laboratory",                 "Visakhapatnam","Andhra Pradesh","Naval Systems & Materials"),
    ("PXE",    "Proof and Experimental Establishment",                       "Balasore",   "Odisha",      "Armaments & Combat Engineering"),
    ("R&DE(E)","Research & Development Establishment (Engineers)",           "Pune",       "Maharashtra", "Armaments & Combat Engineering"),
    ("SAC",    "Space Applications Centre",                                  "Ahmedabad",  "Gujarat",     "Other"),
    ("SAG",    "Scientific Analysis Group",                                  "Delhi",      "Delhi",       "Electronics & Communication Systems"),
    ("SAMEER", "Society for Applied Microwave Electronics Engineering and Research","Mumbai","Maharashtra","Electronics & Communication Systems"),
    ("SASE",   "Snow and Avalanche Study Establishment",                     "Chandigarh", "Chandigarh",  "Other"),
    ("SSPL",   "Solid State Physics Laboratory",                             "Delhi",      "Delhi",       "Materials, Explosives & Propellants"),
    ("TBRL",   "Terminal Ballistics Research Laboratory",                    "Chandigarh", "Chandigarh",  "Armaments & Combat Engineering"),
    ("VRDE",   "Vehicles Research and Development Establishment",            "Ahmednagar", "Maharashtra", "Armaments & Combat Engineering"),
]


def seed():
    from knowledge_base.models import Laboratory
    created = 0
    for acronym, name, city, state, cluster in DRDO_LABS:
        _, made = Laboratory.objects.get_or_create(
            name=name,
            defaults=dict(acronym=acronym, city=city, state=state, cluster=cluster)
        )
        if made:
            created += 1
    print(f"✅ Labs seeded: {created} new / {len(DRDO_LABS) - created} already existed")
