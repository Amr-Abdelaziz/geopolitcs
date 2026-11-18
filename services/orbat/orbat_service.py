"""Order of Battle (ORBAT) Service.

Constructs comprehensive, militarily accurate hierarchical command structures,
unit dossiers, echelon relationships, and readiness statuses for Egypt, Libya, and Israel.
"""
from typing import Dict, List, Optional
from packages.schemas.models import OrbatUnit, OrbatTreeResponse


class OrbatService:
    """Provides interactive hierarchical Order of Battle structures and unit dossiers."""

    def __init__(self):
        self._units: Dict[str, OrbatUnit] = {}
        self._init_database()

    def _init_database(self):
        """Seed high-fidelity ORBAT units for target countries."""
        all_units: List[OrbatUnit] = [
            # =========================================================================
            # 🇪🇬 EGYPTIAN ARMED FORCES (EAF) - القوات المسلحة المصرية
            # =========================================================================
            OrbatUnit(
                id="EAF-GHQ",
                name_ar="القيادة العامة للقوات المسلحة المصرية",
                name_en="Egyptian Armed Forces GHQ & General Staff",
                country="Egypt",
                echelon="GHQ",
                branch="Joint",
                hq_location="مجمع القيادة الاستراتيجية (الأوكتاجون) - العاصمة الإدارية / القاهرة",
                commander="القائد العام للقوات المسلحة وزير الدفاع والإنتاج الحربي",
                role_and_mission="القيادة العليا والسيطرة الاستراتيجية على كافة أفرع وتشكيلات القوات المسلحة وإدارة مسارح العمليات وتأمين السيادة الوطنية الشاملة.",
                equipment=["شبكات القيادة والسيطرة C4ISR المشتركة", "منظومات الأقمار الصناعية العسكرية (طيبة-1)", "مراكز العمليات المشتركة المؤمنة"],
                readiness_status="High Readiness",
                parent_id=None,
                badge_symbol="🦅",
                badge_color="#10b981"
            ),

            # --- EAF: Western Military Zone (الاتجاه الاستراتيجي الغربي والحدود الليبية) ---
            OrbatUnit(
                id="EAF-WEST-ZONE",
                name_ar="قيادة المنطقة الغربية العسكرية",
                name_en="Western Military Zone Command",
                country="Egypt",
                echelon="Theatre",
                branch="Ground",
                hq_location="سيدي براني / مرسى مطروح",
                commander="قائد المنطقة الغربية العسكرية",
                role_and_mission="تأمين الاتجاه الاستراتيجي الغربي بالكامل والعمق الصحراوي مع ليبيا، وحماية الشريط الحدودي ومكافحة التسلل والتهريب العابر للحدود.",
                equipment=["دبابات قتال رئيسية M1A1 Abrams", "مركبات مدرعة YPR-765 / BMP-1", "منظومات رادار كشف بعيد المدى", "طائرات بدون طيار للمراقبة الحدودية"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="🛡️",
                badge_color="#10b981"
            ),
            OrbatUnit(
                id="EAF-BDE-BORDER-WEST",
                name_ar="لواء حرس الحدود الغربي وأفواج الهجانة",
                name_en="Western Border Guard Brigade",
                country="Egypt",
                echelon="Brigade",
                branch="Border Guard",
                hq_location="منفذ السلوم البري / خط الحدود الدولية",
                commander="قائد قطاع حرس الحدود الغربي",
                role_and_mission="إحكام السيطرة التامة على منفذ السلوم الدولي، وتسيير دوريات رادارية واستطلاع راكب على امتداد السلك الحدودي الفاصل مع الشرق الليبي.",
                equipment=["مركبات مصفحة طراز تمساح وفهد", "أنظمة استشعار حراري وأبراج مراقبة إلكترونية", "طائرات خفيفة للدوريات الصحراوية"],
                readiness_status="High Readiness",
                parent_id="EAF-WEST-ZONE",
                badge_symbol="🐪",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-BASE-JULY3",
                name_ar="قاعدة 3 يوليو البحرية والأسطول الشمالي",
                name_en="July 3 Naval Base & Northern Fleet",
                country="Egypt",
                echelon="Base",
                branch="Naval",
                hq_location="منطقة جرجوب - الساحل الشمالي الغربي (البحر المتوسط)",
                commander="قائد الأسطول الشمالي وقاعدة 3 يوليو",
                role_and_mission="حماية المقدرات الاقتصادية وحقول الغاز بشرق وشمال المتوسط وتأمين خطوط الملاحة البحرية وردع أي تهديدات ساحلية على الاتجاه الغربي.",
                equipment=["فرقاطات FREMM (برجاميني وتحيا مصر)", "غواصات طراز تايب 209 الألمانية", "كورفيتات جويند Gowind 2500", "زوارق صواريخ أمباسادور وسوبر فيتا"],
                readiness_status="High Readiness",
                parent_id="EAF-WEST-ZONE",
                badge_symbol="⚓",
                badge_color="#0284c7"
            ),
            OrbatUnit(
                id="EAF-DIV-33-MECH",
                name_ar="الفرقة 33 مشاة ميكانيكية",
                name_en="33rd Mechanized Infantry Division",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="محور مطروح - السلوم",
                commander="قائد الفرقة 33 ميكانيكي",
                role_and_mission="الرد السريع وتشكيل نسق دفاعي تعبوي مانع في عمق القطاع الغربي للتعامل مع أي خروقات أمنية كبرى.",
                equipment=["مدرعات M113A2", "مدافع هاوتزر ذاتية الحركة M109A2", "راجمات صواريخ صقر", "صواريخ تاو المضادة للدروع"],
                readiness_status="Patrol/Deterrence",
                parent_id="EAF-WEST-ZONE",
                badge_symbol="⚔️",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-BDE-AIRDEF-WEST",
                name_ar="لواء الدفاع الجوي التعبوي الغربي",
                name_en="Western Air Defense Brigade",
                country="Egypt",
                echelon="Brigade",
                branch="Air Defense",
                hq_location="نطاق السلوم وقاعدة جرجوب",
                commander="قائد لواء الدفاع الجوي",
                role_and_mission="فرض مظلة حظر جوي وحماية المنشآت الحيوية والقواعد العسكرية الساحلية ضد أي اختراق جوي أو طائرات مسيرة معادية.",
                equipment=["منظومات Antey-2500 (S-300VM)", "منظومات بوك إم 2 (Buk-M2E)", "منظومات تور إم 2 (Tor-M2)", "رادارات إنذار مبكر رنان وبروتيفنيك"],
                readiness_status="High Readiness",
                parent_id="EAF-WEST-ZONE",
                badge_symbol="🛡️",
                badge_color="#0d9488"
            ),

            # --- EAF: 2nd Field Army (الجيش الثاني الميداني - شمال ووسط سيناء وقناة السويس) ---
            OrbatUnit(
                id="EAF-2ND-ARMY",
                name_ar="قيادة الجيش الثاني الميداني",
                name_en="2nd Field Army Command",
                country="Egypt",
                echelon="Army",
                branch="Ground",
                hq_location="الإسماعيلية / قطاع شمال سيناء",
                commander="قائد الجيش الثاني الميداني",
                role_and_mission="تأمين الاتجاه الاستراتيجي الشمالي الشرقي، وحماية المجرى الملاحي لقناة السويس وشمال شبه جزيرة سيناء والحدود الشرقية الدولية.",
                equipment=["دبابات قتال M1A1 Abrams", "مركبات قتال مشاة مصفحة", "مدفعية ثقيلة وصاروخية بعيدة المدى", "مروحيات هجومية أباتشي AH-64D"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="⚔️",
                badge_color="#10b981"
            ),
            OrbatUnit(
                id="EAF-DIV-18-MECH",
                name_ar="الفرقة 18 مشاة ميكانيكية",
                name_en="18th Mechanized Infantry Division",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="القنطرة شرق / بئر العبد - شمال سيناء",
                commander="قائد الفرقة 18 ميكانيكي",
                role_and_mission="تأمين المحاور والدروب التعبوية المؤدية إلى عمق سيناء وتأمين الضفة الشرقية لقناة السويس.",
                equipment=["ناقلات جند مدرعة YPR", "دبابات M1A1", "راجمات صواريخ كاتيوشا وصقر 45"],
                readiness_status="High Readiness",
                parent_id="EAF-2ND-ARMY",
                badge_symbol="🛡️",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-DIV-6-ARMOR",
                name_ar="الفرقة 6 مدرعة",
                name_en="6th Armored Division",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="وسط سيناء / الإسماعيلية",
                commander="قائد الفرقة 6 مدرع",
                role_and_mission="القوة الضاربة التعبوية للردع والمناورة السريعة في المسرح السيناوي وصد أي محاولات اختراق مدرعة.",
                equipment=["ألوية دبابات أبرامز الحديثة", "مركبات قتال برادلي ومدرعات سيناتور", "مدافع هاوتزر K9A1EGY الموجهة"],
                readiness_status="High Readiness",
                parent_id="EAF-2ND-ARMY",
                badge_symbol="⚡",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-BDE-BORDER-SINAI",
                name_ar="لواء حرس الحدود بشمال سيناء ومنافذ رفح",
                name_en="Sinai Border Guard Brigade (Rafah Sector)",
                country="Egypt",
                echelon="Brigade",
                branch="Border Guard",
                hq_location="رفح المصرية / الشيخ زويد / محور الحدود",
                commander="قائد قطاع حدود رفح",
                role_and_mission="تأمين خط الحدود الدولية مع قطاع غزة وإسرائيل، ومنع التسلل والتهريب، وإحكام السيطرة الكاملة على المنفذ الحدودي والمنطقة العازلة.",
                equipment=["مدرعات تمساح شيربا مقاومة للألغام MRAP", "أبراج رصد بانورامية وكاميرات حرارية بعيدة المدى", "معدات كشف الأنفاق التحت أرضية"],
                readiness_status="High Readiness",
                parent_id="EAF-2ND-ARMY",
                badge_symbol="🚧",
                badge_color="#047857"
            ),

            # --- EAF: 3rd Field Army (الجيش الثالث الميداني - جنوب سيناء والبحر الأحمر) ---
            OrbatUnit(
                id="EAF-3RD-ARMY",
                name_ar="قيادة الجيش الثالث الميداني",
                name_en="3rd Field Army Command",
                country="Egypt",
                echelon="Army",
                branch="Ground",
                hq_location="السويس / قطاع وسط وجنوب سيناء",
                commander="قائد الجيش الثالث الميداني",
                role_and_mission="تأمين المدخل الجنوبي لقناة السويس، وتأمين خليج السويس ومضايق البحر الأحمر وشبه جزيرة سيناء الجنوبية وحقول البترول والتعدين.",
                equipment=["دبابات M1A1 Abrams", "مدفعية ذاتية الحركة M109", "مروحيات مقاتلة كاموف Ka-52 وأباتشي"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="⚔️",
                badge_color="#10b981"
            ),
            OrbatUnit(
                id="EAF-DIV-4-ARMOR",
                name_ar="الفرقة 4 مدرعة (فرسان مدرعات القوات المسلحة)",
                name_en="4th Armored Division (Knights of EAF)",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="السويس",
                commander="قائد الفرقة 4 مدرع",
                role_and_mission="الاحتياطي الاستراتيجي المدرع الأقوى للدولة المصرية والجاهز للتدخل التعبوي الفوري في أي اتجاه عملياتي حرج.",
                equipment=["ألوية دبابات M1A1 المحدثة", "مركبات قتال مدرعة متطورة", "كتائب دفاع جوي شيلكا وتور إم"],
                readiness_status="High Readiness",
                parent_id="EAF-3RD-ARMY",
                badge_symbol="🛡️",
                badge_color="#059669"
            ),
            OrbatUnit(
                id="EAF-DIV-19-MECH",
                name_ar="الفرقة 19 مشاة ميكانيكية",
                name_en="19th Mechanized Infantry Division",
                country="Egypt",
                echelon="Division",
                branch="Ground",
                hq_location="جنوب سيناء / الطور / شرم الشيخ",
                commander="قائد الفرقة 19 ميكانيكي",
                role_and_mission="تأمين السواحل الجنوبية لسيناء ومضيق تيران والمقرات السيادية والمطارات الدولية بجنوب سيناء.",
                equipment=["مدرعات خفيفة ودبابات دعم", "صواريخ كورنيت المضادة للدروع", "رادارات مراقبة بحرية وجوية"],
                readiness_status="Patrol/Deterrence",
                parent_id="EAF-3RD-ARMY",
                badge_symbol="🌊",
                badge_color="#059669"
            ),

            # --- EAF: Strategic Naval Fleets & Berenice Base (القوات البحرية وقاعدة برنيس) ---
            OrbatUnit(
                id="EAF-NAVY-SOUTH",
                name_ar="قيادة الأسطول الجنوبي وقاعدة برنيس العسكرية",
                name_en="Southern Fleet Command & Berenice Base",
                country="Egypt",
                echelon="Base",
                branch="Naval",
                hq_location="قاعدة برنيس العسكرية - رأس بناس (البحر الأحمر)",
                commander="قائد الأسطول الجنوبي بالبحر الأحمر",
                role_and_mission="حماية الملاحة الدولية في البحر الأحمر ومضيق باب المندب وتأمين المداخل الجنوبية لقناة السويس ومنع أي تهديدات بحرية موجهة للمياه السيادية.",
                equipment=["حاملتي المروحيات ميسترال (أنور السادات وجمال عبد الناصر)", "فرقاطات بيري وبيري-Fremm", "كورفيتات ميكو A200 المتطورة", "مروحيات بحرية سي سبرايت وسوبر سي ليون"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="⚓",
                badge_color="#0284c7"
            ),

            # --- EAF: Special Operations & Elite Forces (قوات الصاعقة والمظلات والتدخل السريع) ---
            OrbatUnit(
                id="EAF-SOF-CMD",
                name_ar="قيادة قوات الصاعقة والمظلات وقوات التدخل السريع",
                name_en="Special Operations Command & Airborne Forces",
                country="Egypt",
                echelon="Corps",
                branch="Special Forces",
                hq_location="إنشاص / القاهرة",
                commander="قائد قوات الصاعقة والمظلات",
                role_and_mission="تنفيذ العمليات الخاصة النوعية خلف خطوط العدو، ومكافحة الإرهاب عالي الخطورة، والانتشار السريع المنقول جواً عبر أي جبهة استراتيجية.",
                equipment=["أسلحة هجومية خاصة وتصويب ليزري", "مروحيات إنزال Chinook CH-47 ومي-24", "عربات صاعقة خفيفة ومظلات تكتيكية"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="⚡",
                badge_color="#f59e0b"
            ),
            OrbatUnit(
                id="EAF-UNIT-777",
                name_ar="الوحدة 777 قتال (مكافحة الإرهاب الدولي)",
                name_en="Task Unit 777 (CT & Hostage Rescue)",
                country="Egypt",
                echelon="Special_Unit",
                branch="Special Forces",
                hq_location="القاهرة",
                commander="قائد الوحدة 777",
                role_and_mission="عمليات تحرير الرهائن ومكافحة الإرهاب الدولي والاقتحام التكتيكي فائق الدقة في كافة البيئات البرية والبحرية والجوية.",
                equipment=["بنادق قنص Sig Sauer و Barrett", "معدات رؤية ليلية جيل رابع", "مركبات اقتحام مدرعة خفيفة"],
                readiness_status="High Readiness",
                parent_id="EAF-SOF-CMD",
                badge_symbol="🎯",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="EAF-UNIT-999",
                name_ar="الوحدة 999 قتال (العمليات الخاصة خلف الخطوط)",
                name_en="Task Unit 999 (Strategic Recon & Deep Strikes)",
                country="Egypt",
                echelon="Special_Unit",
                branch="Special Forces",
                hq_location="إنشاص",
                commander="قائد الوحدة 999",
                role_and_mission="الاستطلاع الاستراتيجي والعمليات الخاصة العميقة والإغارة التخريبية على خطوط إمداد العدو ومراكزه الحيوية.",
                equipment=["تجهيزات إنزال مظلي حر HALO/HAHO", "أسلحة كتم صوت ومعدات تفجير موجّهة", "أجهزة اتصال وتحديد أهداف عبر الأقمار الصناعية"],
                readiness_status="High Readiness",
                parent_id="EAF-SOF-CMD",
                badge_symbol="🦅",
                badge_color="#d97706"
            ),

            # --- EAF: Strategic Air Force & Air Defense Command ---
            OrbatUnit(
                id="EAF-AIRFORCE",
                name_ar="قيادة القوات الجوية المصرية",
                name_en="Egyptian Air Force (EAF Command)",
                country="Egypt",
                echelon="Corps",
                branch="Air Force",
                hq_location="القاهرة / شبكة القواعد الجوية المشتركة",
                commander="قائد القوات الجوية",
                role_and_mission="السيادة الجوية، الاعتراض التكتيكي، والضربات الاستراتيجية بعيدة المدى وتوفير الدعم والإسناد الجوي القريب لكافة التشكيلات البرية والبحرية.",
                equipment=["مقاتلات Rafale F3R الفرنسية", "مقاتلات F-16 C/D Block 52", "مقاتلات MiG-29M/M2 الروسية", "طائرات الإنذار المبكر E-2C Hawkeye", "مسيرات Wing Loong II المسلحة"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="✈️",
                badge_color="#38bdf8"
            ),
            OrbatUnit(
                id="EAF-AIRDEFENSE",
                name_ar="قيادة قوات الدفاع الجوي المصري",
                name_en="Egyptian Air Defense Command (EADC)",
                country="Egypt",
                echelon="Corps",
                branch="Air Defense",
                hq_location="القاهرة / شبكة مراكز القيادة والإنذار",
                commander="قائد قوات الدفاع الجوي",
                role_and_mission="تأمين المجال الجوي السيادي بالكامل وشل قدرة العدو الجوية وتدمير الصواريخ الباليستية والمجنحة والطائرات المسيرة في كافة الارتفاعات.",
                equipment=["منظومات S-300VM / Antey-2500", "منظومات IRIS-T SLM الألمانية", "منظومات Buk-M2E و Tor-M2", "منظومات بيتشورا 2M المطورة", "شبكة رادارات ثلاثية الأبعاد متعددة الطبقات"],
                readiness_status="High Readiness",
                parent_id="EAF-GHQ",
                badge_symbol="🛡️",
                badge_color="#0d9488"
            ),


            # =========================================================================
            # 🇱🇾 LIBYAN ARMED FORMATIONS (LNA & GNU) - التشكيلات العسكرية في ليبيا
            # =========================================================================
            # --- Libyan National Army (القيادة العامة بالشرق - LNA) ---
            OrbatUnit(
                id="LNA-GHQ",
                name_ar="القيادة العامة للقوات المسلحة بالشرق الليبي (LNA)",
                name_en="Libyan National Army GHQ (Eastern Command)",
                country="Libya",
                echelon="GHQ",
                branch="Joint",
                hq_location="الرجمة / بنغازي",
                commander="القائد العام للقوات المسلحة بالشرق",
                role_and_mission="السيطرة العسكرية على إقليم برقة والهلال النفطي والجنوب الشرقي وتأمين الحدود المشتركة مع مصر وتشاد.",
                equipment=["دبابات T-72 و T-62", "مركبات قتال مدرعة BMP-2", "مقاتلات MiG-21 و MiG-23 وسوخوي Su-24", "منظومات دفاع جوي بانتسير Pantsir-S1"],
                readiness_status="High Readiness",
                parent_id=None,
                badge_symbol="🇱🇾",
                badge_color="#f59e0b"
            ),
            OrbatUnit(
                id="LNA-BDE-106",
                name_ar="اللواء 106 مجحفل (النخبة المدرعة)",
                name_en="106th Reinforced Brigade (LNA Elite Armor)",
                country="Libya",
                echelon="Brigade",
                branch="Ground",
                hq_location="بنغازي / الهلال النفطي",
                commander="قيادة اللواء 106",
                role_and_mission="القوة الضاربة الرئيسية لقوات الشرق، تأمين المواقع والموانئ الحيوية والتدخل التكتيكي السريع في مسارح العمليات.",
                equipment=["دبابات قتال رئيسية T-72 حديثة", "مدرعات مدولبة BTR ومصفحات النمر", "مدافع هاوتزر وراجمات جراد"],
                readiness_status="High Readiness",
                parent_id="LNA-GHQ",
                badge_symbol="⚔️",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="LNA-BDE-TBZ",
                name_ar="لواء طارق بن زياد المعزز",
                name_en="Tariq bin Ziyad Enhanced Brigade",
                country="Libya",
                echelon="Brigade",
                branch="Ground",
                hq_location="سبها / الجفرة / برقة",
                commander="قيادة لواء طارق بن زياد",
                role_and_mission="الانتشار الميداني الموسع في مدن الجنوب وقاعدة الجفرة والسيطرة على تقاطعات الطرق الصحراوية الإقليمية.",
                equipment=["عربات مسلحة دفع رباعي تويوتا مجهزة برشاشات ثقيلة", "مدرعات قتال ومدافع هاون", "صواريخ كورنيت موجهة"],
                readiness_status="High Readiness",
                parent_id="LNA-GHQ",
                badge_symbol="🛡️",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="LNA-PFG-OIL",
                name_ar="حرس المنشآت النفطية بالهلال النفطي",
                name_en="Petroleum Facilities Guard (Oil Crescent Sector)",
                country="Libya",
                echelon="Regiment",
                branch="Border Guard",
                hq_location="رأس لانوف / السدرة / البريقة",
                commander="آمر قطاع حرس المنشآت النفطية",
                role_and_mission="تأمين موانئ تصدير النفط الرئيسية وحقول الإنتاج بالهلال النفطي ومنع أي اعتداء أو تخريب للمنشآت الحيوية.",
                equipment=["عربات دوريات صحراوية مسلحة", "معدات رصد ومراقبة للمحطات والموانئ", "أسلحة خفيفة ومتوسطة"],
                readiness_status="Patrol/Deterrence",
                parent_id="LNA-GHQ",
                badge_symbol="🛢️",
                badge_color="#b45309"
            ),
            OrbatUnit(
                id="LNA-SOF-SAIQA",
                name_ar="القوات الخاصة والصاعقة الليبية",
                name_en="LNA Special Forces (Al-Saiqa)",
                country="Libya",
                echelon="Special_Unit",
                branch="Special Forces",
                hq_location="بنغازي",
                commander="آمر القوات الخاصة",
                role_and_mission="مكافحة التشكيلات المسلحة المتطرفة وتنفيذ الإغارات الليلية وحماية المقرات القيادية الحساسة.",
                equipment=["أسلحة قنص واقتحام متطورة", "مركبات مدرعة خفيفة", "أجهزة رصد ليلي وتتبع ميداني"],
                readiness_status="High Readiness",
                parent_id="LNA-GHQ",
                badge_symbol="⚡",
                badge_color="#b45309"
            ),

            # --- Government of National Unity & Western Tripoli Formations (قوات الغرب - GNU) ---
            OrbatUnit(
                id="GNU-GHQ",
                name_ar="رئاسة الأركان العامة وقوات الغرب الليبي (طرابلس)",
                name_en="GNU General Staff & Western Tripoli Formations",
                country="Libya",
                echelon="GHQ",
                branch="Joint",
                hq_location="طرابلس / السرايا الحمراء وقاعدة معيتيقة",
                commander="رئيس الأركان العامة للجيش الليبي (طرابلس)",
                role_and_mission="السيطرة الإدارية والميدانية على العاصمة طرابلس والمنطقة الغربية والمنافذ البحرية والجوية بالتنسيق مع الحلفاء الإقليميين.",
                equipment=["مركبات مصفحة تركية Kirpi و Vuran", "مسيرات بيرقدار Bayraktar TB2", "منظومات دفاع جوي متوسط وقصير المدى Hawk"],
                readiness_status="High Readiness",
                parent_id=None,
                badge_symbol="🏛️",
                badge_color="#f59e0b"
            ),
            OrbatUnit(
                id="GNU-BDE-444",
                name_ar="اللواء 444 قتال (المنطقة العسكرية طرابلس)",
                name_en="444th Combat Brigade (Tripoli Military Zone)",
                country="Libya",
                echelon="Brigade",
                branch="Ground",
                hq_location="طرابلس / ترهونة / بني وليد",
                commander="محمود حمزة (آمر اللواء)",
                role_and_mission="ضبط الأمن ومكافحة عصابات التهريب والهجرة غير الشرعية وتأمين خطوط الإمداد الحيوية الرابطة بين العاصمة والجنوب الغربي.",
                equipment=["مدرعات Kirpi تركية الصنع", "أطقم هاون ومدافع خفيفة", "عربات دفع رباعي مصفحة للتدخل السريع"],
                readiness_status="Active Combat",
                parent_id="GNU-GHQ",
                badge_symbol="⚔️",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="GNU-DEV-RADAA",
                name_ar="جهاز الردع لمكافحة الإرهاب والجريمة المنظمة",
                name_en="Special Deterrence Force (Radaa Counter-Terrorism)",
                country="Libya",
                echelon="Special_Unit",
                branch="Special Forces",
                hq_location="قاعدة ومطار معيتيقة الدولي - طرابلس",
                commander="عبد الرؤوف كارة",
                role_and_mission="تأمين مطار معيتيقة والمؤسسات السيادية بالعاصمة وملاحقة الخلايا الإرهابية وشبكات الجريمة المنظمة.",
                equipment=["مركبات مصفحة تكتيكية", "أسلحة رشاشة وقناصات حديثة", "شبكات اتصالات واستخبارات داخلية"],
                readiness_status="High Readiness",
                parent_id="GNU-GHQ",
                badge_symbol="🛡️",
                badge_color="#d97706"
            ),
            OrbatUnit(
                id="GNU-JOINT-MISRATA",
                name_ar="القوة المشتركة مصراتة ولواء المحجوب",
                name_en="Misrata Joint Force & Central Operations",
                country="Libya",
                echelon="Brigade",
                branch="Ground",
                hq_location="مصراتة / محاور سرت",
                commander="قيادة القوة المشتركة بمصراتة",
                role_and_mission="تأمين مدينة مصراتة ومينائها البحري الحيوي وخط الدفاع الشرقي على مشارف سرت وأبوقرين.",
                equipment=["دبابات T-55 المطورة", "مدافع مضادة للطائرات محملة على مركبات رباعية", "صواريخ ميلان وتاو المضادة للدروع"],
                readiness_status="Patrol/Deterrence",
                parent_id="GNU-GHQ",
                badge_symbol="⚓",
                badge_color="#d97706"
            ),


            # =========================================================================
            # 🇮🇱 ISRAEL DEFENSE FORCES (IDF) - SOUTHERN THEATRE - القيادة الجنوبية
            # =========================================================================
            OrbatUnit(
                id="IDF-GENERAL-STAFF",
                name_ar="هيئة الأركان العامة لجيش الدفاع الإسرائيلي (Matkal)",
                name_en="IDF General Staff (Matkal / Kirya Command)",
                country="Israel",
                echelon="GHQ",
                branch="Joint",
                hq_location="مجمع الكرياه - تل أبيب",
                commander="رئيس هيئة الأركان العامة (Ramatkal)",
                role_and_mission="القيادة والتخطيط الاستراتيجي الشامل للعمليات العسكرية المشتركة على كافة الجبهات الشمالية والجنوبية والداخلية.",
                equipment=["منظومات C4I المتكاملة للجيش الرقمي", "شبكات الاستخبارات العسكرية أمان (Aman / Unit 8200)", "منظومات الحيتس (Arrow 3) ومقلاع داوود والقبة الحديدية"],
                readiness_status="High Readiness",
                parent_id=None,
                badge_symbol="🇮🇱",
                badge_color="#06b6d4"
            ),
            OrbatUnit(
                id="IDF-SOUTH-CMD",
                name_ar="قيادة المنطقة الجنوبية بالجيش الإسرائيلي (Pikud Darom)",
                name_en="IDF Southern Command (Pikud Darom)",
                country="Israel",
                echelon="Theatre",
                branch="Joint",
                hq_location="بئر السبع / معسكر فيلادلفيا الجنوبي",
                commander="قائد القيادة الجنوبية (Aluf)",
                role_and_mission="إدارة مسرح العمليات القتالية في قطاع غزة، وتأمين الحدود المشتركة مع مصر (شبه جزيرة سيناء)، وخليج إيلات والبحر الأحمر.",
                equipment=["دبابات قتال رئيسية Merkava Mk 4M و Barak", "ناقلات جند ثقيلة Namer ومدرعات Eitan", "طائرات مسيرة هجومية Hermes 900 و Eitan"],
                readiness_status="Active Combat",
                parent_id="IDF-GENERAL-STAFF",
                badge_symbol="⚔️",
                badge_color="#0891b2"
            ),
            OrbatUnit(
                id="IDF-DIV-143-GAZA",
                name_ar="فرقة الثعلب (فرقة غزة - Division 143)",
                name_en="143rd Gaza Territorial Division (Foxes of Shimshon)",
                country="Israel",
                echelon="Division",
                branch="Ground",
                hq_location="محيط قطاع غزة / معسكر ريعيم",
                commander="قائد فرقة غزة (Tat Aluf)",
                role_and_mission="قيادة العمليات الميدانية داخل قطاع غزة، والسيطرة التكتيكية على معبر كرم أبو سالم ومحور فيلادلفيا الحدودي.",
                equipment=["دبابات ميركافا مجهزة بمنظومة تروفي Trophy للقتل الصعب", "جرافات مدرعة D9R المحصنة", "أنظمة رادار رصد أهداف أرضية تكتيكية"],
                readiness_status="Active Combat",
                parent_id="IDF-SOUTH-CMD",
                badge_symbol="🦊",
                badge_color="#0891b2"
            ),
            OrbatUnit(
                id="IDF-DIV-80-EDOM",
                name_ar="فرقة إيدوم التعبوية (Division 80 - حدود سيناء والبحر الأحمر)",
                name_en="80th Edom Territorial Division (Sinai & Red Sea Border)",
                country="Israel",
                echelon="Division",
                branch="Border Guard",
                hq_location="جنوب النقب / عوفدا / إيلات",
                commander="قائد فرقة إيدوم",
                role_and_mission="تأمين خط الهدنة والحدود الدولية المقابلة لشبه جزيرة سيناء المصرية، وتأمين خليج إيلات ومنع التهديدات القادمة من البحر الأحمر واليمن.",
                equipment=["مركبات مصفحة طراز Wolf و David", "بطاريات القبة الحديدية البحرية والبرية", "كتائب الاستطلاع والمراقبة التكتيكية الميدانية"],
                readiness_status="High Readiness",
                parent_id="IDF-SOUTH-CMD",
                badge_symbol="🛡️",
                badge_color="#0891b2"
            ),
            OrbatUnit(
                id="IDF-BDE-GIVATI",
                name_ar="لواء جفعاتي المشاة الميكانيكي النخبوي",
                name_en="Givati Infantry Brigade (Brigade 84)",
                country="Israel",
                echelon="Brigade",
                branch="Ground",
                hq_location="مسرح العمليات الجنوبي",
                commander="قائد لواء جفعاتي",
                role_and_mission="قوة رأس الحربة للاقتحام والقتال في المناطق المبنية والمعقدة وتطهير الأنفاق والمواقع المحصنة.",
                equipment=["ناقلات مدرعة ثقيلة نامير Namer", "أسلحة Tavor X95 الهجومية", "صواريخ سبايك Spike الموجهة بدقة"],
                readiness_status="Active Combat",
                parent_id="IDF-DIV-143-GAZA",
                badge_symbol="⚔️",
                badge_color="#06b6d4"
            ),
            OrbatUnit(
                id="IDF-BDE-401",
                name_ar="اللواء 401 مدرع (المسار الحديدي - دبابات ميركافا باراك)",
                name_en="401st Armored Brigade (Iron Tracks)",
                country="Israel",
                echelon="Brigade",
                branch="Ground",
                hq_location="مسرح العمليات الجنوبي",
                commander="قائد اللواء 401 مدرع",
                role_and_mission="الفرقة المدرعة الضاربة التابعة للفرقة 162، تنفيذ المناورة المدرعة العميقة والاشتباك المباشر وتأمين معابر الإمداد.",
                equipment=["دبابات Merkava Mk 4M مع Trophy", "دبابات Barak جيل خامس مع خوذات IronVision", "مركبات استطلاع مدرعة"],
                readiness_status="Active Combat",
                parent_id="IDF-DIV-143-GAZA",
                badge_symbol="🛡️",
                badge_color="#06b6d4"
            ),
            OrbatUnit(
                id="IDF-CORP-YAHALOM",
                name_ar="وحدة الهندسة الخاصة للأنفاق والمتفجرات (ياهالوم)",
                name_en="Yahalom Special Combat Engineering Unit",
                country="Israel",
                echelon="Special_Unit",
                branch="Special Forces",
                hq_location="معسكر سيركين / الجبهة الجنوبية",
                commander="قائد وحدة ياهالوم",
                role_and_mission="تفكيك شبكات الأنفاق تحت الأرض، نزع حقول الألغام المعقدة، والعمليات التخريبية الدقيقة خلف خطوط المواجهة.",
                equipment=["روبوتات استكشاف الأنفاق PackBot", "رادارات اختراق الأرض GPR", "متفجرات موجهة وكبسولات إغلاق الأنفاق"],
                readiness_status="Active Combat",
                parent_id="IDF-SOUTH-CMD",
                badge_symbol="💣",
                badge_color="#0e7490"
            ),
            OrbatUnit(
                id="IDF-AIR-NEVATIM",
                name_ar="قاعدة نيفاتيم الجوية (أسراب F-35I Adir)",
                name_en="Nevatim Air Base (F-35I Stealth Squadrons)",
                country="Israel",
                echelon="Base",
                branch="Air Force",
                hq_location="صحراء النقب / جنوب إسرائيل",
                commander="قائد قاعدة نيفاتيم الجوية",
                role_and_mission="الضربات الجوية الشبحية بعيدة المدى، السيطرة والاعتراض الجوي، وجمع الاستخبارات الإلكترونية فوق مسارح العمليات الإقليمية.",
                equipment=["أسراب F-35I Adir الشبحية", "طائرات الإنذار المبكر والتجسس Gulfstream G550 Eitam/Oron", "طائرات النقل والتزود بالوقود C-130J و KC-46"],
                readiness_status="High Readiness",
                parent_id="IDF-GENERAL-STAFF",
                badge_symbol="✈️",
                badge_color="#38bdf8"
            ),
            OrbatUnit(
                id="IDF-NAVY-EILAT",
                name_ar="سرب الدورية البحرية وقاعدة إيلات (البحر الأحمر)",
                name_en="Eilat Naval Squadron 915 & Red Sea Base",
                country="Israel",
                echelon="Base",
                branch="Naval",
                hq_location="ميناء وقاعدة إيلات البحرية",
                commander="قائد سرب 915 بحري",
                role_and_mission="حماية المنفذ البحري الجنوبي لإسرائيل وميناء إيلات، واعتراض التهديدات البحرية والمسيرات والصواريخ في خليج العقبة.",
                equipment=["زوارق الدورية السريعة Super Dvora Mk III", "سفن الصواريخ Sa'ar 5 و Sa'ar 6 مع القبة الحديدية C-Dome", "أنظمة رادار وسونار ساحلية"],
                readiness_status="High Readiness",
                parent_id="IDF-SOUTH-CMD",
                badge_symbol="⚓",
                badge_color="#0284c7"
            )
        ]

        for u in all_units:
            self._units[u.id] = u

    def get_unit(self, unit_id: str) -> Optional[OrbatUnit]:
        """Retrieve a specific unit dossier by ID."""
        return self._units.get(unit_id)

    def get_orbat_tree(
        self,
        country: Optional[str] = None,
        branch: Optional[str] = None,
        search: Optional[str] = None
    ) -> OrbatTreeResponse:
        """Construct hierarchical tree with recursive sub-units and optional filters."""
        # Filter units
        units_pool = list(self._units.values())

        if country and country.lower() != "all":
            units_pool = [u for u in units_pool if u.country.lower() == country.lower()]

        if branch and branch.lower() != "all":
            units_pool = [u for u in units_pool if u.branch.lower() == branch.lower()]

        if search and search.strip():
            q = search.lower().strip()
            units_pool = [
                u for u in units_pool
                if q in u.name_ar.lower()
                or q in u.name_en.lower()
                or q in u.hq_location.lower()
                or q in u.role_and_mission.lower()
                or any(q in eq.lower() for eq in u.equipment)
            ]

        # Build ID lookup
        pool_ids = {u.id for u in units_pool}

        # Clone units without sub_units initially
        cloned_map: Dict[str, OrbatUnit] = {}
        for u in units_pool:
            cloned = OrbatUnit(
                id=u.id,
                name_ar=u.name_ar,
                name_en=u.name_en,
                country=u.country,
                echelon=u.echelon,
                branch=u.branch,
                hq_location=u.hq_location,
                commander=u.commander,
                role_and_mission=u.role_and_mission,
                equipment=list(u.equipment),
                readiness_status=u.readiness_status,
                parent_id=u.parent_id,
                badge_symbol=u.badge_symbol,
                badge_color=u.badge_color,
                sub_units=[]
            )
            cloned_map[u.id] = cloned

        # Link children to parents
        roots: List[OrbatUnit] = []
        for u in cloned_map.values():
            if u.parent_id and u.parent_id in cloned_map:
                cloned_map[u.parent_id].sub_units.append(u)
            else:
                # Root unit (either no parent or parent filtered out)
                roots.append(u)

        return OrbatTreeResponse(
            country=country or "All",
            total_units=len(units_pool),
            roots=roots,
            flat_units=list(cloned_map.values())
        )
