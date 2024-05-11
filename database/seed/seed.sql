-- Insert sample data into slps
INSERT INTO slps (slp_id, name, email) VALUES
('d15b0570-1061-70e0-7c36-aa5239d9c5a6', 'John Doe', 'john.doe@example.com'),
('c12b4580-5061-7066-d9e8-0039f2cda8e0', 'Jane Smith', 'jane.smith@example.com'),
('014b95d0-1031-7011-d71f-a5eac87b6c7e', 'Alex Johnson', 'alex.johnson@example.com')
RETURNING slp_id;

-- Insert sample data into patients, ensuring each patient is associated with a specific slp
INSERT INTO patients (slp_id, name, birthdate) VALUES
('d15b0570-1061-70e0-7c36-aa5239d9c5a6', 'Hadoogan', '2010-01-01'),
('d15b0570-1061-70e0-7c36-aa5239d9c5a6', 'Shradoogan', '2012-02-02'),
('c12b4580-5061-7066-d9e8-0039f2cda8e0', 'Patient B1', '2011-03-03'),
('c12b4580-5061-7066-d9e8-0039f2cda8e0', 'Patient B2', '2013-04-04'),
('c12b4580-5061-7066-d9e8-0039f2cda8e0', 'Patient B3', '2015-05-05'),
('014b95d0-1031-7011-d71f-a5eac87b6c7e', 'Patient C1', '2014-06-06'),
('014b95d0-1031-7011-d71f-a5eac87b6c7e', 'Patient C2', '2016-07-07');

-- Insert sample data into lsas, ensuring lsas are associated with patients
-- Revised INSERT statements for LSAs with multiple entries per patient
INSERT INTO lsas (patient_id, name, timestamp, audiofile_url, transcription, mlu, tnw, wps, cps) VALUES
-- Patient A1 (2 LSAs)
(1, 'FunName1', '2023-01-01', NULL, 'Transcription 1', false, 1.1, 100, 2.1, 3.1),
(1, 'FunName2', '2023-02-01', NULL, 'Transcription 2', false, 1.2, 110, 2.2, 3.2),
-- Patient A2 (1 LSA)
(2, 'FunName3', '2023-01-02', NULL, 'Transcription 3', false, 1.3, 120, 2.3, 3.3),
-- Patient B1 (3 LSAs)
(3, 'FunName4', '2023-01-03', NULL, 'Transcription 4', false, 1.4, 130, 2.4, 3.4),
(3, 'FunName5', '2023-02-03', NULL, 'Transcription 5', false, 1.5, 140, 2.5, 3.5),
(3, 'FunName6', '2023-03-03', NULL, 'Transcription 6', false, 1.6, 150, 2.6, 3.6),
-- Patient B2 (2 LSAs)
(4, 'FunName7', '2023-01-04', NULL, 'Transcription 7', false, 1.7, 160, 2.7, 3.7),
(4, 'FunName8', '2023-02-04', NULL, 'Transcription 8', false, 1.8, 170, 2.8, 3.8),
-- Patient B3 (1 LSA)
(5, 'FunName9', '2023-01-05', NULL, 'Transcription 9', false, 1.9, 180, 2.9, 3.9),
-- Patient C1 (5 LSAs)
(6, 'FunName10', '2023-01-06', NULL, 'Transcription 10', false, 2.0, 190, 3.0, 4.0),
(6, 'FunName11', '2023-02-06', NULL, 'Transcription 11', false, 2.1, 200, 3.1, 4.1),
(6, 'FunName12', '2023-03-06', NULL, 'Transcription 12', false, 2.2, 210, 3.2, 4.2),
(6, 'FunName13', '2023-04-06', NULL, 'Transcription 13', false, 2.3, 220, 3.3, 4.3),
(6, 'FunName14', '2023-05-06', NULL, 'Transcription 14', false, 2.4, 230, 3.4, 4.4),
-- Patient C2 (2 LSAs)
(7, 'FunName15', '2023-01-07', NULL, 'Transcription 15', false, 2.5, 240, 3.5, 4.5)
