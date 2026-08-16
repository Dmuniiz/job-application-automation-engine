-- SQLite
DELETE FROM job_records;

ALTER TABLE job_records 
ADD portal_url VARCHAR(255);