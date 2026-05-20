INVOICE_IMAGE_PROMPT = """A highly realistic photograph of an Indian commercial GST tax invoice document written primarily in {language}.

The invoice must look like a real scanned or photographed physical document placed on a flat surface.

INVOICE CONTENT:
- Company letterhead with business name in {language} script, logo placeholder, full address, GSTIN, PAN
- Invoice number, date, due date, place of supply
- Customer billing and shipping address with GSTIN
- Itemized table with 6 to 12 line items: description in {language}, HSN/SAC code, quantity, unit price, tax rate, amount
- Tax summary: CGST + SGST or IGST, subtotal, round-off, grand total in INR
- Amount in words in {language}
- Bank details: bank name, account number, IFSC
- Authorized signature box and company stamp/seal
- Terms and conditions footer in {language}
- E&OE footer text

DOCUMENT TYPE: {doc_type}

VISUAL STYLE:
- Printed on white A4 paper
- Dense table layout with borders, realistic column alignment
- Mix of bold headers and regular body text
- Rupee symbol (Rs or INR) used throughout
- Realistic Indian city names, PIN codes, phone numbers

SCAN STYLE: {scan_style}

The document should fill most of the frame with realistic paper texture and lighting."""


DOCUMENT_TYPES = [
    "Retail / FMCG invoice",
    "Restaurant / Catering bill",
    "Electronics / IT hardware invoice",
    "Pharma / Medical supplies invoice",
    "Logistics / Transport invoice",
    "Grocery / Kirana store bill",
    "Hotel / Hospitality invoice",
    "Manufacturing / Industrial invoice",
    "SaaS / IT Services invoice",
    "Construction / Building materials invoice",
    "Textile / Garments invoice",
    "Automotive parts invoice",
    "Agricultural produce invoice",
    "Educational institute fee receipt",
    "Healthcare / Hospital bill",
]

SCAN_STYLES = [
    "Clean flatbed office scanner — high contrast, sharp edges, white background",
    "Mobile phone camera — slight perspective warp, soft shadow on one side, minor rotation up to 3 degrees",
    "Photocopier output — slightly gray background, faint bleed-through lines, reduced contrast",
    "Old thermal printer — faded gray text, uneven ink density, slightly yellowed paper",
    "Dot matrix printer — visible horizontal banding, monospace text, slight perforation marks on edges",
    "Hand-carried document — visible fold lines, minor coffee stain in corner, worn edges",
]
