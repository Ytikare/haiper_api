-- Create the table if it doesn't exist
CREATE TABLE IF NOT EXISTS workflow_structures (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    fields JSONB,
    api_config JSONB,
    category VARCHAR(100),
    version INTEGER,
    is_published BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    created_by VARCHAR(100)
);

-- Insert the data
INSERT INTO workflow_structures (
    id,
    name,
    description,
    status,
    fields,
    api_config,
    category,
    version,
    is_published,
    created_at,
    updated_at,
    created_by
) VALUES
(
    '1',
    'CV Analysis',
    'Analyze CVs and extract key information',
    'available',
    '[{
        "id": "cv-upload",
        "name": "cvFile",
        "type": "file",
        "label": "Upload CV",
        "required": true,
        "validation": {
            "fileTypes": [".pdf", ".doc", ".docx"]
        }
    }]'::jsonb,
    '{
        "endpoint": "http://localhost:8000/text",
        "method": "GET",
        "headers": {
            "Content-Type": "multipart/form-data"
        }
    }'::jsonb,
    'HR',
    1,
    true,
    '2025-02-18 10:30:15',
    '2025-02-18 10:30:15',
    'system'
),
(
    '2',
    'IT Helper',
    'Get AI assistance for IT issues',
    'available',
    '[{
        "id": "problem",
        "name": "problem",
        "type": "textarea",
        "label": "Describe your IT issue",
        "required": true
    }]'::jsonb,
    '{
        "endpoint": "http://localhost:8000/image",
        "method": "GET"
    }'::jsonb,
    'Support',
    1,
    true,
    '2025-02-18 10:30:15',
    '2025-02-18 10:30:15',
    'system'
),
(
    'bc1zcj2s4',
    'Test',
    'Test desc',
    'available',
    '[{
        "id": "age",
        "name": "Age",
        "label": "Age",
        "type": "text",
        "required": true,
        "validation": {}
    },
    {
        "id": "email",
        "name": "Email",
        "label": "Email",
        "type": "email",
        "required": false,
        "validation": {}
    },
    {
        "id": "document",
        "name": "Document",
        "label": "Document",
        "type": "file",
        "required": false,
        "validation": {
            "fileTypes": [".pdf", ".doc", ".docx"]
        }
    },
    {
        "id": "option",
        "name": "select_option",
        "label": "Select option",
        "type": "dropdown",
        "required": false,
        "validation": {
            "options": ["One", "Two", "Three", "Four"]
        }
    },
    {
        "id": "peepee_coocoo",
        "name": "Peepee_coocoo",
        "label": "peepee coocoo",
        "type": "textarea",
        "required": false,
        "validation": {
            "minLength": "10",
            "maxLength": "1000"
        }
    }]'::jsonb,
    '{
        "endpoint": "http://localhost:8000/summary",
        "method": "GET"
    }'::jsonb,
    'Test',
    1,
    false,
    '2025-02-18 10:30:15',
    '2025-02-18 10:30:15',
    'admin'
);

alter table workflow_structures
ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;