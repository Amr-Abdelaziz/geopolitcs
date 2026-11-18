"""Strategic OSIRIS - Unified Geopolitical & Military Knowledge Graph Service.
Dynamically constructs an ontological multi-domain intelligence graph linking
strategic actors, military commands, ORBAT units, maritime chokepoints, energy assets, and threat vectors.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from packages.schemas.models import GraphEdge, GraphNode, KnowledgeGraph
from services.orbat.orbat_service import orbat_service

log = logging.getLogger("strategic_osiris.knowledge_graph")


class KnowledgeGraphService:
    """Builder and query engine for the Strategic Geopolitical Knowledge Graph."""

    def __init__(self):
        self._cached_graph: Optional[KnowledgeGraph] = None

    def build_graph(
        self,
        theater: Optional[str] = None,
        node_type: Optional[str] = None
    ) -> KnowledgeGraph:
        """Construct the comprehensive geopolitical intelligence graph with optional filtering."""
        all_nodes: List[GraphNode] = [
            # 1. Egypt Strategic Commands & Military Formations
            GraphNode(
                id="NODE-EGY-HQ",
                label_ar="القيادة العامة للقوات المسلحة المصرية",
                label_en="Egyptian Armed Forces GHQ (The Octagon)",
                node_type="actor",
                country="Egypt",
                theater="egypt",
                details="مركز القيادة والسيطرة الاستراتيجية وإدارة مسارح العمليات وتأمين السيادة الوطنية",
                level=1,
                unit_id="EGY-GHQ",
                latitude=29.988056,
                longitude=31.696111,
                logo_url="https://geoconfirmed.org/files/orbat/a8d29b13-913a-4467-5120-08de29b2f6ef.png",
                doctrine_ref="DOC-EGY-001"
            ),
            GraphNode(
                id="NODE-EGY-WEST",
                label_ar="المنطقة العسكرية الغربية وقاعدة 3 يوليو",
                label_en="Western Military Zone & July 3 Base",
                node_type="military_unit",
                country="Egypt",
                theater="egypt",
                details="تأمين الاتجاه الاستراتيجي الغربي والساحل الشمالي والعمق الصحراوي مع ليبيا (سيدي براني وجرجوب)",
                level=2,
                unit_id="EGY-WEST-ZONE",
                latitude=31.5975,
                longitude=25.9261,
                doctrine_ref="DOC-EGY-001"
            ),
            GraphNode(
                id="NODE-EGY-SINAI-2",
                label_ar="قيادة الجيش الثاني الميداني",
                label_en="2nd Field Army (Ismailia & North Sinai)",
                node_type="military_unit",
                country="Egypt",
                theater="egypt",
                details="تأمين الاتجاه الاستراتيجي الشمالي الشرقي وقناة السويس وشمال سيناء والمنافذ الحدودية",
                level=2,
                unit_id="EGY-2ND-ARMY",
                latitude=30.6042,
                longitude=32.2722,
                doctrine_ref="DOC-EGY-001"
            ),
            GraphNode(
                id="NODE-EGY-SINAI-3",
                label_ar="قيادة الجيش الثالث الميداني",
                label_en="3rd Field Army (Suez & South Sinai)",
                node_type="military_unit",
                country="Egypt",
                theater="egypt",
                details="تأمين المدخل الجنوبي لقناة السويس وخليج السويس وجنوب سيناء والمنشآت الحيوية",
                level=2,
                unit_id="EGY-3RD-ARMY",
                latitude=29.9668,
                longitude=32.5498,
                doctrine_ref="DOC-EGY-001"
            ),
            GraphNode(
                id="NODE-EGY-NAVY-SOUTH",
                label_ar="قيادة الأسطول الجنوبي وقاعدة برنيس",
                label_en="Southern Fleet & Berenice Military Base",
                node_type="military_unit",
                country="Egypt",
                theater="red_sea",
                details="تأمين الملاحة في البحر الأحمر والاقتراب من مضيق باب المندب والمياه الاقتصادية الجنوبية",
                level=2,
                unit_id="EGY-NAVY-SOUTH",
                latitude=23.9056,
                longitude=35.4744,
                doctrine_ref="DOC-MR-002"
            ),

            # 2. Strategic Chokepoints & Waterways
            GraphNode(
                id="NODE-CHOKE-SUEZ",
                label_ar="قناة السويس",
                label_en="Suez Canal Maritime Artery",
                node_type="chokepoint",
                country="Egypt",
                theater="egypt",
                details="الممر الملاحي العالمي الأهم الرابط بين الشرق والغرب وعصب الإيرادات السيادية المصرية",
                level=1,
                latitude=30.4589,
                longitude=32.3499,
                doctrine_ref="DOC-MR-002"
            ),
            GraphNode(
                id="NODE-CHOKE-MANDAB",
                label_ar="مضيق باب المندب",
                label_en="Bab el-Mandeb Strategic Strait",
                node_type="chokepoint",
                country="Yemen",
                theater="red_sea",
                details="عنق الزجاجة الجنوبي للبحر الأحمر، يخضع لنظام المرور العابر بموجب اتفاقية UNCLOS 1982",
                level=1,
                latitude=12.5833,
                longitude=43.3333,
                doctrine_ref="DOC-MR-002"
            ),
            GraphNode(
                id="NODE-CHOKE-TIRAN",
                label_ar="مضيق تيران وخليج العقبة",
                label_en="Strait of Tiran & Gulf of Aqaba",
                node_type="chokepoint",
                country="Regional",
                theater="red_sea",
                details="المنفذ الملاحي الحيوي لموانئ العقبة وإيلات، يخضع لنظام المرور البريء وضمانات كامب ديفيد",
                level=2,
                latitude=28.0083,
                longitude=34.4639
            ),
            GraphNode(
                id="NODE-CHOKE-SALLUM",
                label_ar="منفذ السلوم - مساعد الحدودي",
                label_en="Sallum - Musa'ed Border Crossing",
                node_type="chokepoint",
                country="Libya",
                theater="libya",
                details="شريان العبور التجاري واللوجستي والرقابة الأمنية المشتركة على الحدود المصرية-الليبية",
                level=2,
                latitude=31.5303,
                longitude=25.1328,
                doctrine_ref="DOC-LBY-003"
            ),

            # 3. Libya Strategic Commands
            GraphNode(
                id="NODE-LBY-LNA",
                label_ar="القيادة العامة للقوات المسلحة بالشرق الليبي (LNA)",
                label_en="Libyan National Army (Eastern Command - Rajma)",
                node_type="actor",
                country="Libya",
                theater="libya",
                details="السيطرة العسكرية على إقليم برقة ومنطقة الهلال النفطي والتنسيق الأمني لضبط الحدود مع مصر",
                level=1,
                unit_id="LBY-LNA-GHQ",
                latitude=32.0667,
                longitude=20.3667,
                doctrine_ref="DOC-LBY-003"
            ),
            GraphNode(
                id="NODE-LBY-GNU",
                label_ar="حكومة الوحدة الوطنية والمنطقة الغربية (GNU)",
                label_en="Government of National Unity (Western Formations - Tripoli)",
                node_type="actor",
                country="Libya",
                theater="libya",
                details="إدارة العاصمة طرابلس وتأمين المنافذ الساحلية ومعبر رأس جدير مع تونس والاتفاقيات البحرية",
                level=1,
                unit_id="LBY-GNU-TRIPOLI",
                latitude=32.8872,
                longitude=13.1913,
                doctrine_ref="DOC-LBY-003"
            ),

            # 4. Levant & Syria Strategic Formations (Node 6474)
            GraphNode(
                id="NODE-SYR-6474",
                label_ar="القوات السورية والتشكيلات الانتقالية",
                label_en="Syria Defense Formations (Post-Dec 2024)",
                node_type="actor",
                country="Syria",
                theater="syria",
                details="التشكيلات العسكرية الانتقالية وفق رصد GeoConfirmed Node 6474 وإعادة تنظيم منظومة الدفاع",
                level=1,
                unit_id="GC-6474",
                latitude=34.8021,
                longitude=38.9968,
                placemark_url="https://geoconfirmed.org/syria",
                doctrine_ref="DOC-SYR-005"
            ),
            GraphNode(
                id="NODE-SYR-GSS",
                label_ar="جهاز الأمن العام السوري (GSS)",
                label_en="General Security Service (Node 6476)",
                node_type="military_unit",
                country="Syria",
                theater="syria",
                details="ضبط الأمن الداخلي وحماية المنشآت الحيوية في حلب ودمشق (GeoConfirmed Node 6476)",
                level=2,
                unit_id="GC-6476",
                latitude=35.830457,
                longitude=38.218583,
                placemark_url="https://geoconfirmed.org/syria/7afac3b7-85f0-4138-59be-08de50a6d34f",
                doctrine_ref="DOC-SYR-005"
            ),
            GraphNode(
                id="NODE-ISR-IDF",
                label_ar="جيش الدفاع الإسرائيلي (IDF)",
                label_en="Israel Defense Forces (Northern & Southern Commands)",
                node_type="actor",
                country="Israel",
                theater="israel",
                details="الانتشار الميداني على جبهة غزة والحدود اللبنانية وهضبة الجولان ومنطقة البحر الأحمر",
                level=1,
                unit_id="GC-34",
                latitude=32.0853,
                longitude=34.7818,
                placemark_url="https://geoconfirmed.org/israel"
            ),

            # 5. Energy Assets & Offshore Resources
            GraphNode(
                id="NODE-RES-ZOHR",
                label_ar="حقل ظهر للغاز الطبيعي في شرق المتوسط",
                label_en="Zohr Offshore Giant Gas Field",
                node_type="resource",
                country="Egypt",
                theater="east_med",
                details="أضخم حقل غاز طبيعي في البحر المتوسط وعماد أمن الطاقة المصري، محمي بأسطول البحرية المقاتل",
                level=2,
                latitude=32.4833,
                longitude=30.8333,
                doctrine_ref="DOC-EMED-004"
            ),
            GraphNode(
                id="NODE-RES-LNG",
                label_ar="محطات إسالة الغاز بإدكو ودمياط (EMGF)",
                label_en="Idku & Damietta LNG Export Facilities",
                node_type="resource",
                country="Egypt",
                theater="east_med",
                details="البنية التحتية الوحيدة لإسالة وتصدير الغاز في شرق المتوسط باتجاه الأسواق الأوروبية",
                level=2,
                latitude=31.3125,
                longitude=30.3014,
                doctrine_ref="DOC-EMED-004"
            ),
            GraphNode(
                id="NODE-RES-OIL-CRESCENT",
                label_ar="موانئ الهلال النفطي الليبي",
                label_en="Libyan Oil Crescent Terminals (Ras Lanuf & Es Sider)",
                node_type="resource",
                country="Libya",
                theater="libya",
                details="عصب تصدير الخام الليبي ومصدر السيولة المالية المتنافس عليها بين المؤسسات الليبية",
                level=2,
                latitude=30.5167,
                longitude=18.5667,
                doctrine_ref="DOC-LBY-003"
            ),

            # 6. Asymmetric Threat Vectors & Non-State Actors
            GraphNode(
                id="NODE-THREAT-HOUTHI",
                label_ar="حركة أنصار الله (الحوثيون)",
                label_en="Ansar Allah (Houthi Forces)",
                node_type="threat",
                country="Yemen",
                theater="red_sea",
                details="إطلاق المسيرات الهجومية والصواريخ المضادة للسفن على السفن العابرة بمضيق باب المندب",
                level=1,
                latitude=15.3694,
                longitude=44.1910,
                doctrine_ref="DOC-MR-002"
            ),
            GraphNode(
                id="NODE-THREAT-RSF",
                label_ar="قوات الدعم السريع (RSF)",
                label_en="Rapid Support Forces (Sudan)",
                node_type="threat",
                country="Sudan",
                theater="red_sea",
                details="تشكيلات مسلحة في مواجهة الجيش السوداني، تهدد استقرار حزام الساحل وتماسك الدولة",
                level=2,
                latitude=15.5007,
                longitude=32.5599,
                doctrine_ref="DOC-SDN-006"
            ),
        ]

        # Strategic Edges / Relationships
        all_edges: List[GraphEdge] = [
            # Command & Security Hierarchies
            GraphEdge(
                source="NODE-EGY-HQ", target="NODE-EGY-WEST",
                relation_ar="قيادة وسيطرة عملياتية", relation_en="Command & Strategic Control",
                edge_type="security", weight=1.0
            ),
            GraphEdge(
                source="NODE-EGY-HQ", target="NODE-EGY-SINAI-2",
                relation_ar="قيادة وسيطرة عملياتية", relation_en="Command & Strategic Control",
                edge_type="security", weight=1.0
            ),
            GraphEdge(
                source="NODE-EGY-HQ", target="NODE-EGY-SINAI-3",
                relation_ar="قيادة وسيطرة عملياتية", relation_en="Command & Strategic Control",
                edge_type="security", weight=1.0
            ),
            GraphEdge(
                source="NODE-EGY-HQ", target="NODE-EGY-NAVY-SOUTH",
                relation_ar="قيادة وتكليف عملياتي", relation_en="Operational Tasking",
                edge_type="security", weight=1.0
            ),

            # Chokepoints Protection
            GraphEdge(
                source="NODE-EGY-SINAI-2", target="NODE-CHOKE-SUEZ",
                relation_ar="تأمين مجرى القناة والقطاع الشمالي", relation_en="Security of North Canal Sector",
                edge_type="security", weight=1.0
            ),
            GraphEdge(
                source="NODE-EGY-SINAI-3", target="NODE-CHOKE-SUEZ",
                relation_ar="تأمين المدخل الجنوبي والمضايق", relation_en="Southern Canal Security",
                edge_type="security", weight=1.0
            ),
            GraphEdge(
                source="NODE-EGY-NAVY-SOUTH", target="NODE-CHOKE-MANDAB",
                relation_ar="دوريات الردع وتأمين الملاحة الدولية", relation_en="Naval Patrols & Deterrence",
                edge_type="security", weight=0.9
            ),
            GraphEdge(
                source="NODE-EGY-NAVY-SOUTH", target="NODE-CHOKE-TIRAN",
                relation_ar="تأمين السيادة والممرات البحرية", relation_en="Sovereignty & Passage Escort",
                edge_type="security", weight=0.85
            ),

            # Border Security & Diplomacy
            GraphEdge(
                source="NODE-EGY-WEST", target="NODE-CHOKE-SALLUM",
                relation_ar="إحكام السيطرة والرقابة على المنفذ", relation_en="Border Defense & Inspection",
                edge_type="security", weight=1.0
            ),
            GraphEdge(
                source="NODE-LBY-LNA", target="NODE-CHOKE-SALLUM",
                relation_ar="تنسيق أمني وعسكري مشترك", relation_en="Joint Border Security Liaison",
                edge_type="alliance", weight=0.8
            ),
            GraphEdge(
                source="NODE-LBY-LNA", target="NODE-RES-OIL-CRESCENT",
                relation_ar="حماية وتأمين منشآت التصدير", relation_en="Protection of Oil Terminals",
                edge_type="resource", weight=0.9
            ),
            GraphEdge(
                source="NODE-LBY-LNA", target="NODE-LBY-GNU",
                relation_ar="توازن ردع وتنسيق عبر لجنة (5+5)", relation_en="Deterrence Equilibrium (5+5)",
                edge_type="surveillance", weight=0.5
            ),

            # Energy Security
            GraphEdge(
                source="NODE-EGY-HQ", target="NODE-RES-ZOHR",
                relation_ar="تأمين بحري وراداري لمنصات الإنتاج", relation_en="Maritime & Air Defense Umbrella",
                edge_type="resource", weight=0.95
            ),
            GraphEdge(
                source="NODE-RES-ZOHR", target="NODE-RES-LNG",
                relation_ar="إمداد غازي وإسالة للتصدير الدولي", relation_en="Gas Feedstock to LNG Plants",
                edge_type="resource", weight=1.0
            ),

            # Levant & Syria
            GraphEdge(
                source="NODE-SYR-6474", target="NODE-SYR-GSS",
                relation_ar="تبعية العمليات المشتركة والأمن الداخلي", relation_en="Internal Security Command",
                edge_type="security", weight=0.85
            ),
            GraphEdge(
                source="NODE-ISR-IDF", target="NODE-SYR-6474",
                relation_ar="ترقب ومراقبة خط فض الاشتباك بالجولان", relation_en="Disengagement Line Surveillance",
                edge_type="conflict", weight=0.75
            ),

            # Threat Vectors Impacting Chokepoints
            GraphEdge(
                source="NODE-THREAT-HOUTHI", target="NODE-CHOKE-MANDAB",
                relation_ar="تهديد واعتراض حركة الملاحة بالمسيرات", relation_en="Drone & Missile Threat Vector",
                edge_type="conflict", weight=1.0
            ),
            GraphEdge(
                source="NODE-CHOKE-MANDAB", target="NODE-CHOKE-SUEZ",
                relation_ar="ارتباط حيوي (تحويل السفن يخفض الإيرادات)", relation_en="Hydrodynamic Maritime Linkage",
                edge_type="resource", weight=0.95
            ),
        ]

        # Apply theater filter if specified
        filtered_nodes = all_nodes
        if theater and theater.lower() != "all":
            t_clean = theater.lower()
            filtered_nodes = [n for n in all_nodes if n.theater.lower() == t_clean or n.theater.lower() == "regional"]

        # Apply node_type filter if specified
        if node_type and node_type.lower() != "all":
            nt_clean = node_type.lower()
            filtered_nodes = [n for n in filtered_nodes if n.node_type.lower() == nt_clean]

        node_ids: Set[str] = {n.id for n in filtered_nodes}
        filtered_edges = [e for e in all_edges if e.source in node_ids and e.target in node_ids]

        theaters = ["all", "egypt", "libya", "syria", "red_sea", "east_med", "israel"]
        categories = ["all", "actor", "military_unit", "chokepoint", "resource", "threat"]

        return KnowledgeGraph(
            nodes=filtered_nodes,
            edges=filtered_edges,
            theaters=theaters,
            categories=categories
        )


# Singleton instance
knowledge_graph_service = KnowledgeGraphService()
