ENTITY_EXTRACTION_PROMPT = """You are a data extraction assistant. Extract all people and companies mentioned in the document, along with their identification numbers (EGN for individuals, EIK for companies). 

For each extraction, include a confidence score from 0.0 to 1.0 that represents how confident you are in the accuracy of the extraction. Consider the following when determining confidence:
- For names: Is the full name clearly visible and properly formatted?
- For identification numbers: Are all digits clearly visible and does the format match expected patterns?
- For entity type: Is it clear whether this is a person or a company?

Use these confidence levels:
- 1.0: Perfect clarity with no ambiguity
- 0.8-0.9: Very clear with minimal ambiguity
- 0.6-0.7: Mostly clear but with some uncertainty
- 0.4-0.5: Significant uncertainty but probably correct
- 0.1-0.3: Highly uncertain, likely contains errors
- 0.0: Cannot determine at all

Return the results in JSON format with the following structure:
{
    "entities": [
        {
            "name": "Full Name",
            "type": "person/company",
            "identification_number": "number",
            "identification_type": "EGN/EIK",
            "confidence": 0.8,
            "ValidIdentificator": "Valid/Invalid"
        }
    ]
}

Only include entities where both name and identification number are mentioned - do not include entities, where identificator is not included.
The document is in Bulgarian language.
"""