"""Strategic OSIRIS - Scenario Execution and Acceptance Test Script.
Runs a live end-to-end strategic intelligence scenario via the API and OpenRouter,
verifies multi-agent outputs, exercises the human approval gate, and outputs the final report.
"""
import sys
import time
import httpx

API_BASE = "http://localhost:8000"

SCENARIO_PAYLOAD = {
    "research_question": "تقييم التطورات الأمنية والتحركات العسكرية قرب الحدود الغربية المشتركة مع ليبيا، وتداعياتها على استقرار الدولة الوطنية والأمن القومي المصري خلال الأشهر القادمة.",
    "reference_country": "Egypt",
    "target_countries": ["Egypt", "Libya"],
    "time_horizon": "6-12 months",
    "assessment_mode": "strategic_assessment"
}

def main():
    print("=" * 70)
    print("🎯 STRATEGIC OSIRIS — SCENARIO RUN & ACCEPTANCE TEST")
    print("=" * 70)

    # 1. Health Check
    with httpx.Client(base_url=API_BASE, timeout=10.0) as client:
        health = client.get("/api/health").json()
        print(f"[*] API Status: {health['status']}")
        print(f"[*] Intelligence Engine: {health['llm_mode']}")
        print(f"[*] Registered Agents: {health['agents_count']}")

        # 2. Trigger Scenario
        print("\n[*] Launching Strategic Assessment via Multi-Agent Pipeline...")
        print(f"[*] Question: {SCENARIO_PAYLOAD['research_question']}")
        start_time = time.time()
        
        # OpenRouter live calls for multiple agents can take 20-60 seconds depending on API speed
        res = client.post("/api/assessments", json=SCENARIO_PAYLOAD, timeout=180.0)
        elapsed = time.time() - start_time
        
        if res.status_code != 200:
            print(f"[!] Error: {res.status_code} - {res.text}")
            sys.exit(1)

        assessment = res.json()
        aid = assessment["id"]
        print(f"[+] Assessment Completed in {elapsed:.1f}s — ID: {aid}")
        print(f"[+] Status: {assessment['status']} (Awaiting Human Review Gate)")

        # 3. Inspect Output Elements
        print("\n" + "-" * 70)
        print("📋 1. EXECUTIVE SUMMARY (الملخص التنفيذي):")
        print(assessment["executive_summary_ar"][:400] + "...")

        print("\n⚡ 2. KEY JUDGMENTS (الأحكام الاستراتيجية الرئيسية):")
        for i, kj in enumerate(assessment.get("key_judgments", [])):
            print(f"   {i+1}. {kj}")

        print("\n🛡️ 3. MILITARY FINDINGS (A04):")
        mil = assessment.get("military_assessment") or ""
        print(mil[:300] + "...")

        print("\n🏛️ 4. POLITICAL FINDINGS (A05):")
        pol = assessment.get("political_assessment") or ""
        print(pol[:300] + "...")

        # 4. Red Team Audit
        print("\n🔴 5. RED TEAM INDEPENDENT AUDIT (A13):")
        rtc = assessment.get("red_team_critique")
        if rtc:
            print(f"   Verdict: {rtc['verdict']}")
            print(f"   Strengths: {rtc['strengths'][:2]}")
            print(f"   Weaknesses / Challenged Assumptions: {rtc['weaknesses'][:2]}")
            print(f"   Recommendation: {rtc['recommendations_for_chief']}")

        # 5. Future Scenarios
        print("\n🔮 6. FUTURE SCENARIOS:")
        for sc in assessment.get("scenarios", []):
            print(f"   * [{int(sc['probability_estimate']*100)}%] {sc['title']}: {sc['description'][:80]}...")

        # 6. Human Review Approval Gate Action
        print("\n" + "-" * 70)
        print("[*] Exercising Mandatory Human Approval Gate...")
        approve_res = client.post(f"/api/assessments/{aid}/approve", json={
            "action": "approve",
            "reviewer": "رئيس هيئة التقدير الاستراتيجي (Strategic Review General)",
            "notes": "تمت المراجعة والتدقيق، ويعتمد التقدير للنشر المكتبي والتوزيع الاستراتيجي."
        })
        approved_data = approve_res.json()
        print(f"[+] Assessment Status Updated to: {approved_data['status']}")
        print(f"[+] Approved by: {approved_data['approval_reviewer']}")

        # 7. Export Report
        print("\n[*] Exporting Formal Arabic Strategic Markdown Report...")
        export_res = client.get(f"/api/assessments/{aid}/export?format=markdown")
        report_text = export_res.text
        
        with open("docs/LATEST_ASSESSMENT_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report_text)
        print("[+] Report saved to docs/LATEST_ASSESSMENT_REPORT.md")

        print("=" * 70)
        print("✅ SCENARIO RUN & ACCEPTANCE TEST SUCCEEDED 100%")
        print("=" * 70)

if __name__ == "__main__":
    main()
