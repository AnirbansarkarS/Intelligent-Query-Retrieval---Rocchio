import json

def transform_answers(input_list: list) -> dict:
    answers_list = []

    for item in input_list:
        answer_field = item.get("answer")

        if isinstance(answer_field, str):
            try:
                parsed = json.loads(answer_field)
                answers_list.append(parsed.get("answer", "").strip())
            except json.JSONDecodeError:
                answers_list.append(answer_field.strip())

        elif isinstance(answer_field, dict):
            answers_list.append(answer_field.get("answer", "").strip())

    output = {"answers": answers_list}
    print(f"✅ Extracted {len(answers_list)} answers.")
    return output


# Example usage
sample_input = [
    {"question": "Q1", "answer": "{\"answer\": \"Yes, it is covered.\"}"},
    {"question": "Q2", "answer": {"answer": "No, it’s not covered."}},
    {"question": "Q3", "answer": "Simple answer without JSON"}
]

result = transform_answers([
    {
        "question": "What is the waiting period for pre-existing diseases (PED) to be covered?",
        "answer": "{\n    \"answer\": \"Expenses related to the treatment of a Pre-Existing Disease (PED) and its direct complications are excluded until the expiry of thirty-six (36) months of continuous coverage after the date of inception of the first policy.\",\n    \"explanation\": \"The policy document explicitly states under section 4.1. Pre-Existing Diseases (Excl 01) that a waiting period of thirty-six (36) months of continuous coverage applies for Pre-Existing Diseases and their direct complications.\",\n    \"sources\": [\"4.1. Pre-Existing Diseases (Excl 01) a)\"]\n}"
    },
    {
        "question": "What is the waiting period for cataract surgery?",
        "answer": "{\n    \"answer\": \"The waiting period for cataract surgery is two years.\",\n    \"explanation\": \"According to the 'List of specific diseases/procedures' under Section 4.2.f.iii, cataract surgery falls under the two-year waiting period category.\",\n    \"sources\": [\"Page 9 of 25\", \"Section 4.2.f.iii\"]\n}"
    },
    {
        "question": "How does the policy define a 'Hospital'?",
        "answer": "{\n    \"answer\": \"A 'Hospital' is defined as any institution established for in-patient care and day care treatment of disease/injuries that is registered with local authorities under the Clinical Establishments (Registration and Regulation) Act, 2010, or complies with specific minimum criteria including: having qualified nursing staff round the clock, at least ten inpatient beds in towns with population less than ten lacs (and fifteen beds in other places), qualified medical practitioner(s) in charge round the clock, a fully equipped operation theatre, and maintaining daily patient records accessible to the Company.\",\n    \"explanation\": \"The policy explicitly defines 'Hospital' under section 2.22, detailing both the registration requirement and an alternative set of minimum criteria for an institution to qualify as a hospital.\",\n    \"sources\": [\"2.22 Hospital\"]\n}"
    },
    {
        "question": "Is there a benefit for preventive health check-ups?",
        "answer": "{\n    \"answer\": \"Yes, expenses for health check-ups are reimbursed every two continuous policy years, provided the policy has been continuously renewed without a break. The reimbursement is subject to the limit specified in the Table of Benefits, which ranges from INR 5,000 to INR 10,000.\",\n    \"explanation\": \"The document explicitly states under section '3.2.2 Health Check Up' that 'Expenses of health check up shall be reimbursed (irrespective of past claims) at the end of a block of two continuous policy years, provided the Policy has been continuously renewed with the Company without a break. Expenses payable are subject to the limit stated in the Table of Benefits.' The table further clarifies the limits as 'Every 2 yrs., up to INR 5,000 / 7,500 / 10,000'.\",\n    \"sources\": [\n        \"3.2.2 Health Check Up\",\n        \"Good Health Incentives\"\n    ]\n}"
    },
    {
        "question": "What is the No Claim Discount (NCD) offered in this policy?",
        "answer": "{\n    \"answer\": \"A No Claim Discount (NCD) of a flat 5% is offered on the base premium when policies are renewed, provided no claims were reported in the expiring policy year. For policies exceeding one year, the aggregated NCD for each claim-free year is applied, not exceeding 5% of the total base premium for the policy term.\",\n    \"explanation\": \"The context explicitly defines the No Claim Discount (NCD) under section '3.2.1 No Claim Discount (NCD)' and also summarizes it in the 'Good Health Incentives' table. Both state that a flat 5% discount is applied to the base premium if no claims are reported. The text further explains the application for policies with terms of one year versus those exceeding one year, with the aggregate NCD capped at 5% of the total base premium for the term.\",\n    \"sources\": [\"3.2.1 No Claim Discount (NCD)\", \"Good Health Incentives\"]\n}"
    },
    {
        "question": "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "answer": "{\n    \"answer\": \"null\",\n    \"explanation\": \"The provided context details various aspects of the National Parivar Mediclaim Plus Policy, including claims procedures, cessation of cover, enhancement of benefits, and cancellation policies. However, it does not contain any information regarding a grace period for premium payment.\",\n    \"sources\": []\n}"
    },
    {
        "question": "What is the extent of coverage for AYUSH treatments?",
        "answer": "{\n    \"answer\": \"Medical expenses incurred for inpatient care treatment under Ayurveda, Yoga and Naturopathy, Unani, Siddha, and Homeopathy systems are indemnified up to the limit of the Sum Insured as specified in the Policy Schedule for each Policy Period, provided the treatment is received in an AYUSH Hospital.\",\n    \"explanation\": \"According to section 3.1.6 'AYUSH Treatment', the company indemnifies 'Medical Expenses incurred for Inpatient Care treatment under Ayurveda, Yoga and Naturopathy, Unani, Siddha and Homeopathy systems of medicines during each Policy Period up to the limit of Sum Insured as specified in the Policy Schedule in any AYUSH Hospital.'\",\n    \"sources\": [\"3.1.6 AYUSH Treatment\"]\n}"
    },
    {
        "question": "Are the medical expenses for an organ donor covered under this policy?",
        "answer": "{\n    \"answer\": \"Yes, medical expenses incurred for an organ donor's hospitalization during the policy period for the harvesting of an organ donated to an Insured Person are covered. However, this is subject to specific conditions and exclusions.\",\n    \"explanation\": \"Section 3.1.7, 'Organ Donor\u2019s Medical Expenses,' explicitly states that the Company shall indemnify the Medical Expenses incurred in respect of an organ donor\u2019s Hospitalisation during the Policy Period for harvesting of the organ donated to an Insured Person. This coverage is conditional upon adherence to the Transplantation of Human Organs Act 1994, the organ being for an Insured Person medically advised for a transplant, the expenses being for the donor as an in-patient, and the claim for the Insured Person's transplant being admitted under the In-patient Treatment Section. It also lists several exclusions, such as pre/post-hospitalization expenses, costs of organ acquisition, experimental treatments, post-harvesting complications, and organ transportation/preservation.\",\n    \"sources\": [\"3.1.7 Organ Donor\u2019s Medical Expenses\"]\n}"
    },
    {
        "question": "Are there any sub-limits on room rent and ICU charges for Plan A?",
        "answer": "{\n    \"answer\": \"Yes, for Plan A, there are sub-limits on room rent and ICU charges per day. Room charges are limited to 1% of the Sum Insured (SI) or the actual cost, whichever is lower. ICU charges are limited to 2% of the Sum Insured (SI) or the actual cost, whichever is lower. These limits do not apply if treatment is for a listed procedure in a Preferred Provider Network (PPN) as a package.\",\n    \"explanation\": \"The document explicitly states under '3.1.1.1 Limit for Room Charges and Intensive Care Unit Charges' that these charges for Plan A are 'up to the limit as shown in the Table of Benefits'. The 'Table of Benefits' further specifies for PLAN A: 'Room - Up to 1% of SI or actual, whichever is lower' and 'ICU \u2013 Up to 2% of SI or actual, whichever is lower'. It also mentions an exception where these limits do not apply if the treatment is undergone for a listed procedure in a Preferred Provider Network (PPN) as a package.\",\n    \"sources\": [\n        \"3.1.1.1 Limit for Room Charges and Intensive Care Unit Charges\",\n        \"Table of Benefits\"\n    ]\n}"
    },
    {
        "question": "Does this policy cover maternity expenses, and what are the conditions?",
        "answer": "{\n    \"answer\": \"Yes, this policy covers maternity expenses, including medical treatment for childbirth (normal, complicated, C-section), lawful medical termination of pregnancy, and certain new born baby expenses. Coverage is subject to a 24-month waiting period and specific financial limits.\",\n    \"explanation\": \"The policy explicitly states under Section 3.1.14 'Maternity' that it shall indemnify Maternity Expenses. The conditions for coverage include the female insured person being continuously covered for at least 24 months, with benefits subject to limits specified in the Table of Benefits (e.g., INR 30,000 for normal delivery, INR 50,000 for caesarean). The New Born Baby is automatically covered from birth for up to 3 months. Exclusions apply, such as for insured persons below 18 or above 45 years of age, deliveries/terminations within the 24-month waiting period (unless induced by accident), more than two deliveries/terminations in total, more than one in a single policy period, and generally maternity expenses for a surrogate mother (unless under Infertility Section 3.1.15 with a legal affidavit). Ectopic pregnancy is generally excluded but covered if established by medical reports under 'In-patient treatment'. Pre and post hospitalization expenses are excluded, except for pre and post-natal treatment.\",\n    \"sources\": [\n        \"a)\",\n        \"b)\",\n        \"Note: Ectopic pregnancy is covered under \u2018In-patient treatment\u2019, provided such pregnancy is established by medical reports.\",\n        \"Exclusions\",\n        \"1. Covered female Insured Person below eighteen (18) years and above forty-five (45) years of age.\",\n        \"2. Delivery or termination within a Waiting Period of twenty-four (24) months. However, the Waiting Period may be waived only in the case of delivery, miscarriage or abortion induced by accident.\",\n        \"3. Delivery or lawful medical termination of pregnancy limited to two deliveries or terminations or either has been paid under the Policy and its Renewals.\",\n        \"4. More than one delivery or lawful medical termination of pregnancy during a single Policy Period.\",\n        \"5. Maternity Expenses of Surrogate Mother, unless claim is admitted under Section 3.1.15 (Infertility)\",\n        \"6. Ectopic pregnancy\",\n        \"7. Pre and post hospitalisation expenses, other than pre and post natal treatment.\",\n        \"3.1.14 Maternity\",\n        \"The female Insured Person should have been continuously covered for at least 24 months before availing this benefit.\",\n        \"The New Born Baby shall be automatically covered from birth under the Sum Insured available to the mother during the corresponding Policy Period, for up to 3 months of age.\",\n        \"On attaining 3 months of age, the New Born Baby shall be covered only if specifically included in the Policy mid-term and requisite premium paid to the Company.\",\n        \"Maternity (including Baby from Birth Cover) (per insured person, in a policy year, waiting period of 2 years applies) Up to INR 30,000 for normal delivery and INR 50,000 for caesarean section\"\n    ]\n}"
    }
])

# Print or save the result
print(json.dumps(result, indent=2, ensure_ascii=False))
