from typing import Dict, Any


QA_PROMPT = """You are an AI assistant specialized in tender/RFP analysis and proposal writing. Answer the user's question based ONLY on the provided context.

Context:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the provided context
- If the information is not in the context, say "I cannot find this information in the provided documents"
- Be specific and cite relevant sections when possible
- Keep answers concise but complete
- Use professional business language

Answer:"""

CONTEXT_QA_PROMPT = """You are an AI assistant specialized in tender/RFP analysis. Answer the question based on your knowledge.

Question: {question}

Answer:"""


ELIGIBILITY_PROMPT = """You are an expert tender eligibility assessor. Analyze the tender requirements against the company profile.

Tender Context:
{tender_context}

Company Profile:
{company_profile}

Assess each eligibility criterion and provide a GO/NO-GO recommendation.

Output as JSON:
{{
    "decision": "GO" or "NO-GO",
    "confidence": 0.0-1.0,
    "criteria_analysis": [
        {{
            "criterion": "description",
            "met": true/false,
            "evidence": "supporting text from tender or profile",
            "gap": "description if not met"
        }}
    ],
    "missing_requirements": ["list"],
    "recommendations": ["list"],
    "reasoning": "overall assessment"
}}"""

ELIGIBILITY_DETAILED_PROMPT = """Provide a detailed eligibility assessment for each criterion.

Tender Requirements:
{requirements}

Company Profile:
{profile}

For each requirement, provide:
1. Criterion text
2. Met/Partial/Not Met
3. Evidence from tender/company
4. Gap analysis
5. Mitigation strategy if applicable

Output as JSON array."""


COMPLIANCE_MATRIX_PROMPT = """You are a compliance analyst. Create a compliance matrix mapping tender requirements to proposal sections.

Tender Requirements:
{requirements_context}

Proposal Content:
{proposal_context}

For each requirement, assess compliance status: COMPLIANT, PARTIAL, NON-COMPLIANT, NOT ADDRESSED.

Output as JSON array:
[
    {{
        "requirement_id": "REQ-001",
        "requirement_text": "extracted requirement",
        "category": "Mandatory/Desirable",
        "proposal_section": "section name or number",
        "status": "COMPLIANT/PARTIAL/NON-COMPLIANT/NOT ADDRESSED",
        "evidence": "supporting text from proposal",
        "gap": "what is missing if not compliant",
        "notes": "additional notes"
    }}
]"""

REQUIREMENT_EXTRACTION_PROMPT = """Extract ALL requirements from the tender document.

Tender Text:
{tender_context}

Identify:
1. Mandatory requirements (shall, must, required, mandatory)
2. Desirable requirements (should, preferred, desirable)
3. Evaluation criteria with weights
4. Submission requirements
5. Technical specifications
6. Commercial terms
7. Certifications/qualifications

Output as JSON array with fields:
- id: REQ-001 format
- text: requirement text
- category: Mandatory/Desirable/Evaluation/Submission/Technical/Commercial/Qualification
- section: document section reference if available
- keywords: key terms for matching"""


PROPOSAL_DRAFT_PROMPT = """You are an expert proposal writer. Generate a structured proposal draft.

Tender Requirements:
{requirements}

Reusable Content:
{reusable_content}

Company Capabilities:
{company_capabilities}

Generate a proposal with these sections:
1. Executive Summary
2. Technical Approach/Methodology
3. Team & Capabilities
4. Past Experience/Case Studies
5. Commercial Proposal (placeholders)
6. Compliance Statement

Use the reusable content where applicable, adapting to this specific tender.
Include [PLACEHOLDERS] for information that needs customization.
Ensure compliance with all mandatory requirements.

Proposal Draft:"""

PROPOSAL_SECTION_PROMPT = """Write a specific proposal section.

Section: {section_title}
Section Type: {section_type}
Requirements to Address:
{requirements}

Reusable Content:
{reusable_content}

Company Capabilities:
{company_capabilities}

Word Limit: {word_limit}

Write a compelling, compliant section that addresses all requirements.
Use specific examples from reusable content where relevant.
Include [PLACEHOLDERS] for customization."""


EXECUTIVE_SUMMARY_PROMPT = """Create an executive summary for senior leadership.

Tender: {tender_title}
Reference: {tender_ref}
Issuing Authority: {issuing_authority}
Deadline: {deadline}

Tender Context:
{context}

Provide a structured summary covering:
1. Tender Overview (what, who, ref #)
2. Key Dates (submission, clarification, start)
3. Scope of Work
4. Key Eligibility Criteria
5. Commercial (value, payment, duration)
6. Evaluation Method
7. Risk/Opportunity Assessment
8. GO/NO-GO Recommendation with rationale

Max 500 words. Professional executive tone."""

DOCUMENT_SUMMARY_PROMPT = """Summarize the document focusing on: {focus}

Document:
{document_text}

Max {max_words} words. Professional tone. Include key facts, figures, and requirements."""

KEY_POINTS_PROMPT = """Extract the {max_points} most important key points from this text.

Text:
{document_text}

Return as JSON array of strings."""


COMPLIANCE_CHECK_PROMPT = """Check if the proposal section addresses the requirement.

Requirement:
{requirement}

Proposal Section:
{proposal_section}

Output JSON:
{{
    "status": "COMPLIANT/PARTIAL/NON-COMPLIANT/NOT ADDRESSED",
    "evidence": "supporting text from proposal",
    "gap": "what is missing",
    "recommendation": "how to improve"
}}"""

IMPROVEMENT_PROMPT = """Improve this proposal section based on feedback/compliance gaps.

Section Title: {section_title}
Current Content:
{current_content}

Requirements to Address:
{requirements}

Feedback/Improvements Needed:
{feedback}

Company Capabilities:
{company_capabilities}

Rewrite the section to be more compliant, compelling, and complete."""


FINANCIAL_MODEL_PROMPT = """Create a financial model for the proposal.

Tender Commercial Terms:
{commercial_terms}

Company Cost Structure:
{cost_structure}

Pricing Strategy: {pricing_strategy}

Generate:
1. Cost breakdown (labor, materials, subcontractors, overhead, profit)
2. Pricing schedule
3. Payment milestones
4. Cash flow projection
5. Risk contingencies

Output as JSON."""


RISK_ASSESSMENT_PROMPT = """Identify and assess risks for this tender/proposal.

Tender: {tender_title}
Proposal: {proposal_title}

Tender Risks:
{tender_risks}

Proposal Risks:
{proposal_risks}

Output JSON array of risks:
[
    {{
        "id": "RISK-001",
        "category": "Technical/Commercial/Schedule/Legal/Resource",
        "description": "risk description",
        "likelihood": "High/Medium/Low",
        "impact": "High/Medium/Low",
        "mitigation": "mitigation strategy",
        "owner": "role responsible",
        "status": "Open/Mitigated/Accepted"
    }}
]"""


EXPORT_PROPOSAL_PROMPT = """Format the proposal for export as {format}.

Proposal:
{proposal_content}

Apply professional formatting suitable for {format} output.
Include cover page, table of contents, section numbering, and page breaks."""


SECTION_CLASSIFICATION_PROMPT = """Classify this tender section.

Section Title: {title}
Section Content: {content}

Categories: Technical, Commercial, Legal, Administrative, Evaluation, Submission, Qualification, Background, Scope, Requirements

Output: Category name only."""

KEYWORD_EXTRACTION_PROMPT = """Extract key terms and phrases for search/matching.

Text: {text}

Output JSON array of keywords/phrases (max 20)."""


ALL_PROMPTS: Dict[str, str] = {
    "qa": QA_PROMPT,
    "context_qa": CONTEXT_QA_PROMPT,
    "eligibility": ELIGIBILITY_PROMPT,
    "eligibility_detailed": ELIGIBILITY_DETAILED_PROMPT,
    "compliance_matrix": COMPLIANCE_MATRIX_PROMPT,
    "requirement_extraction": REQUIREMENT_EXTRACTION_PROMPT,
    "proposal_draft": PROPOSAL_DRAFT_PROMPT,
    "proposal_section": PROPOSAL_SECTION_PROMPT,
    "executive_summary": EXECUTIVE_SUMMARY_PROMPT,
    "document_summary": DOCUMENT_SUMMARY_PROMPT,
    "key_points": KEY_POINTS_PROMPT,
    "compliance_check": COMPLIANCE_CHECK_PROMPT,
    "improvement": IMPROVEMENT_PROMPT,
    "financial_model": FINANCIAL_MODEL_PROMPT,
    "risk_assessment": RISK_ASSESSMENT_PROMPT,
    "export_proposal": EXPORT_PROPOSAL_PROMPT,
    "section_classification": SECTION_CLASSIFICATION_PROMPT,
    "keyword_extraction": KEYWORD_EXTRACTION_PROMPT,
}


def get_prompt(name: str, **kwargs) -> str:
    prompt = ALL_PROMPTS.get(name)
    if not prompt:
        raise ValueError(f"Prompt '{name}' not found")
    return prompt.format(**kwargs)