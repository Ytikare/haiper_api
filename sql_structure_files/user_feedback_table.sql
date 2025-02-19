-- Create the table with auto-incrementing PK and FK relationship
CREATE TABLE IF NOT EXISTS workflow_submissions (
    id SERIAL PRIMARY KEY,
    is_positive BOOLEAN NOT NULL,
    workflow_id VARCHAR(50) NOT NULL,
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_workflow
        FOREIGN KEY(workflow_id) 
        REFERENCES workflow_structures(id)
        ON DELETE CASCADE
);

-- Create an index on workflow_id for better join performance
CREATE INDEX idx_workflow_submissions_workflow_id 
ON workflow_submissions(workflow_id);